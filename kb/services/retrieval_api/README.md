# Retrieval API (检索API)

## 1. 用途

Retrieval API 是智能知识库的主要入口点。它是一个基于 FastAPI 的微服务，负责响应用户的自然语言查询，并编排整个搜索和检索过程。

其工作流程如下：
1.  接收用户查询。
2.  调用 **Embedding Service** 将查询文本转换为向量嵌入。
3.  在 **Qdrant** 向量数据库中执行相似性搜索，以找到一组初始的候选文档。
4.  将查询和候选文档发送到 **Reranker Service** 进行更精细的相关性评分。
5.  根据重排序器的分数对结果进行排序，并向用户返回最终的、有序的文档列表。

该服务有效地集成了系统的所有其他组件，提供了一个单一、统一的搜索端点。

## 2. API 使用方式

该服务提供两个主要端点：

### `POST /query`

这是主要的搜索端点。

*   **请求体:**

    ```json
    {
      "text": "如何为我们的服务配置水平自动缩放？"
    }
    ```

    *   `text` (str): 用户的自然语言查询。

*   **成功响应 (200 OK):**

    ```json
    {
      "results": [
        {
          "id": "some-uuid-1",
          "payload": {
            "text": "HPA是水平自动缩放...",
            "source": "confluence-123"
          },
          "score": 0.98
        },
        {
          "id": "some-uuid-2",
          "payload": {
            "text": "首先需要安装Metrics Server...",
            "source": "jira-456"
          },
          "score": 0.12
        }
      ]
    }
    ```
    `results` 按相关性排序，得分最高的结果排在最前面。`payload` 包含文档文本及其原始元数据。

### `GET /health`

一个标准的服务健康检查端点。

*   **成功响应 (200 OK):**

    ```json
    {
      "status": "ok"
    }
    ```

## 3. 配置

Retrieval API 需要以下环境变量来连接其依赖项：

*   `QDRANT_ENDPOINT`: Qdrant 向量数据库的主机名 (例如, `qdrant`)。
*   `EMBEDDING_SERVICE_URL`: Embedding Service `/embed` 端点的完整 URL (例如, `http://embedding-service:8000/embed`)。
*   `RERANKER_SERVICE_URL`: Reranker Service `/rerank` 端点的完整 URL (例如, `http://reranker-service:8000/rerank`)。

## 4. 部署

该服务使用提供的 `Dockerfile` 进行容器化。它作为标准的 Kubernetes `Deployment` 进行部署，并且通常通过 Kubernetes `Ingress` 资源暴露给用户，使其成为知识库面向公众的组件。