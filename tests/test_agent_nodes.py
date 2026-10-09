import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch


os.environ.setdefault("DATA_AGENT_TEXT_LLM_API_KEY", "test-key")
os.environ.setdefault("DATA_AGENT_CODE_LLM_API_KEY", "test-key")

from app.agent.nodes import correct_sql as correct_sql_module
from app.agent.nodes import filter_metric as filter_metric_module
from app.agent.nodes import filter_table as filter_table_module
from app.agent.nodes.validate_sql import validate_sql


class FakeChain:
    def __init__(self, response):
        self.response = response
        self.payload = None

    def __or__(self, _other):
        return self

    async def ainvoke(self, payload):
        self.payload = payload
        return self.response


class FakeSQLRepository:
    def __init__(self, error=None):
        self.error = error
        self.calls = []

    async def validate_sql(self, sql):
        self.calls.append(sql)
        if self.error:
            raise self.error


class ValidateSQLTests(unittest.IsolatedAsyncioTestCase):
    async def test_successful_validation_executes_explain_once(self):
        repository = FakeSQLRepository()
        events = []
        runtime = SimpleNamespace(
            stream_writer=events.append,
            context={"dw_mysql_repository": repository},
        )

        result = await validate_sql({"sql": "SELECT 1"}, runtime)

        self.assertEqual({"error": None}, result)
        self.assertEqual(["SELECT 1"], repository.calls)

    async def test_validation_error_is_returned_for_graph_routing(self):
        repository = FakeSQLRepository(RuntimeError("unknown column"))
        events = []
        runtime = SimpleNamespace(
            stream_writer=events.append,
            context={"dw_mysql_repository": repository},
        )

        result = await validate_sql({"sql": "SELECT missing FROM fact_order"}, runtime)

        self.assertEqual({"error": "unknown column"}, result)
        self.assertEqual(["SELECT missing FROM fact_order"], repository.calls)
        self.assertTrue(any("SQL验证失败" in str(event) for event in events))


class CorrectSQLTests(unittest.IsolatedAsyncioTestCase):
    async def test_database_context_is_serialized_for_the_correction_prompt(self):
        chain = FakeChain("SELECT 1")
        state = {
            "query": "统计销售额",
            "table_infos": [],
            "metric_infos": [],
            "date_info": {"date": "2026-10-09"},
            "db_info": {"dialect": "mysql", "version": "8.0.45"},
            "sql": "SELECT broken",
            "error": "syntax error",
        }
        runtime = SimpleNamespace(stream_writer=lambda _event: None, context={})

        with (
            patch.object(correct_sql_module, "PromptTemplate", return_value=chain),
            patch.object(correct_sql_module, "StrOutputParser", return_value=object()),
            patch.object(correct_sql_module, "load_prompt", return_value="template"),
        ):
            result = await correct_sql_module.correct_sql(state, runtime)

        self.assertEqual({"sql": "SELECT 1"}, result)
        self.assertIn("dialect: mysql", chain.payload["db_info"])
        self.assertIn("version: 8.0.45", chain.payload["db_info"])


class FilterStateTests(unittest.IsolatedAsyncioTestCase):
    async def test_table_filter_replaces_table_infos_in_graph_state(self):
        chain = FakeChain({"fact_order": ["order_amount"]})
        state = {
            "query": "统计销售额",
            "table_infos": [
                {
                    "name": "fact_order",
                    "columns": [
                        {"name": "order_amount"},
                        {"name": "order_quantity"},
                    ],
                }
            ],
        }
        runtime = SimpleNamespace(stream_writer=lambda _event: None, context={})

        with (
            patch.object(filter_table_module, "PromptTemplate", return_value=chain),
            patch.object(filter_table_module, "JsonOutputParser", return_value=object()),
            patch.object(filter_table_module, "load_prompt", return_value="template"),
        ):
            result = await filter_table_module.filter_table(state, runtime)

        self.assertEqual("fact_order", result["table_infos"][0]["name"])
        self.assertEqual(
            ["order_amount"],
            [column["name"] for column in result["table_infos"][0]["columns"]],
        )
        self.assertNotIn("filter_table_infos", result)

    async def test_metric_filter_replaces_metric_infos_in_graph_state(self):
        chain = FakeChain(["GMV"])
        state = {
            "query": "统计销售额",
            "metric_infos": [
                {"name": "GMV"},
                {"name": "AOV"},
            ],
        }
        runtime = SimpleNamespace(stream_writer=lambda _event: None, context={})

        with (
            patch.object(filter_metric_module, "PromptTemplate", return_value=chain),
            patch.object(filter_metric_module, "JsonOutputParser", return_value=object()),
            patch.object(filter_metric_module, "load_prompt", return_value="template"),
        ):
            result = await filter_metric_module.filter_metric(state, runtime)

        self.assertEqual(["GMV"], [metric["name"] for metric in result["metric_infos"]])
        self.assertNotIn("filter_metric_infos", result)


if __name__ == "__main__":
    unittest.main()
