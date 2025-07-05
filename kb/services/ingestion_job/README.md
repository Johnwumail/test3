# Ingestion Job (数据摄取作业)

## 1. 用途

Ingestion Job 是一个数据处理组件，作为 Kubernetes `CronJob` 定期运行。其主要职责是编排知识库的数据摄取流程。

该流程包括：
1.  从各种数据源（当前为 Jira 和 Confluence 的占位逻辑）获取原始数据。
2.  调用 **Embedding Service** 将文本数据转换为向量嵌入。
3.  将原始数据工件存储在 **MinIO** 对象存储中。
4.  将相应的向量嵌入和元数据存储在 **Qdrant** 向量数据库中。

该作业确保知识库与已配置的数据源保持同步，包含最新的信息。

## 2. 使用方式

该服务不是一个 API 服务器，而是一个从头到尾执行的 Python 脚本 (`ingest_data.py`)。在项目的 Kubernetes 设置中，它由 `CronJob` 资源按预定计划触发。

要手动运行它（用于测试或开发），您需要在已安装必要依赖项并设置了环境变量的环境中直接执行该 Python 脚本。

## 3. 配置

Ingestion Job 完全依赖环境变量进行配置。

### 数据源 (占位符)
*   `JIRA_URL`: Jira 实例的 URL。
*   `JIRA_USERNAME`: 用于 Jira 身份验证的用户名。
*   `JIRA_API_TOKEN`: 用于 Jira 身份验证的 API 令牌。
*   `CONFLUENCE_URL`: Confluence 实例的 URL。
*   `CONFLUENCE_USERNAME`: 用于 Confluence 身份验证的用户名。
*   `CONFLUENCE_API_TOKEN`: 用于 Confluence 身份验证的 API 令牌。

### 服务依赖
*   `MINIO_ENDPOINT`: MinIO 服务器的端点 URL (例如, `minio:9000`)。
*   `MINIO_ACCESS_KEY`: MinIO 的访问密钥。
*   `MINIO_SECRET_KEY`: MinIO 的私有密钥。
*   `QDRANT_ENDPOINT`: Qdrant 向量数据库的主机名 (例如, `qdrant`)。
*   `EMBEDDING_SERVICE_URL`: Embedding Service `/embed` 端点的完整 URL (例如, `http://embedding-service:8000/embed`)。

## 4. 部署

该作业使用提供的 `Dockerfile` 进行容器化，并设计为作为 Kubernetes `CronJob` 进行部署。其执行计划和其他作业参数在 `k8s/phase1/` 目录中相应的 YAML 清单文件中定义。