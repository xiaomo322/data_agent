
from langgraph.runtime import Runtime

from app.agent.context import DataAgentContext
from app.agent.state import DataAgentState
from app.core.log import logger


async def validate_sql(state:DataAgentState,runtime:Runtime[DataAgentContext]):
    writer = runtime.stream_writer
    writer("开始验证SQL")
    sql = state["sql"]

    dw_mysql_repository = runtime.context["dw_mysql_repository"]

    await dw_mysql_repository.validate_sql(sql)

    try:
        await dw_mysql_repository.validate_sql(sql)
        logger.info("SQL验证成功")
        return {"error": None}
    except Exception as e:
        writer(f"SQL验证失败：{e}")
        logger.error(f"SQL验证失败：{e}")
        return {"error": str(e)}

