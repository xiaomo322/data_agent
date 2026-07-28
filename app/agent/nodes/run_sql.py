from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def run_sql(state: DataAgentState, runtime: Runtime[DataAgentContext]):
    writer = runtime.stream_writer

    # 1. 发送步骤开始
    writer("开始执行SQL")

    sql = state["sql"]
    dw_mysql_repository = runtime.context["dw_mysql_repository"]

    try:
        result = await dw_mysql_repository.run_sql(sql)
        logger.info(f"SQL执行结果：{result}")

        # 2. ✅ 存入 state（后续节点可能用到）
        state["result"] = result

        # 3. ✅ 转换结果为前端表格格式并发送
        if isinstance(result, list) and len(result) > 0:
            # 已经是数组（如 [{列: 值}, ...]）
            writer({
                "type": "result",
                "data": result
            })
        elif isinstance(result, list) and len(result) == 0:
            writer({
                "type": "result",
                "data": [],
                "message": "查询成功，返回空结果"
            })
        else:
            # 其他格式，包装成单条数据
            writer({
                "type": "result",
                "data": [{"结果": str(result)}]
            })

    except Exception as e:
        error_msg = str(e)
        state["error"] = error_msg
        logger.error(f"SQL执行失败：{error_msg}")

        # 4. ✅ 发送错误到前端
        writer({
            "type": "error",
            "message": f"SQL执行失败: {error_msg}"
        })

    return state