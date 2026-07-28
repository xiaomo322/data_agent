# Data Agent

面向企业数据仓库的 NL2SQL 智能问数系统。用户以自然语言提出问题，系统检索表、字段、指标和维度值等元数据，生成 SQL 并通过预检、执行和错误回写完成校正，再以 SSE 将执行过程和查询结果流式返回前端。

> 这是一个用于展示 LLM 应用工程能力的可运行项目：重点在于检索增强、工作流编排、SQL 风险控制与可观测的流式交互，而不是让模型直接“猜”出 SQL。

## 核心能力

- **12 节点 LangGraph 工作流**：关键词扩展、三路并行召回、上下文合并、表/指标筛选、SQL 生成、校验、修复与执行。
- **混合元数据检索**：Qdrant 负责字段/指标语义召回，Elasticsearch 负责维度值全文召回，LLM 进行相关性筛选。
- **SQL 自校正闭环**：通过 `EXPLAIN` 预检、执行错误上下文回灌和二次生成，降低表名、字段和语法幻觉。
- **流式可观测性**：FastAPI + SSE 推送工作流进度和最终结果；Vue 3 页面实时呈现执行步骤与表格结果。
- **基础设施即代码**：Docker Compose 一键启动 MySQL、Elasticsearch、Kibana、Qdrant 与 embedding 服务。

## 架构

```text
自然语言问题
    │
    ▼
关键词扩展 ──► 字段语义召回 (Qdrant)
    ├────────► 指标语义召回 (Qdrant)
    └────────► 维度值召回 (Elasticsearch)
                         │
                         ▼
                 上下文合并与筛选
                         │
                         ▼
          SQL 生成 → EXPLAIN 预检 → 执行
                         │              │
                         └── 错误上下文回灌 ──► SQL 修复
                                               │
                                               ▼
                                      SSE 流式返回前端
```

## 技术栈

| 层级 | 技术 |
| --- | --- |
| Agent 编排 | LangGraph、LangChain |
| 后端 | Python 3.12、FastAPI、SQLAlchemy、asyncmy、SSE |
| 检索 | Qdrant、Elasticsearch、BGE-large-zh-v1.5 |
| 存储 | MySQL 8.0 |
| 前端 | Vue 3、Vite |
| 部署 | Docker Compose |

## 快速开始

### 1. 准备配置

```bash
cp conf/.env.example .env
# 编辑 .env，填写 MySQL 密码和 LLM API Key
```

PowerShell：

```powershell
Copy-Item conf/.env.example .env
```

`conf/app_config.yaml` 使用环境变量，不会保存真实密码或 API Key。若本机运行后端，请将 `.env` 中需要的变量导入当前终端。

### 2. 启动依赖服务

```bash
cd docker
docker compose --env-file ../.env up -d
cd ..
```

Embedding 模型在容器第一次启动时由镜像拉取；仓库不包含模型权重。

### 3. 安装后端并构建元数据

```bash
uv sync
uv run python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml
uv run fastapi dev main.py
```

服务默认监听 `http://127.0.0.1:8000`，可访问 `/docs` 查看 OpenAPI 文档。

### 4. 启动前端

```bash
cd agent-fronted
npm install
npm run dev
```

Vite 开发服务器已将 `/api` 代理到 `http://localhost:8000`。

## API 示例

`POST /api/query` 使用 SSE 返回工作流事件：

```bash
curl -N -X POST http://127.0.0.1:8000/api/query \
  -H "Content-Type: application/json" \
  -d '{"query":"统计 2025 年各地区销售总额"}'
```

响应为 `data: {...}` 形式的 SSE 事件，事件可表示节点进度、查询结果或错误信息。

## 项目结构

```text
app/
  agent/          # LangGraph 状态、节点与工作流
  api/            # FastAPI 路由和依赖注入
  clients/        # MySQL、Qdrant、ES、Embedding 客户端
  repositories/   # 元数据与检索仓储层
  services/       # 查询服务与 SSE 输出
  scripts/        # 元数据构建脚本
agent-fronted/    # Vue 3 可视化客户端
conf/             # 可公开的配置模板
docker/           # MySQL、ES、Qdrant、Embedding 编排
prompts/          # SQL 生成、修复和筛选提示词
```

## 安全说明

- `.env`、模型权重、日志、缓存和前端构建产物均已忽略，不应提交。
- 请始终通过环境变量提供数据库密码和 LLM API Key。
- 执行生产数据库前，应增加只读账号、SQL 白名单和资源限额；本项目的示例数据仅用于本地演示。

## 简历描述（可直接使用）

> 基于 LangGraph 构建 NL2SQL 智能问数系统：通过 Qdrant 向量检索、Elasticsearch 全文检索与 LLM 重排序召回企业元数据，设计“SQL 生成 - EXPLAIN 预检 - 执行验证 - 错误回写”的自校正闭环；以 FastAPI + SSE 输出工作流事件，并通过 Docker Compose 编排 MySQL、Qdrant、Elasticsearch 和 Embedding 服务。

