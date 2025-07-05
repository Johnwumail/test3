
## 阶段一实施计划：基础文档语义搜索与 GPU 引入

**目标：** 建立基于 GPU 的高质量文档语义搜索能力，专注于通用文本数据。

本阶段的核心是构建一个具备基础数据摄取、GPU 加速的 Embedding 服务和 Reranker 服务、以及纯向量检索能力的知识库。

-----

### 1\. 人类需要提供的内容 (Human Contributions)

在 LLM Agent 开始实施之前，以下关键信息和环境准备需要由人类团队完成和提供。这些是 LLM Agent 无法自行获取或决定的上下文和权限。

  * **1.1. Kubernetes 集群访问与凭证：**
      * 提供 K8s 集群的 **kubeconfig 文件**或等效的**API 访问凭证**。
      * 指定 LLM Agent 应该在哪个 **Namespace (命名空间)** 中部署所有资源（例如：`knowledge-base-dev` 或 `kb-stage1`）。
      * 确认 LLM Agent 拥有在指定 Namespace 中创建、修改和删除 `Deployment`, `StatefulSet`, `Service`, `Ingress`, `PVC`, `CronJob` 等资源的权限。
  * **1.2. GPU 节点信息与确认：**
      * **确认集群中存在至少一个已正确配置 NVIDIA GPU Operator 的工作节点**。
      * 提供该 GPU 节点的 **Label (标签)** 信息，例如 `nvidia.com/gpu: "true"`，以便 LLM Agent 在 YAML 中正确配置 `nodeSelector`。
      * 如果 GPU 节点有 `taint (污点)`，需要提供相应的 `toleration (容忍)` 配置。
  * **1.3. 持久化存储 (Persistent Volume) 配置：**
      * 提供 K8s 集群中可用的 **StorageClass 名称**（例如：`ceph-rbd`, `nfs-client`, `standard-rwo` 等），用于动态创建 PVC。
      * 确认 StorageClass 具备 `ReadWriteOnce` 或 `ReadWriteMany` 访问模式，以满足不同组件的需求。
  * **1.4. Docker 镜像仓库凭证与地址：**
      * 提供用于存储 LLM Agent 生成的 Docker 镜像的**私有镜像仓库地址**（例如：`your-registry.example.com`）。
      * 提供访问该镜像仓库的**凭证**或创建 K8s `imagePullSecrets` 所需的信息。
  * **1.5. 数据源访问凭证与配置：**
      * **Jira API 凭证：** 用户名、API Token 或 OAuth 凭证。
      * **Confluence API 凭证：** 用户名、API Token 或 OAuth 凭证。
      * **Jira & Confluence 实例 URL：** 例如 `https://your-jira.com`, `https://your-confluence.com`。
      * **要抽取数据的项目 ID/Key 或 Confluence Space Key/Page ID 列表。**
      * **网页抓取起始 URL 列表或规则。**
      * **MinIO 访问凭证：** Access Key, Secret Key (LLM Agent 部署 MinIO 后，人类仍需提供初始访问凭证给摄取脚本)。
      * **LLM Agent 不需要直接拥有这些凭证，但需要知道如何通过 K8s Secret 或 ConfigMap 安全地注入给相应的 Pod。**
  * **1.6. 模型选择与确认：**
      * **指定用于 Embedding Service 和 Reranker Service 的具体模型名称**（例如：`BAAI/bge-large-zh-v1.5` 和 `BAAI/bge-reranker-base`）。
      * **确认这些模型是否可以通过 Hugging Face Hub 公开访问，或者需要从内部存储加载。** 如果是后者，需要提供模型文件的具体存储路径（如 MinIO 上的 Bucket 和 Key）。
  * **1.7. 团队协作与沟通：**
      * 明确 LLM Agent 提交代码和报告的**代码仓库路径**（例如：一个特定的 Git 分支或 MR）。
      * 指定人类团队将通过何种方式（如 Slack 频道、Jira Issue）接收 LLM Agent 的状态更新和问题报告。

-----

### 2\. 大模型实施所需要的所有内容 (LLM Agent's Implementation Scope)

LLM Agent 将根据上述人类提供的信息，结合阶段一的目标，执行以下步骤：

  * **2.1. 环境变量与配置管理：**
      * **从人类提供的信息中提取所有必要的配置参数**（如 K8s Namespace、GPU 标签、StorageClass 等）。
      * 将敏感凭证设计为 K8s `Secret`，将非敏感配置设计为 K8s `ConfigMap`。
      * 在生成的 YAML 文件中，通过 `envFrom` 或 `valueFrom` 引用这些 Secret 和 ConfigMap。
  * **2.2. K8s YAML 清单文件生成：**
      * **2.2.1. MinIO 部署：**
          * 生成 **`minio-pvc.yaml`**: 定义 MinIO 数据存储的 PVC (100Gi, `ReadWriteOnce`, 使用人类提供的 StorageClass)。
          * 生成 **`minio-deployment.yaml`**: 定义 MinIO 的 `StatefulSet` (1 个副本)，挂载上述 PVC，配置 MinIO `ACCESS_KEY` 和 `SECRET_KEY` （从 K8s Secret 引用），开放 9000 和 9001 端口。
          * 生成 **`minio-service.yaml`**: 定义 `ClusterIP` Service，用于 K8s 内部访问。
      * **2.2.2. Qdrant/Weaviate 部署：** (以 Qdrant 为例)
          * 生成 **`qdrant-pvc.yaml`**: 定义 Qdrant 数据存储的 PVC (例如 50Gi, `ReadWriteOnce`, 使用人类提供的 StorageClass)。
          * 生成 **`qdrant-deployment.yaml`**: 定义 Qdrant 的 `StatefulSet` (1 个副本)，挂载上述 PVC，开放 6333 (gRPC) 和 6334 (HTTP) 端口。
          * 生成 **`qdrant-service.yaml`**: 定义 `ClusterIP` Service。
      * **2.2.3. Embedding Service 部署：**
          * **代码生成：** 编写 **Python FastAPI 应用代码** (`main.py`)，使用 `sentence-transformers` 或 `transformers` 加载指定模型，暴露 `/embed` API 端点，支持批量推理。
          * **Dockerfile 生成：** 编写 `Dockerfile`，包含 Python 运行时、FastAPI 依赖、CUDA/PyTorch 基础镜像（确保兼容 GPU），并将 `main.py` 和模型文件（如果打包到镜像中）添加到镜像中。
          * 生成 **`embedding-service-deployment.yaml`**: 定义 `Deployment` (1 个副本)，配置 `nodeSelector` 和 `tolerations` 将其调度到 GPU 节点，请求并限制 `nvidia.com/gpu: 1` 资源，暴露 8000 端口。
          * 生成 **`embedding-service-service.yaml`**: 定义 `ClusterIP` Service。
      * **2.2.4. Reranker Service 部署：**
          * **代码生成：** 编写 **Python FastAPI 应用代码** (`main.py`)，使用 `sentence-transformers` 加载指定 Reranker 模型，暴露 `/rerank` API 端点，支持批量推理。
          * **Dockerfile 生成：** 编写 `Dockerfile`，与 Embedding Service 类似。
          * 生成 **`reranker-service-deployment.yaml`**: 定义 `Deployment` (1 个副本)，同样配置 GPU 调度和资源限制，暴露 8000 端口。
          * 生成 **`reranker-service-service.yaml`**: 定义 `ClusterIP` Service。
      * **2.2.5. 数据摄取 (Ingestion) CronJob 部署：**
          * **代码生成：** 编写 **Python 脚本** (`ingest_data.py`)，实现 Jira、Confluence、网页、Markdown、PPT/邮件的数据抽取、清洗、通用文本分块逻辑。
          * **内部调用：** 脚本将通过 K8s Service 名称（例如 `http://embedding-service:8000/embed`）调用 Embedding Service 获取向量，并将向量和元数据写入 Qdrant/Weaviate，原始数据写入 MinIO。
          * **Dockerfile 生成：** 编写 `Dockerfile`，包含 Python 运行时和所有必要的库。
          * 生成 **`ingestion-cronjob.yaml`**: 定义 `CronJob`，配置定时调度（例如每天运行一次），挂载必要的 K8s Secret 或 ConfigMap 以获取数据源凭证。
      * **2.2.6. 核心检索 API (FastAPI) 部署：**
          * **代码生成：** 编写 **Python FastAPI 应用代码** (`api.py`)，暴露 `/query` 端点。实现纯向量检索逻辑，并通过 K8s Service 名称调用 Reranker Service (`http://reranker-service:8000/rerank`)。
          * **Dockerfile 生成：** 编写 `Dockerfile`。
          * 生成 **`retrieval-api-deployment.yaml`**: 定义 `Deployment` (1 个副本)，暴露 8000 端口。
          * 生成 **`retrieval-api-service.yaml`**: 定义 `ClusterIP` Service。
          * 生成 **`retrieval-api-ingress.yaml`**: 定义 `Ingress`，将外部流量路由到 `retrieval-api-service`。
      * **2.2.7. 额外的 K8s 配置：**
          * 生成用于存储敏感信息的 K8s `Secret` YAMLs（例如数据源凭证）。
          * 生成用于存储非敏感配置的 K8s `ConfigMap` YAMLs。
  * **2.3. Docker 镜像构建与推送：**
      * 对于所有生成的 `Dockerfile`，LLM Agent 将执行 **`docker build`** 命令构建 Docker 镜像。
      * 执行 **`docker push`** 命令将构建好的镜像推送到人类指定的私有镜像仓库。
  * **2.4. K8s 资源部署：**
      * 按依赖顺序，使用 **`kubectl apply -f <file.yaml>`** 命令将所有生成的 YAML 文件应用到 K8s 集群中，包括 PVCs, Deployments, StatefulSets, Services, Ingress, CronJobs。
      * 部署顺序示例：PVCs -\> MinIO -\> Qdrant/Weaviate -\> Embedding Service -\> Reranker Service -\> Retrieval API -\> Ingestion CronJob。
  * **2.5. 状态监控与初步报告：**
      * 执行 **`kubectl get pods -n <namespace>`**，`kubectl get deployments -n <namespace>` 等命令，检查所有 Pod 和服务的运行状态。
      * 简要报告所有部署成功的服务及其对应的 K8s IP/域名。
      * 记录部署过程中遇到的任何错误或警告。

-----

### 3\. 人类如何验证 (Human Verification)

在 LLM Agent 完成部署后，人类团队需要进行以下验证步骤，以确保系统按预期工作并满足阶段一的目标。

  * **3.1. K8s 资源状态检查：**
      * 执行 `kubectl get all -n <namespace>`：确认所有 `Pod`, `Deployment`, `StatefulSet`, `Service`, `Ingress`, `CronJob` 均处于 `Running` 或 `Completed` 状态，没有 `CrashLoopBackOff` 或其他错误状态。
      * 检查 GPU Pod 调度：执行 `kubectl describe pod <embedding-service-pod-name>`，确认 Pod 已成功调度到 GPU 节点，并且 GPU 资源（`nvidia.com/gpu: 1`）已被正确分配。
      * 检查 PVC 绑定：执行 `kubectl get pvc -n <namespace>`，确认所有 PVCs 均已成功绑定到 PV。
  * **3.2. 服务连通性测试：**
      * **MinIO 访问：** 尝试通过 `kubectl port-forward` 或 Ingress 访问 MinIO 控制台，使用提供的凭证登录，确认 MinIO 正常运行。
      * **Qdrant/Weaviate 访问：** 通过 `kubectl port-forward` 访问其 API 端口，或通过简单的 Python 客户端连接，确认数据库可访问。
      * **Embedding Service 测试：**
          * 使用 `curl` 或 Postman/Python 脚本向 Ingress 暴露的 Retrieval API 的 `/query` 端点发送测试请求，或者直接通过 `kubectl port-forward` 访问 Embedding Service 的内部 IP/端口，发送一个简单文本数组，验证其是否能返回向量嵌入。
          * **示例请求 (Python):**
            ```python
            import requests
            import json

            embedding_service_url = "http://<Retrieval-API-Ingress-URL>/embed" # 或直接通过 port-forward 的 IP:Port
            headers = {"Content-Type": "application/json"}
            payload = {"texts": ["这是一个测试句子。", "另一个句子。"], "normalize_embeddings": True}

            try:
                response = requests.post(embedding_service_url, headers=headers, data=json.dumps(payload))
                response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)
                result = response.json()
                print("Embedding Service 响应:", result)
                assert "embeddings" in result and len(result["embeddings"]) == 2
                assert len(result["embeddings"][0]) > 0 # 向量长度大于0
                print("Embedding Service 测试成功!")
            except Exception as e:
                print(f"Embedding Service 测试失败: {e}")
            ```
      * **Reranker Service 测试：**
          * 通过 `kubectl port-forward` 访问 Reranker Service 的内部 IP/端口，发送测试请求，验证其是否能返回得分。
          * **示例请求 (Python):**
            ```python
            import requests
            import json

            reranker_service_url = "http://localhost:8000/rerank" # 假设通过 port-forward 到 8000
            headers = {"Content-Type": "application/json"}
            payload = {
                "query": "关于项目计划",
                "docs": ["项目计划书详细介绍了项目目标。", "这份报告与项目无关。"]
            }

            try:
                response = requests.post(reranker_service_url, headers=headers, data=json.dumps(payload))
                response.raise_for_status()
                result = response.json()
                print("Reranker Service 响应:", result)
                assert "scores" in result and len(result["scores"]) == 2
                print("Reranker Service 测试成功!")
            except Exception as e:
                print(f"Reranker Service 测试失败: {e}")
            ```
  * **3.3. 数据摄取验证：**
      * 检查 `ingestion-cronjob` 的运行日志：`kubectl logs -f $(kubectl get pods -l job-name=<ingestion-cronjob-name> -o jsonpath='{.items[0].metadata.name}')`，确认脚本正常运行，没有明显错误。
      * 验证数据是否成功入库：
          * 在 MinIO 中检查是否存在新上传的原始数据文件（如 Jira JSON, Confluence HTML）。
          * 在 Qdrant/Weaviate 中查询，确认是否存在新的向量数据，并且其元数据与预期一致。
  * **3.4. 核心检索 API 功能验证：**
      * 通过 Ingress 暴露的检索 API (例如 `http://<your-ingress-domain>/query`) 发送实际的自然语言查询。
      * **示例请求 (Python):**
        ```python
        import requests
        import json

        api_url = "http://<your-ingress-domain>/query"
        headers = {"Content-Type": "application/json"}
        query_payload = {"text": "项目A的需求文档是什么？"} # 示例查询

        try:
            response = requests.post(api_url, headers=headers, data=json.dumps(query_payload))
            response.raise_for_status()
            result = response.json()
            print("检索 API 响应:", result)
            assert "results" in result and len(result["results"]) > 0 # 确认有返回结果
            print("核心检索 API 功能验证成功!")
        except Exception as e:
            print(f"核心检索 API 功能验证失败: {e}")
        ```
      * 分析返回结果的**相关性**：人工评估返回的文本块是否与查询高度相关，这是语义搜索质量的关键验证。
  * **3.5. 可观测性验证：**
      * 确认 Pod 日志可被正确收集。
      * 检查 Prometheus/Grafana 中是否能看到各 Pod 的 CPU、内存和 GPU 利用率指标。

-----

**交付物 (LLM Agent 提交)：**

  * 所有生成的 K8s YAML 清单文件。
  * 所有生成的 Python 应用程序代码和 `Dockerfile`。
  * 一个部署报告，包含部署过程的日志、所有 K8s 资源的 `kubectl get all` 输出、以及初步的服务连通性测试结果。
  * 任何在实施过程中发现的问题或需要人工介入的依赖项。

