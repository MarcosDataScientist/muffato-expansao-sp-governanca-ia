FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir \
    mlflow==3.18.0 \
    scikit-learn>=1.3.0 \
    pandas>=2.0.0 \
    numpy>=1.24.0 \
    scipy>=1.11.0 \
    matplotlib>=3.8.0 \
    joblib>=1.3.0 \
    pyyaml>=6.0

EXPOSE 5000

CMD ["mlflow", "server", \
     "--host", "0.0.0.0", \
     "--port", "5000", \
     "--backend-store-uri", "sqlite:////mlflow/mlflow.db", \
     "--default-artifact-root", "mlflow-artifacts:/", \
     "--artifacts-destination", "/mlflow/mlartifacts", \
     "--serve-artifacts"]

