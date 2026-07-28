from langchain.chat_models import init_chat_model

from app.conf.app_config import app_config

text_llm= init_chat_model(
    model=app_config.text_llm.model_name,
    api_key=app_config.text_llm.api_key,
    base_url=app_config.text_llm.base_url,
    temperature=0.4
)
code_llm= init_chat_model(
    model=app_config.code_llm.model_name,
    api_key=app_config.code_llm.api_key,
    base_url=app_config.code_llm.base_url,
    temperature=0
)

#.env自己配置版
# load_dotenv(dotenv_path=Path(__file__).parents[2]/'conf'/'.env')
#
# text_llm = init_chat_model(
#     model=os.getenv("text_llm"),
#     api_key=os.getenv("api_key"),
#     base_url=os.getenv("base_url"),
#     temperature=0.4
# )
#
# code_llm = init_chat_model(
#     model=os.getenv("code_llm"),
#     api_key=os.getenv("api_key"),
#     base_url=os.getenv("base_url"),
#     temperature=0
# )


if __name__ == '__main__':
    print(text_llm.invoke("你好"))
    print("="*100)
    print(code_llm.invoke("给我来一段sql的代码"))