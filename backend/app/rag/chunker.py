# 文档分块器：RecursiveCharacterTextSplitter + 中文分隔符优先
# 对应文档：S2 Pattern 1.2

from typing import List
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# 强制参数（来自 05 §3.2 和 03 §5.3）
CHUNK_CONFIG = {
    "chunk_size": 512,       # token（BGE-M3 max_seq_length=512）
    "chunk_overlap": 64,     # token（12.5% overlap）
    "separators": [
        "\n\n",   # 段落边界
        "\n",     # 行边界
        "。",     # 中文句号
        "！",     # 中文感叹号
        "？",     # 中文问号
        "；",     # 中文分号
        "，",     # 中文逗号
        " ",      # 英文空格
        "",        # 字符级（最后的 fallback）
    ],
}

# 全局 chunker 实例（避免重复创建）
_splitter = None


def _get_splitter() -> RecursiveCharacterTextSplitter:
    """获取/创建分块器实例（单例）"""
    global _splitter
    if _splitter is None:
        _splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_CONFIG["chunk_size"],
            chunk_overlap=CHUNK_CONFIG["chunk_overlap"],
            separators=CHUNK_CONFIG["separators"],
            length_function=len,  # 用字符数（中文约 1 char ≈ 1 token）
        )
    return _splitter


async def chunk_documents(documents: List[Document]) -> List[dict]:
    """
    将 Document 列表切分为 chunk。

    返回：[{content, file_name, page, chunk_index, token_count}, ...]
    """
    splitter = _get_splitter()
    chunks = []

    for doc in documents:
        texts = splitter.split_text(doc.page_content)
        file_name = doc.metadata.get("file_name", "")
        page = doc.metadata.get("page")
        chapter = doc.metadata.get("chapter", "")

        for i, text in enumerate(texts):
            chunks.append({
                "content": text,
                "file_name": file_name,
                "page": page,
                "chapter": chapter,
                "chunk_index": i,
                "token_count": len(text),  # 粗略估算
            })

    return chunks
