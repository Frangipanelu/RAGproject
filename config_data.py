md5_path = "./data/md5.text"
meta_db_path = "./data/knowledge_meta.json"


# Chroma
collection_name = "personal_kb"
persist_directory = "./data/chroma_db"


# 文件上传配置
ALLOWED_EXTENSIONS = ["md", "pdf", "docx", "txt", "html", "csv", "xlsx", "pptx", "json", "yaml", "yml"]

# 文本分割
chunk_size = 500                # 文本分割块大小（BGE模型最大支持512 tokens，约1500字符）
chunk_overlap = 50              # 块重叠字符数
separators = ["\n\n", "\n", "。", "！", "？", ".", "!", "?", " ", ""]
max_split_char_number = 500     # 文本分割的阈值
max_embedding_chars = 1500     # embedding 单次最大字符数（BGE限制）

# 检索
retrieve_top_k = 5                  # 检索返回匹配的文档数量


# SiliconFlow API 配置
SILICONFLOW_BASE_URL = "https://api.siliconflow.cn/v1"
SILICONFLOW_API_KEY = "sk-pxhecitcvtbgzcdqtifrknqjkdeyzfktewocsidmzesekoxy"

# 禁用代理（避免SSL握手失败）
import os
os.environ.pop("HTTP_PROXY", None)
os.environ.pop("HTTPS_PROXY", None)
os.environ.pop("http_proxy", None)
os.environ.pop("https_proxy", None)
os.environ["NO_PROXY"] = "*"
os.environ["no_proxy"] = "*"

# 模型
embedding_model_name = "BAAI/bge-large-zh-v1.5"
chat_model_name = "nex-agi/Nex-N2-Pro"


def get_embeddings():
    """统一创建 Embedding 客户端（兼容 SiliconFlow BGE 模型）"""
    from langchain_openai import OpenAIEmbeddings
    return OpenAIEmbeddings(
        model=embedding_model_name,
        openai_api_key=SILICONFLOW_API_KEY,
        openai_api_base=SILICONFLOW_BASE_URL,
        check_embedding_ctx_length=False,  # 避免LangChain把input包成二维数组
        chunk_size=1,  # 逐条发送，SiliconFlow BGE模型不支持批处理格式
    )

# 会话
session_config = {
        "configurable": {
            "session_id": "user_001",
        }
    }

# 自动分类规则（关键词 → 分类）
AUTO_CATEGORIES = {
    "技术": ["代码", "编程", "算法", "框架", "API", "数据库", "服务器", "部署", "架构", "Python", "Java", "JavaScript", "SQL", "Git", "Docker", "Linux", "前端", "后端", "开发", "技术栈"],
    "工作": ["面试", "简历", "JD", "岗位", "项目", "团队", "管理", "绩效", "OKR", "KPI", "汇报", "协作", "沟通", "领导", "职业规划"],
    "学习": ["课程", "笔记", "读书", "学习", "考试", "培训", "教程", "知识", "概念", "理论", "原理", "方法论"],
    "生活": ["健康", "运动", "饮食", "旅行", "购物", "理财", "投资", "保险", "住房", "装修", "生活"],
    "个人": ["日记", "随笔", "想法", "感悟", "反思", "总结", "计划", "目标", "习惯"],
}

# 默认分类
DEFAULT_CATEGORY = "未分类"