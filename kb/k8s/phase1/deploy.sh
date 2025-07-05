#!/bin/bash

# This script deploys all the resources for Phase 1 of the knowledge base.
# It applies the YAML files in a specific order to ensure dependencies are met.

# Exit immediately if a command exits with a non-zero status.
set -e

# Check if kubectl is installed
if ! command -v kubectl &> /dev/null
then
    echo "kubectl could not be found. Please install it and configure access to your cluster."
    exit 1
fi

# Define the base directory for config files
CONFIG_DIR="./configs"

echo "🚀 Starting deployment of the Knowledge Base...
"

# Step 1: Namespace, Secrets, and ConfigMaps
echo "🔹 Applying Namespace, Secrets, and ConfigMap..."
kubeclt apply -f "${CONFIG_DIR}/00-namespace.yaml"
kubeclt apply -f "${CONFIG_DIR}/01-secrets.yaml"
kubeclt apply -f "${CONFIG_DIR}/02-configmap.yaml"
echo "✅ Namespace, Secrets, and ConfigMap applied.
"

# Step 2: Storage Layer (MinIO and Qdrant)
# These are StatefulSets with PVCs, so they should be created first.
echo "🔹 Applying Storage Layer: MinIO and Qdrant..."
kubeclt apply -f "${CONFIG_DIR}/minio.yaml"
kubeclt apply -f "${CONFIG_DIR}/qdrant.yaml"
echo "✅ Storage Layer applied. Waiting for StatefulSets to be ready..."
# Note: In a production script, you might add a `kubectl rollout status` command here.

# Step 3: Model Services Layer (GPU-accelerated)
echo "
🔹 Applying Model Services Layer: Embedding and Reranker Services..."
kubeclt apply -f "${CONFIG_DIR}/embedding-service.yaml"
kubeclt apply -f "${CONFIG_DIR}/reranker-service.yaml"
echo "✅ Model Services Layer applied.
"

# Step 4: API Layer
echo "🔹 Applying API Layer: Retrieval API..."
kubeclt apply -f "${CONFIG_DIR}/retrieval-api.yaml"
echo "✅ API Layer applied.
"

# Step 5: Data Processing Layer
echo "🔹 Applying Data Processing Layer: Ingestion CronJob..."
kubeclt apply -f "${CONFIG_DIR}/ingestion-cronjob.yaml"
echo "✅ Data Processing Layer applied.
"

echo "🎉 Deployment script finished successfully!"
echo "
To check the status of your resources, run:
kubectl get all -n <your-namespace>
"