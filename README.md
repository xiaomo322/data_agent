# Data Agent

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-SSE-009688?logo=fastapi&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Agent-1C3C3C)
![Vue](https://img.shields.io/badge/Vue-3-42B883?logo=vuedotjs&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)

面向企业数据仓库的 NL2SQL 智能问数系统。用户用自然语言提出问题，系统会检索表、字段、指标和维度值等元数据，生成 SQL，并通过预检、执行、错误回写完成自校正，最后用 SSE 将执行过程和查询结果流式返回前端。

这个项目重点展示的是 LLM 应用工程能力：检索增强、Agent 工作流编排、SQL 风险控制、流式交互和可观测执行链路，而不是让模型直接“猜”SQL。

## 项目亮点

| 能力 | 实现方式 | 价值 |
| --- | --- | --- |
| 自然语言问数 | FastAPI + LangGraph 编排 NL2SQL 工作流 | 降低业务人员查询数据的使用门槛 |
| 元数据增强 | Qdrant 语义召回 + Elasticsearch 维度值召回 | 让模型基于真实表结构、指标口径和维度值生成 SQL |
| SQL 自校正 | `EXPLAIN` 预检、执行错误回写、二次修复 | 降低表名、字段名、语法和口径幻觉 |
| 流式反馈 | SSE 推送节点进度、SQL、结果和错误信息 | 前端可展示完整执行过程，便于调试和面试演示 |
| 本地可运行 | Docker Compose 编排 MySQL、ES、Qdrant、Embedding 服务 | 便于复现项目，不依赖线上数据库 |

## 运行结果

下面预留了运行截图位置。完成本地启动后，建议把图片放到 `docs/images/`，再替换对应路径，这样 GitHub 首页会更有说服力。

完整演示步骤见 [docs/demo.md](docs/demo.md)。

| 展示项 | 建议文件 | 状态 |
| --- | --- | --- |
| 前端问数页面 | `docs/images/frontend-query.png` | 待补充 |
| Agent 执行过程 / SSE 事件流 | `docs/images/sse-stream.png` | 待补充 |
| 查询结果表格 | `docs/images/query-result.png` | 待补充 |
| OpenAPI 文档或健康检查 | `docs/images/openapi-docs.png` | 待补充 |

<!--
截图补充后可以取消下面注释：

### 前端问数页面

![前端问数页面](docs/images/frontend-query.png)

### SSE 执行过程

![SSE 执行过程](docs/images/sse-stream.png)

### 查询结果

![查询结果](docs/images/query-result.png)
-->

## 工作流

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
| 后端服务 | Python 3.12、FastAPI、SQLAlchemy、asyncmy、SSE |
| 检索增强 | Qdrant、Elasticsearch、BGE-large-zh-v1.5 |
| 数据存储 | MySQL 8.0 |
| 前端页面 | Vue 3、Vite |
| 本地部署 | Docker Compose |

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

`conf/app_config.yaml` 使用环境变量读取敏感信息，仓库不会保存真实数据库密码或 API Key。若本机直接运行后端，请将 `.env` 中需要的变量导入当前终端。

### 2. 启动依赖服务

```bash
cd docker
docker compose --env-file ../.env up -d
cd ..
```

依赖服务包括 MySQL、Elasticsearch、Kibana、Qdrant 和 embedding 服务。Embedding 模型在容器第一次启动时由镜像拉取，仓库不包含模型权重。

### 3. 安装后端并构建元数据

```bash
uv sync
uv run python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml
uv run fastapi dev main.py
```

服务默认监听 `http://127.0.0.1:8000`，可访问 `http://127.0.0.1:8000/docs` 查看 OpenAPI 文档。

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

响应为 `data: {...}` 形式的 SSE 事件，事件可表示节点进度、召回上下文、生成 SQL、查询结果或错误信息。

```text
data: {"event":"node_start","node":"recall_column"}
data: {"event":"node_end","node":"generate_sql","sql":"SELECT ..."}
data: {"event":"result","columns":["region","sales_amount"],"rows":[...]}
```

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
- 执行生产数据库前，应增加只读账号、SQL 白名单和资源限额；本项目示例数据仅用于本地演示。
