-----

好的，这是一个**专为 LLM Agent 准备的、用于实施智能知识库阶段一的完整文档**。这份文档结合了项目的**宏观背景**、**阶段一所需的核心设计细节**以及**具体的实施计划与验证步骤**，旨在提供 LLM Agent 准确理解并高效执行任务所需的所有上下文和指令。

-----

# 智能知识库项目：阶段一实施指南 (面向 LLM Agent)

## 1\. 项目概述与核心架构

本智能知识库项目旨在为**项目开发人员**提供快速、全面的项目全貌、设计细节、代码信息和问题解决方案；同时，为**大语言模型（LLM）Agent**提供高质量的上下文信息，以辅助其进行复杂任务。

我们的解决方案融合了**检索增强生成（RAG）** 和 **知识图谱（Knowledge Graph）** 的核心优势，并充分考虑了在 **Kubernetes (K8s) 环境下进行部署，并从项目初期就利用 GPU 资源进行模型推理**的需求。

-----

### 1.1 核心架构概览

我们的知识库将采用**三层架构**：数据摄取与预处理层、数据存储层、以及索引与检索层。所有组件都将容器化部署在 Kubernetes 集群中，GPU 节点将专门用于模型推理。

```
+-----------------------------------------------------------------------------------------+
|                                  **Kubernetes Cluster** |
| +---------------------+   +---------------------+   +---------------------+           |
| |   **Worker Node 1** |   |   **Worker Node 2** |   |   **Worker Node 3** |           |
| | (CPU/Memory)        |   | (CPU/Memory)        |   | (CPU/Memory)        |           |
| +---------------------+   +---------------------+   +---------------------+           |
|          |                         |                         |                          |
|          V                         V                         V                          |
| +-------------------------------------------------------------------------------------+ |
| |                                 **Centralized Storage** | |
| | +---------------------+     +---------------------+     +---------------------+   | |
| | | **持久卷 (PV)** | | **持久卷 (PV)** | | **持久卷 (PV)** | |
| | | (Neo4j, Qdrant/Weaviate | | (MinIO 数据)         | | (代码仓库/原始数据) | |
| | |  数据)              |     |                     |     |                     |   | |
| | +---------------------+     +---------------------+     +---------------------+   | |
| +-------------------------------------------------------------------------------------+ |
|                                                                                         |
| +-------------------------------------------------------------------------------------+ |
| |                  **控制平面 (Master 节点 - 未明确绘制)** | |
| +-------------------------------------------------------------------------------------+ |
|                                         |                                             |
| +-----------------------------------------------------------------------------------------+
| |                            **GPU 工作节点 (Minimum 1x initially, scaling to 4x)** |
| | +---------------------+   +---------------------+   +---------------------+           |
| | |   **GPU Node 1** |   |   **GPU Node 2** |   |   **GPU Node 3** |           |
| | | (CPU/内存/GPU)    |   | (CPU/内存/GPU)    |   | (CPU/内存/GPU)    |           |
| | +---------------------+   +---------------------+ +---------------------+           |
| +-----------------------------------------------------------------------------------------+
|                                         |                                             |
|                                         |                                             |
| +-----------------------------------------------------------------------------------------+
| |                                 **Knowledge Base Applications (Pods)** |
| | +---------------------+ +---------------------+ +---------------------+ +---------------------+ |
| | | **数据摄取/解析** | | **Neo4j Pods** | | **Qdrant/Weaviate** | | **FastAPI API Pods**| |
| | | (批处理/定时任务)   | | (有状态集)       | | (有状态集)       | | (部署)              | |
| | +---------------------+ +---------------------+ +---------------------+ +---------------------+ |
| | +---------------------+ +---------------------+ +---------------------+ +---------------------+ |
| | | **Embedding 服务** | | **Reranker 服务** | | **MinIO Pods** | | **LLM 推理** | |
| | | (GPU 部署)        | | (GPU 部署)        | | (有状态集)       | | (GPU 部署)        | |
| | +---------------------+ +---------------------+ +---------------------+ +---------------------+ |
+-----------------------------------------------------------------------------------------+
```

-----

## 2\. 阶段一：基础文档语义搜索与 GPU 引入

**目标：** 建立基于 GPU 的高质量文档语义搜索能力，专注于通用文本数据。

本阶段的核心是构建一个具备基础数据摄取、GPU 加速的 Embedding 服务和 Reranker 服务、以及纯向量检索能力的知识库。本阶段暂不涉及知识图谱构建、代码数据处理及 LLM Agent 的复杂集成。

-----

### 2.1 阶段一相关设计细节

为确保 LLM Agent 对当前阶段要实施的组件有清晰的理解，以下是与阶段一直接相关的详细设计说明。

### 2.1.1 数据摄取与预处理层 (Ingestion & Preprocessing Layer) - 阶段一范围

**目标：** 从多源抽取数据，进行清洗、标准化、文本化，并为向量化做准备。

  * **数据连接器与抽取（插件式设计）：**
      * **设计原则：** 预留接口，支持未来更多数据源的插件式扩展。
      * **本阶段核心连接器：**
          * **Jira & Confluence：** 编写 **Python 脚本**，利用官方 **REST API** 周期性（如每日）拉取 Issue（详情、评论、附件链接、状态、优先级等）、Sprint 信息、Confluence 页面内容（HTML 结构和纯文本）、附件链接。
          * **网页：** 使用 **BeautifulSoup** 和 **Requests** (Python 库) 进行网页抓取，可配置 URL 列表或爬取规则。
          * **PPT/Markdown/邮件：** 使用相应的 Python 库（`python-pptx`、`markdown`、`imaplib` 等）解析内容。
  * **数据清洗与标准化：**
      * **统一数据模型：** 定义一个核心的、标准化的数据模型（例如，`Document`、`Issue`）。
      * **标准化模块：** 移除 HTML 标签、Markdown 格式符、特殊字符、多余空白。将源数据字段映射到标准模型字段。提取通用元数据：`source_type`, `doc_id` (唯一标识符), `title`, `author`, `created_date`, `last_modified_date`, `url` (如果适用), `project_name`。
  * **文本分块 (Chunking) 与上下文保留：**
      * 使用 **LangChain** 或 **LlamaIndex** 提供的 **`TextSplitters`** (例如 `RecursiveCharacterTextSplitter`)。
      * **通用文本策略：** 将文档分割成语义完整的、大小适中的**文本块 (chunks)**，通常每个块包含 200-500 个 token，并设置适当的**重叠 (overlap)** 以保留上下文。

### 2.1.2 数据存储层 (Storage Layer) - 阶段一范围

**目标：** 存储处理后的原始数据和向量嵌入。

  * **原始数据湖：**
      * **技术：** **MinIO** (私有部署的 S3 兼容对象存储)。
      * **用途：** 存储原始 Jira JSON, Confluence HTML/XML, 网页快照, PPT/Markdown/邮件的原始文件。
      * **K8s 部署：** 通过 **`StatefulSet`** 部署 MinIO，其数据目录通过 **PVC** 持久化。
  * **向量数据库 (Vector Database)：**
      * **技术：** **Qdrant** 或 **Weaviate** (LLM Agent 需选择其中之一)。
      * **内容：** 存储所有经过文本分块处理后的文本块的**向量嵌入**。
      * **元数据：** 每个向量条目应包含丰富的元数据，如 `source_type`, `doc_id`, `title`, `author`, `last_modified_date`, `project_name`, `issue_key`, `page_id` 等。这些元数据将用于**过滤检索结果**。
      * **K8s 部署：** 通过 **`StatefulSet`** 部署，其数据目录通过 **PVC** 持久化。

### 2.1.3 索引与检索层 (Indexing & Retrieval Layer) - 阶段一范围

**目标：** 提供基础的文本向量化、重排序和纯向量检索能力。

  * **核心检索API：**
      * **技术：** 使用 **FastAPI** 构建一个高性能的 RESTful API。
      * **端点：** 主要提供一个 `/query` 或 `/search` 端点，接收用户的自然语言查询和可选的过滤参数（如 `project_name`, `source_type`）。
  * **向量嵌入服务 (Embedding Service) 与 Reranker 服务 详细设计与部署：**
      * **Embedding 服务设计：**
          * **目标：** 提供一个高性能、可伸缩的 API 接口，用于将文本转换为向量嵌入，并利用 GPU 进行加速。
          * **技术栈：** 使用 **FastAPI** 构建 RESTful API 服务，核心的 Embedding 模型通过 **Hugging Face `transformers` 库** 或 **`sentence-transformers` 库** 加载和运行。
          * **API 接口设计：**
              * **端点：** `POST /embed`
              * **请求体：** `{"texts": ["文本句子1", "文本句子2", ...], "normalize_embeddings": true}`
              * **响应体：** `{"embeddings": [[0.1, ...], [0.3, ...]], "model_used": "..."}`
              * **功能：** 支持**批量处理**。
          * **模型加载与管理：** 服务启动时，将模型**一次性加载到 GPU 内存**。模型权重文件**直接打包到 Docker 镜像中**或从外部（如 MinIO）拉取并缓存到本地磁盘。
      * **Reranker 服务设计：**
          * **技术栈：** 同样使用 **FastAPI** 封装 **Sentence Transformers** 库中的 Reranker 模型。
          * **API 接口：** 提供 `/rerank` 端点，接收查询文本和候选文本对，返回它们的得分。
          * **K8s 部署：** 同样作为独立的 `Deployment` 部署在 GPU 节点上。
      * **vLLM 或 Ollama 等模型引擎的适用性：** 对于 Embedding Service，**优先推荐直接使用 FastAPI 封装 `transformers` 或 `sentence-transformers` 库进行部署**。vLLM 主要针对 LLM 生成推理优化，Ollama 更适合本地部署。在生产级 K8s 环境下，直接使用 `transformers` + FastAPI 提供了足够的性能和可控性。
      * **K8s 部署细节 (示例):** LLM Agent 应根据此示例生成对应的 YAML。
        ```yaml
        apiVersion: apps/v1
        kind: Deployment
        metadata:
          name: embedding-service
          labels:
            app: embedding-service
        spec:
          replicas: 1 # 初始副本数
          selector:
            matchLabels:
              app: embedding-service
          template:
            metadata:
              labels:
                app: embedding-service
            spec:
              nodeSelector:
                nvidia.com/gpu: "true" # 从人类提供获取
              tolerations: # 从人类提供获取，如果适用
                - key: "nvidia.com/gpu"
                  operator: "Exists"
                  effect: "NoSchedule"
              containers:
                - name: embedding-service-container
                  image: your-registry/embedding-service:latest # LLM Agent 构建并推送到此
                  ports:
                    - containerPort: 8000
                  resources:
                    limits:
                      nvidia.com/gpu: 1
                      memory: "16Gi"
                      cpu: "4"
                    requests:
                      nvidia.com/gpu: 1
                      memory: "8Gi"
                      cpu: "2"
                  env: # 环境变量，指定模型名称等
                    - name: MODEL_NAME
                      value: "BAAI/bge-large-zh-v1.5" # 从人类提供获取
                  # volumeMounts 和 volumes 仅在模型从外部加载并缓存时需要
                  # (此处简化为镜像打包模型，LLM Agent 可根据人类指令调整)
        ---
        apiVersion: v1
        kind: Service
        metadata:
          name: embedding-service
        spec:
          selector:
            app: embedding-service
          ports:
            - protocol: TCP
              port: 8000
              targetPort: 8000
        # HPA 暂不在此阶段详细配置，留待后续优化
        ```
  * **检索逻辑与融合 (RAG 核心) - 阶段一范围：**
      * **查询向量化：** 调用 **Embedding Service** 将用户输入转换为向量。
      * **向量检索：** 使用查询向量在**向量数据库**中执行**语义相似度搜索**，检索 Top-N 最相关的文本块。同时利用元数据过滤。
      * **Reranking (重排序)：** 对检索到的候选文本块，调用 **Reranker Service** 进行二次排序。

-----

### 2.2 多阶段稳健实施方案概述

为了降低项目风险并逐步验证核心价值，我们采用**分阶段实施**方法。

  * **阶段一：基础文档语义搜索与 GPU 引入**
      * **目标：** 建立基于 GPU 的高质量文档语义搜索能力，专注于通用文本数据。
      * **关键交付：** MinIO、向量数据库、GPU 加速的 Embedding/Reranker 服务、基础数据摄取和纯向量检索 API。
  * **阶段二：引入知识图谱与结构化知识查询**
      * **目标：** 增强结构化知识查询能力，并初步构建实体关系图谱。
  * **阶段三：全面高可用与 LLM Agent 集成准备**
      * **目标：** 全面提升所有核心组件的生产级可用性和弹性，并为 LLM Agent 集成提供高性能接口。
  * **阶段四：引入代码知识与高级功能**
      * **目标：** 将代码信息纳入知识库，并探索多模态检索和离线分析。
  * **阶段五：知识演化、反馈闭环与生产级完善**
      * **目标：** 建立知识库的持续改进机制，并实现生产环境的最高标准。

**LLM Agent 须知：** 本文档当前仅聚焦于**阶段一**的实施。请严格按照阶段一的要求执行，不要提前实现后续阶段的功能。

-----

### 2.3 阶段一实施计划

### 2.3.1. 人类需要提供的内容 (Human Contributions)

在 LLM Agent 开始实施之前，以下关键信息和环境准备需要由人类团队完成和提供。这些是 LLM Agent 无法自行获取或决定的上下文和权限。

  * **1. K8s 集群访问与凭证：**
      * 提供 K8s 集群的 **kubeconfig 文件**或等效的**API 访问凭证**。
      * 指定 LLM Agent 应该在哪个 **Namespace (命名空间)** 中部署所有资源（例如：`knowledge-base-dev` 或 `kb-stage1`）。
      * 确认 LLM Agent 拥有在指定 Namespace 中创建、修改和删除 `Deployment`, `StatefulSet`, `Service`, `Ingress`, `PVC`, `CronJob` 等资源的权限。
  * **2. GPU 节点信息与确认：**
      * **确认集群中存在至少一个已正确配置 NVIDIA GPU Operator 的工作节点**。
      * 提供该 GPU 节点的 **Label (标签)** 信息，例如 `nvidia.com/gpu: "true"`，以便 LLM Agent 在 YAML 中正确配置 `nodeSelector`。
      * 如果 GPU 节点有 `taint (污点)`，需要提供相应的 `toleration (容忍)` 配置。
  * **3. 持久化存储 (Persistent Volume) 配置：**
      * 提供 K8s 集群中可用的 **StorageClass 名称**（例如：`ceph-rbd`, `nfs-client`, `standard-rwo` 等），用于动态创建 PVC。
      * 确认 StorageClass 具备 `ReadWriteOnce` 或 `ReadWriteMany` 访问模式。
  * **4. Docker 镜像仓库凭证与地址：**
      * 提供用于存储 LLM Agent 生成的 Docker 镜像的**私有镜像仓库地址**（例如：`your-registry.example.com`）。
      * 提供访问该镜像仓库的**凭证**或创建 K8s `imagePullSecrets` 所需的信息。
  * **5. 数据源访问凭证与配置：**
      * **Jira API 凭证：** 用户名、API Token 或 OAuth 凭证。
      * **Confluence API 凭证：** 用户名、API Token 或 OAuth 凭证。
      * **Jira & Confluence 实例 URL：** 例如 `https://your-jira.com`, `https://your-confluence.com`。
      * **要抽取数据的项目 ID/Key 或 Confluence Space Key/Page ID 列表。**
      * **网页抓取起始 URL 列表或规则。**
      * **MinIO 访问凭证：** Access Key, Secret Key (LLM Agent 部署 MinIO 后，人类仍需提供初始访问凭证给摄取脚本)。
      * **LLM Agent 不需要直接拥有这些凭证，但需要知道如何通过 K8s Secret 或 ConfigMap 安全地注入给相应的 Pod。**
  * **6. 模型选择与确认：**
      * **指定用于 Embedding Service 和 Reranker Service 的具体模型名称**（例如：`BAAI/bge-large-zh-v1.5` 和 `BAAI/bge-reranker-base`）。
      * **确认这些模型是否可以通过 Hugging Face Hub 公开访问，或者需要从内部存储加载。** 如果是后者，需要提供模型文件的具体存储路径（如 MinIO 上的 Bucket 和 Key）。
  * **7. 团队协作与沟通：**
      * 明确 LLM Agent 提交代码和报告的**代码仓库路径**（例如：一个特定的 Git 分支或 MR）。
      * 指定人类团队将通过何种方式（如 Slack 频道、Jira Issue）接收 LLM Agent 的状态更新和问题报告。

-----

### 2.3.2. 大模型实施所需要的所有内容 (LLM Agent's Implementation Scope)

LLM Agent 将根据上述人类提供的信息，结合阶段一的目标，执行以下步骤：

  * **1. 环境变量与配置管理：**
      * **从人类提供的信息中提取所有必要的配置参数**（如 K8s Namespace、GPU 标签、StorageClass 等）。
      * 将敏感凭证设计为 K8s `Secret`，将非敏感配置设计为 K8s `ConfigMap`。
      * 在生成的 YAML 文件中，通过 `envFrom` 或 `valueFrom` 引用这些 Secret 和 ConfigMap。
  * **2. K8s YAML 清单文件生成：**
      * **2.1. MinIO 部署：**
          * 生成 **`minio-pvc.yaml`**: 定义 MinIO 数据存储的 PVC (例如 100Gi, `ReadWriteOnce`, 使用人类提供的 StorageClass)。
          * 生成 **`minio-deployment.yaml`**: 定义 MinIO 的 `StatefulSet` (1 个副本)，挂载上述 PVC，配置 MinIO `ACCESS_KEY` 和 `SECRET_KEY` （从 K8s Secret 引用），开放 9000 和 9001 端口。
          * 生成 **`minio-service.yaml`**: 定义 `ClusterIP` Service。
      * **2.2. Qdrant/Weaviate 部署：** (LLM Agent 需选择 Qdrant 或 Weaviate 进行部署，并生成相应 YAML)
          * 生成 **`vector-db-pvc.yaml`**: 定义向量数据库数据存储的 PVC (例如 50Gi, `ReadWriteOnce`, 使用人类提供的 StorageClass)。
          * 生成 **`vector-db-deployment.yaml`**: 定义向量数据库的 `StatefulSet` (1 个副本)，挂载上述 PVC，开放所需端口。
          * 生成 **`vector-db-service.yaml`**: 定义 `ClusterIP` Service。
      * **2.3. Embedding Service 部署：**
          * **代码生成：** 编写 **Python FastAPI 应用代码** (`embedding_app.py`)，使用 `sentence-transformers` 或 `transformers` 加载人类指定的模型，暴露 `/embed` API 端点，支持批量推理。
          * **Dockerfile 生成：** 编写 `Dockerfile`，包含 Python 运行时、FastAPI 依赖、CUDA/PyTorch 基础镜像（确保兼容 GPU），并将 `embedding_app.py` 和模型文件（如果打包到镜像中）添加到镜像中。
          * 生成 **`embedding-service-deployment.yaml`**: 定义 `Deployment` (1 个副本)，配置 `nodeSelector` 和 `tolerations` 将其调度到 GPU 节点，请求并限制 `nvidia.com/gpu: 1` 资源，暴露 8000 端口。
          * 生成 **`embedding-service-service.yaml`**: 定义 `ClusterIP` Service。
      * **2.4. Reranker Service 部署：**
          * **代码生成：** 编写 **Python FastAPI 应用代码** (`reranker_app.py`)，使用 `sentence-transformers` 加载人类指定的 Reranker 模型，暴露 `/rerank` API 端点，支持批量推理。
          * **Dockerfile 生成：** 编写 `Dockerfile`，与 Embedding Service 类似。
          * 生成 **`reranker-service-deployment.yaml`**: 定义 `Deployment` (1 个副本)，同样配置 GPU 调度和资源限制，暴露 8000 端口。
          * 生成 **`reranker-service-service.yaml`**: 定义 `ClusterIP` Service。
      * **2.5. 数据摄取 (Ingestion) CronJob 部署：**
          * **代码生成：** 编写 **Python 脚本** (`ingest_data.py`)，实现 Jira、Confluence、网页、Markdown、PPT/邮件的数据抽取、清洗、通用文本分块逻辑。
          * **内部调用：** 脚本将通过 K8s Service 名称（例如 `http://embedding-service:8000/embed`）调用 Embedding Service 获取向量，并将向量和元数据写入 Qdrant/Weaviate，原始数据写入 MinIO。
          * **Dockerfile 生成：** 编写 `Dockerfile`，包含 Python 运行时和所有必要的库。
          * 生成 **`ingestion-cronjob.yaml`**: 定义 `CronJob`，配置定时调度（例如每天运行一次），挂载必要的 K8s Secret 或 ConfigMap 以获取人类提供的数据源凭证。
      * **2.6. 核心检索 API (FastAPI) 部署：**
          * **代码生成：** 编写 **Python FastAPI 应用代码** (`retrieval_api.py`)，暴露 `/query` 端点。实现纯向量检索逻辑，并通过 K8s Service 名称调用 Reranker Service (`http://reranker-service:8000/rerank`)。
          * **Dockerfile 生成：** 编写 `Dockerfile`。
          * 生成 **`retrieval-api-deployment.yaml`**: 定义 `Deployment` (1 个副本)，暴露 8000 端口。
          * 生成 **`retrieval-api-service.yaml`**: 定义 `ClusterIP` Service。
          * 生成 **`retrieval-api-ingress.yaml`**: 定义 `Ingress`，将外部流量路由到 `retrieval-api-service`。
      * **2.7. 额外的 K8s 配置：**
          * 生成用于存储敏感信息的 K8s `Secret` YAMLs（例如数据源凭证，MinIO 凭证）。
          * 生成用于存储非敏感配置的 K8s `ConfigMap` YAMLs。
  * **3. Docker 镜像构建与推送：**
      * 对于所有生成的 `Dockerfile`，LLM Agent 将执行 **`docker build`** 命令构建 Docker 镜像。
      * 执行 **`docker push`** 命令将构建好的镜像推送到人类指定的私有镜像仓库。
  * **4. K8s 资源部署：**
      * 按依赖顺序，使用 **`kubectl apply -f <file.yaml>`** 命令将所有生成的 YAML 文件应用到 K8s 集群中，包括 PVCs, Deployments, StatefulSets, Services, Ingress, CronJobs。
      * **部署顺序建议：** PVCs -\> MinIO -\> 向量数据库 (Qdrant/Weaviate) -\> Embedding Service -\> Reranker Service -\> Retrieval API -\> Ingestion CronJob。
  * **5. 状态监控与初步报告：**
      * 执行 **`kubectl get pods -n <namespace>`**，`kubectl get deployments -n <namespace>` 等命令，检查所有 Pod 和服务的运行状态。
      * 简要报告所有部署成功的服务及其对应的 K8s IP/域名。
      * 记录部署过程中遇到的任何错误或警告，并尝试根据报错信息进行初步诊断和修正。

-----

### 2.3.3. 人类如何验证 (Human Verification)

在 LLM Agent 完成部署后，人类团队需要进行以下验证步骤，以确保系统按预期工作并满足阶段一的目标。

  * **1. K8s 资源状态检查：**
      * 执行 `kubectl get all -n <namespace>`：确认所有 `Pod`, `Deployment`, `StatefulSet`, `Service`, `Ingress`, `CronJob` 均处于 `Running` 或 `Completed` 状态，没有 `CrashLoopBackOff` 或其他错误状态。
      * 检查 GPU Pod 调度：执行 `kubectl describe pod <embedding-service-pod-name>`，确认 Pod 已成功调度到 GPU 节点，并且 GPU 资源（`nvidia.com/gpu: 1`）已被正确分配。
      * 检查 PVC 绑定：执行 `kubectl get pvc -n <namespace>`，确认所有 PVCs 均已成功绑定到 PV。
  * **2. 服务连通性测试：**
      * **MinIO 访问：** 尝试通过 `kubectl port-forward` 或 Ingress 访问 MinIO 控制台，使用提供的凭证登录，确认 MinIO 正常运行。
      * **向量数据库 (Qdrant/Weaviate) 访问：** 通过 `kubectl port-forward` 访问其 API 端口，或通过简单的 Python 客户端连接，确认数据库可访问。
      * **Embedding Service 测试：**
          * 使用 `curl` 或 Postman/Python 脚本向 Ingress 暴露的 Retrieval API 的 `/query` 端点发送测试请求，或者直接通过 `kubectl port-forward` 访问 Embedding Service 的内部 IP/端口，发送一个简单文本数组，验证其是否能返回向量嵌入。
          * **示例请求 (Python):**
            ```python
            import requests
            import json

            # 请替换为实际的 Embedding Service URL（可能是通过 port-forward 或 Ingress 暴露的内部 URL）
            embedding_service_url = "http://localhost:8000/embed"
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

            # 请替换为实际的 Reranker Service URL
            reranker_service_url = "http://localhost:8000/rerank"
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
  * **3. 数据摄取验证：**
      * 检查 `ingestion-cronjob` 的运行日志：`kubectl logs -f $(kubectl get pods -l job-name=<ingestion-cronjob-name> -o jsonpath='{.items[0].metadata.name}')`，确认脚本正常运行，没有明显错误。
      * 验证数据是否成功入库：
          * 在 MinIO 中检查是否存在新上传的原始数据文件（如 Jira JSON, Confluence HTML）。
          * 在向量数据库中查询，确认是否存在新的向量数据，并且其元数据与预期一致。
  * **4. 核心检索 API 功能验证：**
      * 通过 Ingress 暴露的检索 API (例如 `http://<your-ingress-domain>/query`) 发送实际的自然语言查询。
      * **示例请求 (Python):**
        ```python
        import requests
        import json

        # 请替换为实际的 Retrieval API Ingress URL
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
  * **5. 可观测性验证：**
      * 确认所有 Pod 的日志可被正确收集（如通过 `kubectl logs` 查看）。
      * 确认 Prometheus/Grafana 中是否能看到各 Pod 的 CPU、内存和 GPU 利用率指标（如果已部署监控栈）。

-----

### 2.3.4. 交付物 (LLM Agent 提交)

在完成阶段一的所有实施和自验证后，LLM Agent 必须提交以下交付物：

  * **1. K8s YAML 清单文件：**
      * 所有生成的 YAML 文件，包括 `Deployment`, `StatefulSet`, `Service`, `Ingress`, `PVC`, `CronJob`, `Secret`, `ConfigMap`。
      * 这些文件应按照模块清晰组织在 Git 仓库中。
  * **2. 应用程序代码与 Dockerfile：**
      * 所有生成的 Python FastAPI 应用程序代码（`embedding_app.py`, `reranker_app.py`, `retrieval_api.py`）。
      * 数据摄取脚本 (`ingest_data.py`)。
      * 所有相关联的 `Dockerfile`。
      * 这些代码和 `Dockerfile` 应清晰地组织在 Git 仓库中。
  * **3. 部署报告：**
      * 一份 Markdown 格式的报告，包含：
          * 部署过程的详细日志输出。
          * 所有 K8s 资源的 `kubectl get all -n <namespace>` 命令输出。
          * 所有服务连通性测试的详细结果（包括请求和响应示例）。
          * 数据摄取 Job 的运行日志摘录，确认数据成功入库的证据。
          * 核心检索 API 的功能验证结果，包括查询和返回结果示例。
          * 在实施过程中发现的任何问题、错误或需要人工介入的依赖项，以及 LLM Agent 尝试的解决方案。
  * **4. Docker 镜像列表：**
      * 所有已成功构建并推送到指定镜像仓库的 Docker 镜像的名称和标签。

-----