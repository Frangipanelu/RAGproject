from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableWithMessageHistory, RunnableLambda
from core.history import get_history
from core.vector_stores import VectorStoreService
from langchain_openai import ChatOpenAI
import config_data as config
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
import time


def print_prompt(prompt):
    return prompt


class RagService:
    def __init__(self, workspace_id: str = None, category_id: str = None, category: str = None):
        """
        :param workspace_id: 工作区 ID（按工作区过滤检索）
        :param category_id: 分类 ID（按分类过滤检索）
        :param category: 兼容旧版分类字段
        """
        self.workspace_id = workspace_id
        self.category_id = category_id
        self.category = category
        # 暴露最近一次检索到的来源（用于"保存到知识库"功能）
        self.last_sources = []

        self.vector_service = VectorStoreService(embedding=config.get_embeddings())

        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system",
                 "你是一个个人知识库助手。请严格基于用户知识库中的参考资料来回答问题。\n"
                 "规则：\n"
                 "1. 优先使用参考资料中的内容回答，不要编造信息\n"
                 "2. 如果参考资料中没有相关信息，请如实告知用户\n"
                 "3. 回答时注明信息来源（文件名）\n"
                 "4. 回答要简洁、专业、有条理\n\n"
                 "参考资料：{context}\n\n"
                 "对话历史："),
                MessagesPlaceholder("history"),
                ("user", "{input}")
            ]
        )

        self.chat_model = ChatOpenAI(
            model=config.chat_model_name,
            openai_api_key=config.SILICONFLOW_API_KEY,
            openai_api_base=config.SILICONFLOW_BASE_URL,
        )
        self.chain = self.__get_chain()

    def __get_chain(self):
        """构建执行链，支持工作区/分类过滤"""
        retriever = self.vector_service.get_retriever(
            workspace_id=self.workspace_id,
            category_id=self.category_id,
            category=self.category,
        )

        def format_document(docs: list[Document]):
            # 同时把来源保存到实例属性
            try:
                self.last_sources = [
                    {
                        "filename": doc.metadata.get("source", "未知"),
                        "snippet": doc.page_content[:300] if doc.page_content else "",
                        "workspace_id": doc.metadata.get("workspace_id", ""),
                        "category_id": doc.metadata.get("category_id", ""),
                        "category_path": doc.metadata.get("category_path", ""),
                    }
                    for doc in docs
                ]
            except Exception:
                self.last_sources = []

            if not docs:
                return "知识库中暂无相关参考资料"
            formatted_str = ""
            for doc in docs:
                source = doc.metadata.get("source", "未知")
                cat_path = doc.metadata.get("category_path", "")
                if cat_path:
                    formatted_str += f"【来源：{cat_path}/{source}】\n{doc.page_content}\n\n"
                else:
                    formatted_str += f"【来源：{source}】\n{doc.page_content}\n\n"
            return formatted_str

        def format_for_retriever(value: dict) -> str:
            return value["input"]

        def format_for_prompt_template(value):
            new_value = {}
            new_value["input"] = value["input"]["input"]
            new_value["context"] = value["context"]
            new_value["history"] = value["input"]["history"]
            return new_value

        def retry_on_error(func, max_retries=3, delay=2):
            def wrapper(*args, **kwargs):
                retries = 0
                while retries < max_retries:
                    try:
                        return func(*args, **kwargs)
                    except Exception as e:
                        retries += 1
                        if retries >= max_retries:
                            raise
                        time.sleep(delay)
                return None
            return wrapper

        def retrieve_with_retry(query):
            retry_func = retry_on_error(retriever.invoke)
            return retry_func(query)

        chain = (
            {
                "input": RunnablePassthrough(),
                "context": RunnableLambda(format_for_retriever)
                           | RunnableLambda(retrieve_with_retry)
                           | format_document
            }
            | RunnableLambda(format_for_prompt_template)
            | self.prompt_template
            | print_prompt
            | self.chat_model
            | StrOutputParser()
        )

        conversation_chain = RunnableWithMessageHistory(
            chain,
            get_history,
            input_messages_key="input",
            history_messages_key="history",
        )

        return conversation_chain


if __name__ == '__main__':
    session_config = {
        "configurable": {
            "session_id": "user_001",
        }
    }

    # 不限制
    res = RagService().chain.invoke({"input": "Python如何入门？"}, session_config)
    print(res)

    # 限定工作区
    res2 = RagService(workspace_id="ws_xxx").chain.invoke({"input": "Python如何入门？"}, session_config)
    print(res2)
