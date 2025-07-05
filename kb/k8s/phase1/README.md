# Phase 1: Deployment Configuration

This directory contains all the necessary Kubernetes YAML files to deploy Phase 1 of the Intelligent Knowledge Base.

## Configuration

Before applying these configurations, please review and edit the placeholder values in the YAML files located in the `configs/` subdirectory.

### Main Configuration Parameters:

These values are used across multiple YAML files and should be replaced with your environment-specific settings.

1.  **Namespace:**
    *   All resources will be deployed in a specific namespace.
    *   **Placeholder:** `knowledge-base`
    *   **File to edit:** `configs/00-namespace.yaml`

2.  **Docker Registry & Image Pull Secret:**
    *   The Docker images built for the services need to be pushed to your private registry.
    *   **Placeholder:** `your-docker-registry/your-repo`
    *   **Image Pull Secret:** `regcred` (This secret must be created in your namespace manually).
    *   **Files to edit:** All `Deployment` and `CronJob` YAML files.

3.  **StorageClass:**
    *   The PersistentVolumeClaims (PVCs) need a StorageClass to provision storage.
    *   **Placeholder:** `standard`
    *   **Files to edit:** `configs/minio.yaml`, `configs/qdrant.yaml`

4.  **GPU Node Configuration:**
    *   The Embedding and Reranker services need to be scheduled on nodes with GPUs.
    *   **GPU Node Selector Label:** `nvidia.com/gpu: "true"`
    *   **GPU Node Toleration:** A commented-out example is provided in the deployment files if your GPU nodes have taints.
    *   **Files to edit:** `configs/embedding-service.yaml`, `configs/reranker-service.yaml`

5.  **Secrets:**
    *   Data source credentials (Jira, Confluence) and MinIO credentials need to be set.
    *   **File to edit:** `configs/01-secrets.yaml`. The values are base64 encoded. You can create them using `echo -n 'your-password' | base64`.

### Deployment

Once you have updated the configuration, you can deploy all resources by running the `deploy.sh` script from this directory:

```bash
bash deploy.sh
```
