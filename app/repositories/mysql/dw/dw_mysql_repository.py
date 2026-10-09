import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


_FORBIDDEN_SQL_TOKENS = {
    "ALTER",
    "BENCHMARK",
    "CALL",
    "CREATE",
    "DELETE",
    "DROP",
    "DUMPFILE",
    "GRANT",
    "HANDLER",
    "INSERT",
    "INTO",
    "LOAD",
    "LOAD_FILE",
    "LOCK",
    "RENAME",
    "REPLACE",
    "REVOKE",
    "SET",
    "SLEEP",
    "TRUNCATE",
    "UNLOCK",
    "UPDATE",
    "USE",
}


def _mask_quoted_content(sql: str) -> str:
    """Mask literals and identifiers so safety checks inspect SQL structure only."""
    masked: list[str] = []
    quote: str | None = None
    index = 0

    while index < len(sql):
        character = sql[index]
        next_character = sql[index + 1] if index + 1 < len(sql) else ""

        if quote:
            masked.append(" ")
            if character == quote:
                if next_character == quote:
                    masked.append(" ")
                    index += 2
                    continue

                backslash_count = 0
                previous_index = index - 1
                while previous_index >= 0 and sql[previous_index] == "\\":
                    backslash_count += 1
                    previous_index -= 1
                if backslash_count % 2 == 0:
                    quote = None
            index += 1
            continue

        if character in {"'", '"', "`"}:
            quote = character
            masked.append(" ")
            index += 1
            continue

        if (
            (character == "-" and next_character == "-")
            or character == "#"
            or (character == "/" and next_character == "*")
        ):
            raise ValueError("SQL comments are not allowed")

        masked.append(character)
        index += 1

    if quote:
        raise ValueError("SQL contains an unterminated quoted value")

    return "".join(masked)


def ensure_read_only_sql(sql: str) -> None:
    """Reject model output that is not one read-only SELECT statement."""
    if not isinstance(sql, str) or not sql.strip():
        raise ValueError("SQL must be a non-empty string")

    masked_sql = _mask_quoted_content(sql).strip()
    if masked_sql.endswith(";"):
        masked_sql = masked_sql[:-1].rstrip()
    if ";" in masked_sql:
        raise ValueError("Only a single SQL statement is allowed")

    first_keyword = re.match(r"^[A-Za-z_]+", masked_sql)
    if not first_keyword or first_keyword.group(0).upper() not in {"SELECT", "WITH"}:
        raise ValueError("Only read-only SELECT queries are allowed")

    tokens = set(re.findall(r"[A-Za-z_]+", masked_sql.upper()))
    if tokens & _FORBIDDEN_SQL_TOKENS:
        raise ValueError("Only read-only SELECT queries are allowed")
    if ":=" in masked_sql:
        raise ValueError("Only read-only SELECT queries are allowed")


class DWMySQLRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_column_types(self, table_name) -> dict[str, str]:
        sql = f"show columns from {table_name}"
        result = await self.session.execute(text(sql))
        result_dict = result.mappings().fetchall()
        # [{Field:order_id,Type:varchar(30),Null:No},{Field:customer_id,Type:varchar(20),Null:YES}]

        return {row['Field']: row['Type'] for row in result_dict}
        # {order_id:varchar(30),customer_id:varchar(30)}

    async def get_column_values(self, table_name, column_name, limit=10):
        sql = f"select distinct {column_name} from {table_name} limit {limit}"
        result = await self.session.execute(text(sql))
        return [row[0] for row in result.fetchall()]

    async def get_db_info(self):
        sql = "select version()"
        result = await self.session.execute(text(sql))
        version = result.scalar()
        dialect=self.session.bind.dialect.name
        return {"dialect":dialect,"version":version}

    async def validate_sql(self, sql: str):
        ensure_read_only_sql(sql)
        sql=f"explain {sql}"
        await self.session.execute(text(sql))

    async def run_sql(self, sql: str)-> list[dict]:
        ensure_read_only_sql(sql)
        sql = f"{sql}"
        result = await self.session.execute(text(sql))

        return [dict(row) for row in result.mappings().fetchall()]
