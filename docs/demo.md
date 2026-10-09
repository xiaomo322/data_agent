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

## 7. 已收录的运行证据

| 截图 | 文件 | 展示内容 |
| --- | --- | --- |
| 系统首页 | [`01-home.png`](images/01-home.png) | 智能问数入口与示例问题 |
| 前端运行结果 | [`02-query-result.png`](images/02-query-result.png) | Agent 执行步骤与分类销售额结果表格 |
| GMV 执行链路 | [`03-gmv-trace.png`](images/03-gmv-trace.png) | 召回、筛选、SQL 生成、校验与执行日志 |
| 分类销售额链路 | [`04-category-trace.png`](images/04-category-trace.png) | 多表 JOIN 和 `GROUP BY` 查询的完整后端记录 |

截图与日志仅展示本地模拟数据，不包含 API Key、数据库密码或真实业务数据。
