from langchain_chroma import Chroma
import config_data as config


class VectorStoreService:
    def __init__(self, embedding):
        """
        :param embedding: 嵌入模型实例
        """
        self.embedding = embedding

        self.vector_store = Chroma(
            collection_name=config.collection_name,
            embedding_function=self.embedding,
            persist_directory=config.persist_directory,
        )

    def get_retriever(self, workspace_id: str = None, category_id: str = None, category: str = None):
        """返回向量检索器，支持多级过滤"""
        search_kwargs = {"k": config.retrieve_top_k}

        # Chroma 的 metadata filter 使用 $and / $or 组合多个条件
        filters = []
        if workspace_id:
            filters.append({"workspace_id": workspace_id})
        if category_id:
            filters.append({"category_id": category_id})
        elif category:  # 兼容旧版按 category 字符串过滤
            filters.append({"category": category})

        if len(filters) == 1:
            search_kwargs["filter"] = filters[0]
        elif len(filters) > 1:
            search_kwargs["filter"] = {"$and": filters}

        return self.vector_store.as_retriever(search_kwargs=search_kwargs)

    def search(self, query: str, workspace_id: str = None, category_id: str = None,
               category: str = None, top_k: int = None):
        """直接搜索，返回文档列表"""
        k = top_k or config.retrieve_top_k
        kwargs = {"k": k}

        filters = []
        if workspace_id:
            filters.append({"workspace_id": workspace_id})
        if category_id:
            filters.append({"category_id": category_id})
        elif category:
            filters.append({"category": category})

        if len(filters) == 1:
            kwargs["filter"] = filters[0]
        elif len(filters) > 1:
            kwargs["filter"] = {"$and": filters}

        return self.vector_store.similarity_search(query, **kwargs)


if __name__ == '__main__':
    import config_data as config
    service = VectorStoreService(config.get_embeddings())
    res = service.search("Python编程", workspace_id="ws_test")
    print(res)
