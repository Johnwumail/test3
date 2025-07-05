# Embedding Service (向量嵌入服务)

## 1. 用途

Embedding Service 是模型服务层的核心组件。它是一个高性能的 FastAPI 微服务，负责将批量文本转换为高质量的向量嵌入。

为了实现最佳性能，该服务设计运行在配备 GPU 的 Kubernetes 节点上。它利用 `sentence-transformers` 库加载并提供一个预训练的语言模型。数据摄取作业（Ingestion CronJob）依赖此服务将文档向量化，然后存入 Qdrant 向量数据库。

## 2. API 使用方式

该服务提供两个主要端点：

### `POST /embed`

这是用于生成向量嵌入的主要端点。

*   **请求体:**

    ```json
    {
      "texts": ["这是第一段文本。", "这是第二段文本。"],
      "normalize_embeddings": true
    }
    ```

    *   `texts` (list[str]): 需要被向量化的字符串列表。
    *   `normalize_embeddings` (bool, 可选): 是否将输出的向量归一化为单位长度。默认为 `true`。

*   **成功响应 (200 OK):**

    ```json
    {
      "embeddings": [
        [0.12, 0.45, ...],
        [0.67, 0.89, ...]
      ],
      "model_used": "BAAI/bge-large-zh-v1.5"
    }
    ```

### `GET /health`

一个标准的服务健康检查端点。

*   **成功响应 (200 OK):**

    ```json
    {
      "status": "ok"
    }
    ```

## 3. 配置

向量嵌入模型可以通过环境变量进行配置：

*   `MODEL_NAME`: 要使用的 `sentence-transformer` 模型名称。
    *   **默认值:** `BAAI/bge-large-zh-v1.5`

## 4. 部署

该服务使用项目提供的 `Dockerfile` 进行容器化。它旨在作为 Kubernetes `Deployment` 进行部署，通常调度在启用 GPU 的节点上以实现硬件加速。