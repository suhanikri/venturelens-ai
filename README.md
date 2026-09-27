# VentureLens

**Multi-Agent Pitch Screening & Founder Feedback Engine**

An agentic AI system built for FICCI FLO's startup pitch evaluation process. VentureLens automates the screening of pitch deck applications using specialized AI agents, replacing slow manual review and generic rejection emails with transparent, actionable feedback for founders.

## Problem

Organizations like FICCI FLO receive thousands of pitch applications for investment cohorts. Manual evaluation is slow, and over 90% of rejected applicants receive no real feedback on why they were cut or how to improve.

## Solution

A multi-agent pipeline powered by Google's Agent Development Kit (ADK) and the Gemini API automates screening and generates transparent outputs for both internal evaluators and founders:
- **Accepted startups** receive a 1-page due diligence memo for the screening committee
- **Rejected startups** receive a diagnostic report detailing exact rejection reasons and concrete improvement steps

## Pipeline Architecture

    Founder submits Pitch Deck (PDF) + GST Document
                |
                v
    1. Document Extraction & Ingestion Agent
       (Extracts data -> Structured JSON)
                |
                v
    2. Gatekeeper / Mandate Agent
       (Checks eligibility & compliance)
                |
        +-------+-------+
        |               |
     FAILED          PASSED
        |               |
        v               v
    5A. Founder      3. Multi-Agent Scorer (Parallel)
    Diagnostic       - Market & TAM Agent
    Agent            - Financial & CAC/LTV Agent
                     - Traction & Moat Agent
                             |
                             v
                     4. Orchestrator / Judge Agent
                     (Aggregates scores vs. cutoff)
                             |
                     +-------+-------+
                     |               |
                  REJECTED        ACCEPTED
                     |               |
                     v               v
             5A. Founder      5B. Committee Memo
             Diagnostic       Agent
             Agent

## Tech Stack

| Layer | Technology |
|---|---|
| Cloud Infrastructure | Google Cloud Platform (Cloud Run) |
| Core Language Models | Gemini 3.8 Flash (via Gemini API) |
| Agent Orchestration | Google Agent Development Kit (ADK) |
| Document Parsing | Gemini Multimodal Vision |
| Backend | Python / FastAPI |
| Frontend | Streamlit |
| File Storage | Google Cloud Storage |
| Structured Data | Firestore |
| Analytics | BigQuery |

## Project Status

Currently in active development as a capstone project.

### Completed
- [x] Project scaffolding and environment setup
- [x] Document Extraction & Ingestion Agent — reads Pitch Deck + GST PDFs, outputs structured JSON, tested with and without GST data present
- [x] Gatekeeper / Mandate Agent — validates GST presence, format, and status, tested on both pass and fail routing paths

### In Progress
- [ ] Market & TAM Agent
- [ ] Financial & CAC/LTV Agent
- [ ] Traction & Moat Agent
- [ ] Orchestrator / Judge Agent
- [ ] Founder Diagnostic Agent
- [ ] Committee Memo Agent
- [ ] GCP infrastructure setup (Cloud Storage, Firestore, BigQuery)
- [ ] FastAPI backend integration
- [ ] Streamlit frontend

## Project Structure

    venturelens/
    ├── agents/
    │   ├── extraction_agent.py
    │   └── gatekeeper_agent.py
    ├── sample_data/
    │   ├── dummy_pitch_deck.pdf
    │   └── dummy_gst_document.pdf
    ├── run_extraction_test.py
    ├── run_gatekeeper_test.py
    ├── run_gatekeeper_fail_test.py
    ├── generate_dummy_pdf.py
    ├── generate_dummy_gst.py
    ├── .env (not committed)
    ├── .gitignore
    └── README.md

## Setup

1. Clone the repo

       git clone https://github.com/suhanikri/venturelens-ai.git
       cd venturelens-ai

2. Create and activate a virtual environment

       python -m venv venv
       venv\Scripts\activate

3. Install dependencies

       pip install google-adk python-dotenv fpdf2

4. Add your Gemini API key to a `.env` file

       GOOGLE_API_KEY=your_api_key_here

5. Run a test

       python run_extraction_test.py

## Author

Suhani Kri — Capstone Project