# 文档解析器：支持 PDF/DOCX/PPTX/MD/TXT 5 种格式
# 对应文档：S2 Pattern 1.1

from typing import List
from langchain_core.documents import Document

PARSER_MAP = {
    "pdf": "PyPDFParser",
    "docx": "DocxParser",
    "pptx": "PptxParser",
    "md": "MarkdownParser",
    "txt": "TextParser",
}


async def parse_file(file_path: str, file_type: str) -> List[Document]:
    """
    根据文件类型选择解析器，返回 LangChain Document 列表。
    每个 Document 包含 page_content + metadata {file_name, page, chapter}。

    使用 aload() 异步版本（Celery 任务中执行）。
    """
    file_type = file_type.lower().strip()
    if file_type not in PARSER_MAP:
        raise ValueError(f"不支持的文件类型: {file_type}，支持的类型: {list(PARSER_MAP.keys())}")

    if file_type == "pdf":
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(file_path)
        docs = await loader.aload()
        return _enrich_metadata(docs, file_path)

    if file_type == "docx":
        from langchain_community.document_loaders import Docx2txtLoader
        loader = Docx2txtLoader(file_path)
        docs = await loader.aload()
        return _enrich_metadata(docs, file_path)

    if file_type == "pptx":
        from langchain_community.document_loaders import UnstructuredPowerPointLoader
        loader = UnstructuredPowerPointLoader(file_path)
        docs = await loader.aload()
        return _enrich_metadata(docs, file_path)

    if file_type == "md":
        from langchain_community.document_loaders import TextLoader
        loader = TextLoader(file_path, autodetect_encoding=True)
        docs = await loader.aload()
        return _enrich_metadata(docs, file_path)

    if file_type == "txt":
        from langchain_community.document_loaders import TextLoader
        loader = TextLoader(file_path, autodetect_encoding=True)
        docs = await loader.aload()
        return _enrich_metadata(docs, file_path)

    return []


def _enrich_metadata(docs: List[Document], file_path: str) -> List[Document]:
    """为每个 Document 补充统一的 metadata 字段"""
    import os
    file_name = os.path.basename(file_path)
    for i, doc in enumerate(docs):
        doc.metadata["file_name"] = file_name
        doc.metadata["page"] = doc.metadata.get("page", i + 1)
        doc.metadata["chapter"] = doc.metadata.get("chapter", "")
    return docs
