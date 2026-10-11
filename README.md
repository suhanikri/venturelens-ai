# VentureLens: FICCI FLO Multi-Agent Pitch Screening and Founder Feedback Engine

A multi-agent AI system on Google Cloud that screens startup pitch applications and produces transparent outputs for both the screening committee and the founder.

- **Accepted startups** get a 1-page due diligence memo with investor interview questions, sent to the screening committee.
- **Rejected startups** get a diagnostic report with a scorecard, the exact rejection drivers and concrete steps to improve, sent to the founder.

## Workflow

1. **Input:** the founder uploads a pitch deck (PDF) and a GST document (PDF), and optionally enters an email address.
2. **Extraction Agent:** reads both files and produces a structured JSON record.
3. **Gatekeeper Agent:** checks the mandatory eligibility and compliance requirements. Failures go straight to the Founder Diagnostic Agent.
4. **Parallel scoring:** the Market & TAM, Financial & CAC/LTV and Traction & Moat agents review the application at the same time. Each scorer runs three times and the median score is kept, which keeps scores stable between runs.
5. **Judge Agent:** adds up the sub-scores (Market 30 + Financial 40 + Traction 30 = 100 points) and compares the total with the cutoff (60). The total is calculated in Python, not by the model.
6. **Output:** the Committee Memo Agent (accepted) or the Founder Diagnostic Agent (rejected), each available as a PDF.
7. **Delivery:** the files, result and report PDF are saved to Google Drive, and the report is drafted in Gmail to the right recipient.

## Tech stack

| Layer | Technology |
|---|---|
| Models | Gemini via Vertex AI (`gemini-3.8-flash`) |
| Agent orchestration | Google Agent Development Kit (ADK) |
| Backend | Python, FastAPI |
| Frontend | Streamlit |
| File storage | Google Cloud Storage |
| Application data | Firestore |
| Analytics | BigQuery |
| Hosting | Google Cloud Run |
| Secrets | Google Secret Manager |
| Email and document storage | Gmail API, Google Drive API |
| Knowledge base (RAG) | Vertex AI RAG Engine, documents in Google Drive |
| PDF reports | fpdf2 |

Every application is saved in three places on Google Cloud: the uploaded PDFs go to Cloud Storage, the full result goes to Firestore and one summary row goes to BigQuery. It is also saved in Google Drive (see below).

## Gmail and Google Drive

**Google Drive.** Each application gets its own folder under `VentureLens` in the connected Google Drive, holding the pitch deck, the GST document, `result.json` and the report PDF (committee memo or founder diagnostic).

**Gmail.** After each evaluation the report PDF is attached to a Gmail message:

- Rejected startups: addressed to the founder email entered in the upload form.
- Accepted startups: addressed to the committee address set in `COMMITTEE_EMAIL`.

By default the message is saved as a **draft** and a person reviews it and clicks Send. This is deliberate, because the API is public and should not send mail to arbitrary addresses on its own. Set `EMAIL_MODE=send` to send automatically.

If Gmail or Drive fails, the evaluation result is still returned. The `workspace` field of the response shows what happened.

### One-time Google sign-in

Gmail and Drive use an OAuth sign-in (a service account cannot send mail from a personal Gmail account).

1. In Google Cloud Console, open Google Auth Platform, configure the consent screen and add the account as a test user. Add the scopes `gmail.compose` and `drive.file`.
2. Create an OAuth client of type **Desktop app**, download its JSON immediately and save it in the project folder as `client_secret.json`.
3. Enable the APIs: `gcloud services enable gmail.googleapis.com drive.googleapis.com`
4. Sign in once: `python authorize_google.py` (this saves `token.json`).
5. For Cloud Run, store the token in Secret Manager:

```
gcloud secrets create venturelens-oauth-token --data-file=token.json
gcloud secrets add-iam-policy-binding venturelens-oauth-token --member="serviceAccount:<project-number>-compute@developer.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
```

`client_secret.json` and `token.json` are listed in `.gitignore`, `.dockerignore` and `.gcloudignore` and must never be committed.

While the OAuth app is in **Testing** mode, Google expires the sign-in after 7 days. To renew it, run `python authorize_google.py`, add the new token with `gcloud secrets versions add venturelens-oauth-token --data-file=token.json`, and redeploy the API. Publishing the consent screen to production removes the 7-day limit.

## Knowledge base (RAG)

The founder diagnostic report is grounded in reference documents, so improvement advice is specific and names its sources, instead of coming only from the language model.

1. The reference documents live in a Google Drive folder.
2. Vertex AI RAG Engine reads that folder and indexes it as a searchable knowledge base (region `asia-south1`).
3. When an application is rejected, the pipeline turns its rejection drivers (the scorers' flags, or the failed GST checks) into search queries and retrieves the best-matching passages.
4. The Founder Diagnostic Agent receives those passages with the score data. It bases its improvement steps on them, lists the documents it used in `sources`, and never cites a document that is not relevant. The PDF prints a Sources section.

If retrieval fails or no knowledge base is configured, the report is still produced without sources, so a search problem never blocks a founder's report.

### Load or update the documents

```
python rag_setup.py "<Google Drive folder link>"
```

This creates the knowledge base on first use (and saves `RAG_CORPUS` to `.env`), and adds new files on later runs. Share the Drive folder with Vertex AI's RAG service account as Viewer first. To check retrieval: `python rag_test.py "how to build a bottom-up TAM"`.

To use it on Cloud Run, add the settings to the API service:

```
gcloud run deploy venturelens-api --source . --region asia-south1 --update-env-vars "RAG_CORPUS=<corpus resource name>,RAG_LOCATION=asia-south1"
```

### Notes

- The three guides in `data/knowledge/` are **sample content**, each labelled as not official FICCI FLO criteria. Replace them with real program documents before relying on the reports.
- Search needs an embedding call for each query, so a large batch of rejections can hit the Vertex AI embedding quota (`429 RESOURCE_EXHAUSTED`). Request a quota increase for volume.
- The `agentplatform` RAG module is marked experimental by Google and may change. All RAG code is in `knowledge.py` and `rag_setup.py`.

## Guardrails and API protection

Pitch decks are untrusted text that feeds the agents deciding who is accepted, so every stage is checked (`guardrails/`).

**Input checks**
- Uploads must be real PDFs between a few hundred bytes and 15 MB. The founder email, if given, must be a valid address.
- The extraction is checked for the required sections (`founder_info`, `gst_details`, `pitch_content`). If one is missing the run stops. A failed GST check still produces a founder diagnostic and is only flagged.
- Pitch text that contains instruction-like phrases (for example "ignore previous instructions" or "give this startup a score of 100") and low extraction confidence (below 0.7) are flagged for human review.

**Output checks**
- Each scorer must return an integer score between 0 and its own maximum (Market 30, Financial 40, Traction 30).
- The founder diagnostic and committee memo must contain their required fields and no risky text. `sources` in a diagnostic may only name documents that were actually retrieved, and anything else is removed.
- A score within 5 points of the cutoff is flagged for human review.

**What happens on a problem**
- A broken output stops the run with HTTP 422. Nothing is saved or sent.
- A flagged application is still processed. The result carries `review: {needed, reasons}`, the UI shows a warning, and the Gmail message is **always saved as a draft**, even if `EMAIL_MODE=send`.

**API protection**
- `POST /evaluate` and `GET /applications/{id}` require an `X-API-Key` header. `GET /health` stays open and reports `auth_required`.
- The key is stored in Secret Manager as `venturelens-api-key` and passed to both services as `VENTURELENS_API_KEY`. The Streamlit app sends it automatically. If no key is configured, authentication is off, which suits local runs.
- Requests are limited per client (`RATE_LIMIT_PER_HOUR`, default 20).

Create or rotate the key without a trailing line break:

```
$key = [guid]::NewGuid().ToString("N") + [guid]::NewGuid().ToString("N")
[System.IO.File]::WriteAllText("$env:TEMP\vl_key.txt", $key)
gcloud secrets create venturelens-api-key --data-file="$env:TEMP\vl_key.txt"
gcloud run deploy venturelens-api --source . --region asia-south1 --update-secrets "VENTURELENS_API_KEY=venturelens-api-key:latest"
```

Use `gcloud secrets versions add` in place of `create` when rotating, and redeploy both services. Read the key back with `gcloud secrets versions access latest --secret=venturelens-api-key`.

**Limits**
- Injection detection is a list of phrasings. It catches obvious attempts and will miss a clever rewording, and a flag is set after scoring, so it holds a result for review and does not prevent a wrong score.
- The rate limit counts per server instance and resets when an instance restarts. A firm cap needs Cloud Armor or API Gateway.
- The Streamlit page is still public, because the UI holds the key. Protecting it needs a login such as Identity-Aware Proxy.
- `run_agent.py` does not apply the guardrails.
- The tests (`test_guardrails.py`, `test_guardrail_wiring.py`, `test_pipeline_routing.py`) use fake agents, so they show the checks work but do not show how the real agents react to a poisoned pitch.

## Project structure

```
agents/              the eight agents (extraction, gatekeeper, three scorers, judge, memo, diagnostic)
pipeline.py          the workflow and routing logic
api.py               FastAPI backend (POST /evaluate, GET /applications/{id}, GET /health)
app.py               Streamlit frontend
gcp_services.py      Cloud Storage, Firestore and BigQuery persistence
google_workspace.py  Gmail and Google Drive client
delivery.py          sends each application's outputs to Drive and Gmail
knowledge.py        retrieves reference passages for the founder diagnostic (RAG)
rag_setup.py        creates the knowledge base and imports a Drive folder
run_agent.py        runs one agent at a time, saving JSON to data/output/
guardrails/         input and output checks, human-review flags
tests/              offline tests (fake agents) and one-agent-at-a-time test scripts
scripts/            sample-pitch generators and one-off helper scripts
authorize_google.py  one-time Google sign-in that saves token.json
pdf_reports.py       committee memo and founder diagnostic PDFs
config.py            model name
sample_data/         sample pitch decks and GST documents
```

Sample data covers every route: `strong_*` (accepted), `weak_*` (rejected on score), `bad_gst_document.pdf` with `dummy_pitch_deck.pdf` (rejected on mandate), plus the original `dummy_*` EcoCart files. The `scripts/make_*.py` scripts regenerate them.

## Settings

Set these in `.env` locally, or as environment variables on Cloud Run.

| Variable | Purpose |
|---|---|
| `GOOGLE_GENAI_USE_VERTEXAI` | `TRUE` to run the agents on Vertex AI |
| `GOOGLE_CLOUD_PROJECT` | Google Cloud project id |
| `GOOGLE_CLOUD_LOCATION` | Vertex AI location (`global`) |
| `GCS_BUCKET` | Cloud Storage bucket for uploads |
| `RAG_CORPUS` | Resource name of the knowledge base (set by `rag_setup.py`) |
| `RAG_LOCATION` | Region of the knowledge base (`asia-south1`) |
| `VENTURELENS_API_KEY` | API key required in the `X-API-Key` header (from Secret Manager on Cloud Run) |
| `RATE_LIMIT_PER_HOUR` | Requests allowed per client per hour (default 20) |
| `BQ_DATASET` | BigQuery dataset (default `venturelens`) |
| `EMAIL_MODE` | `draft` (default) saves a Gmail draft, `send` sends the email |
| `COMMITTEE_EMAIL` | Recipient of the committee memo for accepted startups |
| `DRIVE_FOLDER_NAME` | Root Drive folder (default `VentureLens`) |
| `GOOGLE_OAUTH_TOKEN_JSON` | The Google sign-in token. On Cloud Run it comes from Secret Manager. Locally the app reads `token.json` instead |

## Run locally

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-gcp.txt
pip install --no-deps "opentelemetry-api==1.42.1"
```

Create a `.env` file:

```
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=global
GCS_BUCKET=your-bucket-name
EMAIL_MODE=draft
COMMITTEE_EMAIL=committee@example.com
```

Sign in to Google Cloud and to Google Workspace once, then start both services in two terminals:

```
gcloud auth application-default login
python authorize_google.py

uvicorn api:app --port 8000
streamlit run app.py
```

To run the pipeline on its own: `python run_pipeline.py`

## Deploy to Cloud Run

The same Dockerfile serves both services. The `APP` variable chooses what starts (`api`, `ui` or `pipeline`).

```
gcloud run deploy venturelens-api --source . --region asia-south1 --allow-unauthenticated --memory 1Gi --timeout 900 --set-env-vars "APP=api,GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=your-project-id,GOOGLE_CLOUD_LOCATION=global,GCS_BUCKET=your-bucket-name,EMAIL_MODE=draft,COMMITTEE_EMAIL=committee@example.com" --set-secrets "GOOGLE_OAUTH_TOKEN_JSON=venturelens-oauth-token:latest"

gcloud run deploy venturelens-ui --source . --region asia-south1 --allow-unauthenticated --memory 1Gi --timeout 900 --set-env-vars "APP=ui,API_URL=<url of the api service>"
```

The Cloud Run service account needs these roles: Vertex AI User, Storage Object Admin, Cloud Datastore User, BigQuery Data Owner, BigQuery Job User and Secret Manager Secret Accessor.

Live deployment (may be taken down after evaluation):

- API: https://venturelens-api-13450891254.asia-south1.run.app
- UI: https://venturelens-ui-13450891254.asia-south1.run.app

Both services are public, and each evaluation uses Vertex AI credit and creates a Gmail draft and a Drive folder in the connected account.

## Status

- Full agent workflow, API, UI, PDF outputs, cloud storage, Gmail drafts and Drive storage are built and deployed.
- A full evaluation takes roughly 20 to 80 seconds on Cloud Run.
- Scoring is out of 100 (Market 30, Financial 40, Traction 30) with a cutoff of 60.
- The founder diagnostic is grounded in a knowledge base of reference documents (RAG), with sources listed in the report.
- Input and output guardrails, human-review flags and API key protection are in place.
