import unittest

from app.repositories.mysql.dw.dw_mysql_repository import DWMySQLRepository


class FakeMappings:
    def fetchall(self):
        return []


class FakeResult:
    def mappings(self):
        return FakeMappings()


class FakeSession:
    def __init__(self):
        self.statements = []

    async def execute(self, statement):
        self.statements.append(str(statement))
        return FakeResult()


class ReadOnlySQLTests(unittest.IsolatedAsyncioTestCase):
    async def test_select_query_is_executed(self):
        session = FakeSession()
        repository = DWMySQLRepository(session)

        result = await repository.run_sql("SELECT order_amount FROM fact_order;")

        self.assertEqual([], result)
        self.assertEqual(["SELECT order_amount FROM fact_order;"], session.statements)

    async def test_cte_select_query_is_executed(self):
        session = FakeSession()
        repository = DWMySQLRepository(session)

        await repository.run_sql(
            "WITH totals AS (SELECT SUM(order_amount) AS amount FROM fact_order) "
            "SELECT amount FROM totals"
        )

        self.assertEqual(1, len(session.statements))

    async def test_write_statement_is_rejected_before_database_execution(self):
        session = FakeSession()
        repository = DWMySQLRepository(session)

        with self.assertRaisesRegex(ValueError, "read-only"):
            await repository.run_sql("DELETE FROM fact_order")

        self.assertEqual([], session.statements)

    async def test_multiple_statements_are_rejected_before_validation(self):
        session = FakeSession()
        repository = DWMySQLRepository(session)

        with self.assertRaisesRegex(ValueError, "single SQL statement"):
            await repository.validate_sql("SELECT 1; DROP TABLE fact_order")

        self.assertEqual([], session.statements)

    async def test_file_export_is_rejected(self):
        session = FakeSession()
        repository = DWMySQLRepository(session)

        with self.assertRaisesRegex(ValueError, "read-only"):
            await repository.run_sql("SELECT * FROM fact_order INTO OUTFILE '/tmp/orders.csv'")

        self.assertEqual([], session.statements)

    async def test_sql_comments_are_rejected(self):
        session = FakeSession()
        repository = DWMySQLRepository(session)

        with self.assertRaisesRegex(ValueError, "comments"):
            await repository.run_sql("SELECT * FROM fact_order /* generated query */")

        self.assertEqual([], session.statements)

    async def test_server_file_reads_are_rejected(self):
        session = FakeSession()
        repository = DWMySQLRepository(session)

        with self.assertRaisesRegex(ValueError, "read-only"):
            await repository.run_sql("SELECT LOAD_FILE('/etc/passwd')")

        self.assertEqual([], session.statements)

    async def test_session_variable_assignment_is_rejected(self):
        session = FakeSession()
        repository = DWMySQLRepository(session)

        with self.assertRaisesRegex(ValueError, "read-only"):
            await repository.run_sql("SELECT @row_count := COUNT(*) FROM fact_order")

        self.assertEqual([], session.statements)

    async def test_forbidden_words_inside_string_literals_are_allowed(self):
        session = FakeSession()
        repository = DWMySQLRepository(session)

        await repository.run_sql("SELECT 'drop table' AS message")

        self.assertEqual(1, len(session.statements))


if __name__ == "__main__":
    unittest.main()
