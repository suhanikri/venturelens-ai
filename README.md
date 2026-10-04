# VentureLens: FICCI FLO Multi-Agent Pitch Screening and Founder Feedback Engine

A multi-agent AI system on Google Cloud that screens startup pitch applications and produces transparent outputs for both the screening committee and the founder.

- **Accepted startups** get a 1-page due diligence memo with investor interview questions.
- **Rejected startups** get a diagnostic report with a scorecard, the exact rejection drivers and concrete steps to improve.

## Workflow

1. **Input:** the founder uploads a pitch deck (PDF) and a GST document (PDF).
2. **Extraction Agent:** reads both files and produces a structured JSON record.
3. **Gatekeeper Agent:** checks the mandatory eligibility and compliance requirements. Failures go straight to the Founder Diagnostic Agent.
4. **Parallel scoring:** the Market & TAM, Financial & CAC/LTV and Traction & Moat agents review the application at the same time. Each scorer runs three times and the median score is kept, which keeps scores stable between runs.
5. **Judge Agent:** adds up the sub-scores (Market 30 + Financial 40 + Traction 30 = 100 points) and compares the total with the cutoff (60). The total is calculated in Python, not by the model.
6. **Output:** the Committee Memo Agent (accepted) or the Founder Diagnostic Agent (rejected), each downloadable as a PDF.

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
| PDF reports | fpdf2 |

Every application is saved: the uploaded PDFs go to Cloud Storage, the full result goes to Firestore and one summary row goes to BigQuery.

## Project structure

```
agents/            the eight agents (extraction, gatekeeper, three scorers, judge, memo, diagnostic)
pipeline.py        the workflow and routing logic
api.py             FastAPI backend (POST /evaluate, GET /applications/{id}, GET /health)
app.py             Streamlit frontend
gcp_services.py    Cloud Storage, Firestore and BigQuery persistence
pdf_reports.py     committee memo and founder diagnostic PDFs
config.py          model name
sample_data/       dummy pitch deck and GST document
```

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
```

Sign in to Google Cloud once, then start both services in two terminals:

```
gcloud auth application-default login

uvicorn api:app --port 8000
streamlit run app.py
```

To run the pipeline on its own: `python run_pipeline.py`

## Deploy to Cloud Run

The same Dockerfile serves both services. The `APP` variable chooses what starts (`api`, `ui` or `pipeline`).

```
gcloud run deploy venturelens-api --source . --region asia-south1 --allow-unauthenticated --memory 1Gi --timeout 900 --set-env-vars "APP=api,GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_PROJECT=your-project-id,GOOGLE_CLOUD_LOCATION=global,GCS_BUCKET=your-bucket-name"

gcloud run deploy venturelens-ui --source . --region asia-south1 --allow-unauthenticated --memory 1Gi --timeout 900 --set-env-vars "APP=ui,API_URL=<url of the api service>"
```

Live deployment (may be taken down after evaluation):

- API: https://venturelens-api-13450891254.asia-south1.run.app
- UI: https://venturelens-ui-13450891254.asia-south1.run.app

## Status

- Full agent workflow, API, UI, PDF outputs and cloud storage are built and deployed.
- A full evaluation takes roughly 35 to 45 seconds on Cloud Run.
- Scoring is out of 100 (Market 30, Financial 40, Traction 30) with a cutoff of 60.

