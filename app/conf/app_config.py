from dataclasses import dataclass
from pathlib import Path

from omegaconf import OmegaConf

@dataclass
class File:
    enable: bool
    level:str
    path:str
    rotation:str
    retention:str

@dataclass
class Console:
    enable:bool
    level:str

@dataclass
class LoggingConfig:
    file: File
    console: Console

#数据库的配置
@dataclass
class DBConfig:
    host:str
    port:int
    user:str
    password:str
    database:str

@dataclass
class QdrantConfig:
    host:str
    port:int
    embedding_size:int

@dataclass
class EmbeddingConfig:
    host:str
    port:int
    model:str

@dataclass
class ESConfig:
    host:str
    port:int
    index_name:str

@dataclass
class TextLLMConfig:
    model_name:str
    api_key:str
    base_url:str

@dataclass
class CodeLLMConfig:
    model_name:str
    api_key:str
    base_url:str

@dataclass
class AppConfig:
    logging: LoggingConfig
    db_meta: DBConfig
    db_dw: DBConfig
    qdrant: QdrantConfig
    embedding: EmbeddingConfig
    es: ESConfig
    text_llm: TextLLMConfig
    code_llm: CodeLLMConfig

#结构合并
config_file=Path(__file__).parents[2]/'conf'/'app_config.yaml'
context=OmegaConf.load(config_file)
schema=OmegaConf.structured(AppConfig)
app_config: AppConfig = OmegaConf.to_object(OmegaConf.merge(schema,context))



if __name__ == '__main__':
    pass
    #print(app_config.qdrant.host)



















# config_file=Path(__file__).parents[2]/'conf1'/'app_config.yaml'
# content=OmegaConf.load(config_file)
# schema=OmegaConf.structured(AppConfig)
#
# app_conf :AppConfig = OmegaConf.to_object(OmegaConf.merge(content,schema))
#
# print(app_conf.age)
