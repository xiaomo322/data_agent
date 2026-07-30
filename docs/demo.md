# Data Agent 演示流程

这份文档用于记录一次完整的本地运行过程，方便 GitHub 访问者或面试官快速判断项目是否可复现。

## 1. 环境准备

建议环境：

| 工具 | 版本 |
| --- | --- |
| Python | 3.12+ |
| uv | latest |
| Node.js | 20+ |
| Docker Desktop | latest |

复制环境变量模板：

```powershell
Copy-Item conf/.env.example .env
```

填写 `.env`：

```env
MYSQL_ROOT_PASSWORD=your-root-password
MYSQL_USER=data_agent
MYSQL_PASSWORD=your-db-password
DATA_AGENT_TEXT_LLM_API_KEY=your-text-model-key
DATA_AGENT_CODE_LLM_API_KEY=your-code-model-key
```

## 2. 启动基础服务

```powershell
cd docker
docker compose --env-file ../.env up -d
cd ..
```

启动后建议检查：

```powershell
docker compose --env-file ../.env ps
```

预期看到 MySQL、Elasticsearch、Kibana、Qdrant、Embedding 服务均为运行状态。

## 3. 构建元数据索引

```powershell
uv sync
uv run python -m app.scripts.build_meta_knowledge -c conf/meta_config.yaml
```

这一步会读取 MySQL 中的表、字段、指标和维度值信息，并写入 Qdrant 与 Elasticsearch。

## 4. 启动后端

```powershell
uv run fastapi dev main.py
```

后端默认地址：

```text
http://127.0.0.1:8000
```

可检查：

```text
http://127.0.0.1:8000/healthz
http://127.0.0.1:8000/docs
```

## 5. 启动前端

```powershell
cd agent-fronted
npm install
npm run dev
```

前端默认地址：

```text
http://127.0.0.1:5173
```

## 6. 演示问题

可以在前端输入：

```text
统计上海地区的销售总额
```

或使用接口测试：

```powershell
curl -N -X POST http://127.0.0.1:8000/api/query `
  -H "Content-Type: application/json" `
  -d "{\"query\":\"统计上海地区的销售总额\"}"
```

预期效果：

- 页面显示 Agent 执行步骤，例如关键词扩展、字段召回、指标召回、SQL 生成、SQL 校验、SQL 执行。
- 后端通过 SSE 连续返回事件。
- 最终返回表格结果或明确的错误信息。

## 7. 截图建议

建议补充以下截图到 `docs/images/`：

| 截图 | 文件名 | 内容 |
| --- | --- | --- |
| 前端问数页面 | `frontend-query.png` | 输入自然语言问题后的完整页面 |
| SSE 执行过程 | `sse-stream.png` | 浏览器 Network、终端 curl 或页面步骤流 |
| 查询结果表格 | `query-result.png` | 最终返回的数据表格 |
| OpenAPI 文档 | `openapi-docs.png` | `http://127.0.0.1:8000/docs` 页面 |

截图补齐后，可以回到 README 取消“运行结果”区域中的图片注释。
