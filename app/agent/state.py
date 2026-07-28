from typing import TypedDict

from app.entities.column_info import  ColumnInfo
from app.entities.metric_info import MetricInfo
from app.entities.value_info import ValueInfo

class MetricInfoState(TypedDict):
    name: str
    description: str
    relevant_columns: list[str]
    alias: list[str]


class ColumnInfoState(TypedDict):
    name: str
    type: str
    role: str
    examples: list
    description: str
    alias: list[str]


class TableInfoState(TypedDict):
    name: str
    role: str
    description: str
    columns: list[ColumnInfoState]


class DateInfoState(TypedDict):
    date: str
    weekday: str
    quarter: str


class DBInfoState(TypedDict):
    dialect: str
    version: str



class DataAgentState(TypedDict):
    error: str                    #校验sql的准确信息

    keywords: list[str]             #抽取的关键词

    retrieved_column_infos: list[ColumnInfo] #检索的字段信息

    retrieved_metric_infos: list[MetricInfo] #检索的指标信息

    retrieved_value_infos: list[ValueInfo] #检索的字段取值信息

    table_infos: list[TableInfoState]     #过滤后的表信息

    metric_infos: list[MetricInfoState]   #过滤后的指标信息

    db_info: DBInfoState                 #数据库信息

    date_info: DateInfoState               #日期信息

    sql: str

    query: str                      #问题

    result: str                     #执行结果
