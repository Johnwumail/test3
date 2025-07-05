# Reranker Service (重排序服务)

## 1. 用途

Reranker Service 是模型服务层的关键组件，旨在提高搜索结果的相关性。它是一个高性能的 FastAPI 微服务，使用 Cross-Encoder 模型对从初始向量搜索中检索到的文档进行二次、计算量更大的评分。

通过接收用户查询和候选文档列表，它基于更深层次的语义理解对它们进行重新排序，将最相关的结果推到最前面。与 Embedding Service 一样，它也设计在启用 GPU 的 Kubernetes 节点上运行，以获得最佳性能。

## 2. API 使用方式

该服务提供两个主要端点：

### `POST /rerank`

这是用于根据查询对文档列表进行重新评分的主要端点。

*   **请求体:**

    ```json
    {
      "query": "如何配置HPA？",
      "docs": ["HPA是水平自动缩放...", "首先需要安装Metrics Server...", "这是另一个无关的文档。"]
    }
    ```

    *   `query` (str): 原始用户查询。
    *   `docs` (list[str]): 需要评分和重排序的文本文档列表。

*   **成功响应 (200 OK):**

    ```json
    {
      "scores": [0.98, 0.12, -2.5],
      "model_used": "BAAI/bge-reranker-base"
    }
    ```
    响应包含与输入文档相对应的分数列表。分数越高表示相关性越强。

### `GET /health`

一个标准的服务健康检查端点。

*   **成功响应 (200 OK):**

    ```json
    {
      "status": "ok"
    }
    ```

## 3. 配置

重排序模型可以通过环境变量进行配置：

*   `RERANKER_MODEL_NAME`: 要使用的 `sentence-transformers` 库中的 Cross-Encoder 模型名称。
    *   **默认值:** `BAAI/bge-reranker-base`

## 4. 部署

该服务使用提供的 `Dockerfile` 进行容器化。它旨在作为 Kubernetes `Deployment` 进行部署，通常调度在启用 GPU 的节点上以实现硬件加速。Retrieval API 依赖此服务来优化其搜索结果。