import asyncio

from elasticsearch import AsyncElasticsearch


from app.conf.app_config import ESConfig, app_config


#es服务器类
class ESClientManager():
    def __init__(self,config:ESConfig):
        self.client:AsyncElasticsearch | None = None
        self.config:ESConfig = config

    def _get_url(self):
        return f"http://{self.config.host}:{self.config.port}/"

    def init(self):
        self.client=AsyncElasticsearch(hosts=[self._get_url()])

    async def close(self):
        await self.client.close()

es_client_manager = ESClientManager(app_config.es)

if __name__ == '__main__':
    es_client_manager.init()
    client=es_client_manager.client

    async def test():
        #写入数据
        await client.index(
            index="my_index",
            document={
                "foo": "foo",
                "bar": "bar",
            }
        )
        #查询数据
        resp=await client.search(
            index="my_index",
        )
        print(resp)
        await es_client_manager.close()
    asyncio.run(test())


















