FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt requirements-gcp.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -r requirements-gcp.txt
# ADK needs this exact version; same fix as on your machine
RUN pip install --no-cache-dir --no-deps "opentelemetry-api==1.42.1"

COPY . .

# APP picks what starts: api (default), ui, or pipeline
ENV APP=api
CMD ["sh", "-c", "if [ \"$APP\" = \"ui\" ]; then exec streamlit run app.py --server.port=${PORT:-8080} --server.address=0.0.0.0 --server.headless=true --server.enableCORS=false --server.enableXsrfProtection=false; elif [ \"$APP\" = \"pipeline\" ]; then exec python run_pipeline.py; else exec uvicorn api:app --host 0.0.0.0 --port ${PORT:-8080}; fi"]
