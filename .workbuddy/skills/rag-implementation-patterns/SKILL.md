---
name: rag-implementation-patterns
description: >
  RAG（检索增强生成）管道实施模式 —— 当 CodeBuddy 开始编写文档处理、向量检索、
  重排序、上下文注入或知识库相关代码时触发。覆盖：Document Chunking 策略与参数配置、
  Embedding 模型选型（BGE-M3）与 ChromaDB Collection 配置、MMR 检索与 Rerank 管道、
  Query Rewrite（LLM 改写查询）、Post-Processing 与 Sources 格式化、ChromaDB ↔ PostgreSQL
  双库同步（chunks 表桥梁模式）、三级降级策略实现、本项目 5 个关键约束。
agent_created: true
---

# RAG Implementation Patterns

## Purpose

本 Skill 提供教学智能体项目（EduAgent）中 RAG（检索增强生成）管道的专家级实施模式。
当 CodeBuddy 需要编写涉及文档分块、Embedding 向量化、ChromaDB 检索、重排序（Rerank）、
查询改写或上下文压缩的代码时，应使用本 Skill 中的模式和参数。

## When to Use

在以下场景中触发本 Skill：

- CodeBuddy 开始编写文档上传/处理相关代码（文件解析 → Chunking → Embedding → 入库）
- CodeBuddy 需要实现 RAG 检索功能（向量检索、MMR、相似度过滤）
- CodeBuddy 需要实现 Query Rewrite（用 LLM 改写查询语句以提升检索精度）
- CodeBuddy 需要实现 Rerank（重排序）逻辑
- CodeBuddy 需要设计后处理（上下文压缩、来源引用格式化、去重合并）
- CodeBuddy 需要实现三层降级策略（LLM 不可用 → RAG Only → 服务不可用）
- CodeBuddy 需要处理 ChromaDB 和 PostgreSQL 的数据同步

---

## Core Patterns

### Pattern 1: Document Processing Pipeline（文档处理全流程）

文档上传后必须经过一个完整的异步处理管道，不可跳过任何环节：

```
文件上传 (MinIO)
    ↓
[1] 文件类型检测 → 选择 Parser
    ↓
[2] 文本提取 (PyPDF2 / python-docx / python-pptx / markdown)
    ↓
[3] Document Chunking (RecursiveCharacterTextSplitter)
    ↓
[4] Embedding 向量化 (BGE-M3)
    ↓
[5] ChromaDB 写入 (逐条，带 metadata)
    ↓
[6] PostgreSQL chunks 表写入 (逐条，chroma_id 关联)
    ↓
[7] resources 表更新 status='ready', chunk_count=N
```

#### 1.1 File Parser Selection

```python
# backend/app/rag/parsers.py

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
    每个 Document 包含 page_content + metadata {file_name, page, chapter}
    """
    parser_cls = PARSER_MAP.get(file_type)
    if not parser_cls:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    # 实现示例：
    if file_type == "pdf":
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(file_path)
        return await loader.aload()  # aload() → List[Document]
    
    if file_type == "docx":
        from langchain_community.document_loaders import Docx2txtLoader
        loader = Docx2txtLoader(file_path)
        return await loader.aload()
    
    # ... 其他类型
```

**关键决策**：
- 用 `aload()` 而不是 `load()`——文档解析在 Celery 异步任务中执行，必须用异步版本
- 每个 Document 必须携带 `metadata`：`file_name`（用于 source 引用）、`page`（用于溯源）、`chapter`（从目录提取，可选）

#### 1.2 Document Chunking（分块策略）

**本项目强制参数**（来自 05 §3.2 和 03 §5.3）：

```python
# backend/app/rag/chunker.py

from langchain.text_splitter import RecursiveCharacterTextSplitter

CHUNK_CONFIG = {
    "chunk_size": 512,       # token
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

async def chunk_documents(documents: List[Document]) -> List[dict]:
    """
    将 Document 列表切分为 chunk。
    返回：[{content, metadata, chunk_index, token_count}, ...]
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_CONFIG["chunk_size"],
        chunk_overlap=CHUNK_CONFIG["chunk_overlap"],
        separators=CHUNK_CONFIG["separators"],
        length_function=len,  # 用字符数（中文约 1 char ≈ 1 token）
    )
    
    chunks = []
    for doc in documents:
        texts = splitter.split_text(doc.page_content)
        for i, text in enumerate(texts):
            chunks.append({
                "content": text,
                "file_name": doc.metadata.get("file_name", ""),
                "page": doc.metadata.get("page"),
                "chunk_index": i,
                "token_count": len(text),  # 粗略估算，后续用 tiktoken 精确计算
            })
    return chunks
```

**为什么 chunk_size=512？**
- BGE-M3 Embedding 模型最佳输入长度 512 token，超过会被截断，语义信息丢失
- 中文场景：1 个中文字符 ≈ 1 token，512 token ≈ 一段中等长度的段落

**为什么不设置更大？**
- 512 是 BGE-M3 的 `max_seq_length`，再大会被截断（无声信息丢失）
- 如果需要更长的上下文，用 **Chunk + 父文档引用** 模式（见 Pattern 6 扩展）

#### 1.3 ChromaDB Collection 配置

```python
# backend/app/rag/vector_store.py

import chromadb
from chromadb.config import Settings

# ⚠️ 重要：每个课程一个 Collection，实现课程级知识隔离
COLLECTION_PREFIX = "course_"

def get_collection_name(course_id: str) -> str:
    """课程 ID → Collection 名称映射"""
    return f"{COLLECTION_PREFIX}{course_id.replace('-', '_')}"

async def get_or_create_collection(course_id: str):
    """获取或创建课程的 ChromaDB Collection"""
    client = chromadb.HttpClient(
        host="chromadb",  # Docker 服务名
        port=8001,
        settings=Settings(anonymized_telemetry=False),
    )
    
    collection_name = get_collection_name(course_id)
    
    # 尝试获取已有 collection，不存在则创建
    try:
        collection = client.get_collection(
            name=collection_name,
            embedding_function=None,  # 手动传 embedding
        )
    except Exception:
        collection = client.create_collection(
            name=collection_name,
            metadata={
                "hnsw:space": "cosine",  # ⚠️ 必须：BGE-M3 已归一化，余弦=点积
                "course_id": course_id,
            },
        )
    return collection
```

**必须注意**：
- `hnsw:space: "cosine"` —— BGE-M3 输出已 L2 归一化，必须用余弦距离
- 每个课程独立 Collection —— 防止课程间知识污染
- embedding 手动传入（不在 ChromaDB 侧调 embedding 函数），更灵活可控

#### 1.4 Embedding + ChromaDB 写入（含 PostgreSQL 同步）

```python
# backend/app/rag/indexer.py

import uuid
from langchain_huggingface import HuggingFaceEmbeddings

async def index_chunks(
    course_id: str,
    resource_id: str,
    chunks: List[dict],
    db_session,  # SQLAlchemy async session
):
    """
    将 chunks 向量化并写入 ChromaDB + PostgreSQL。
    这是 Step 4-6 的合并实现。
    """
    # === Step 4: Embedding ===
    embedding_model = HuggingFaceEmbeddings(
        model_name="BAAI/bge-m3",
        model_kwargs={"device": "cpu"},  # 生产环境用 cuda
        encode_kwargs={"normalize_embeddings": True},
    )
    
    texts = [chunk["content"] for chunk in chunks]
    embeddings = await embedding_model.aembed_documents(texts)
    
    # === Step 5: ChromaDB 写入 ===
    collection = await get_or_create_collection(course_id)
    
    chroma_ids = [str(uuid.uuid4()) for _ in chunks]
    metadatas = [
        {
            "resource_id": resource_id,
            "course_id": course_id,
            "file_name": chunk["file_name"],
            "page": chunk.get("page", 0),
            "chunk_index": chunk["chunk_index"],
        }
        for chunk in chunks
    ]
    
    collection.add(
        ids=chroma_ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )
    
    # === Step 6: PostgreSQL chunks 表同步写入 ===
    from ..models.chunk import Chunk  # SQLAlchemy model
    
    for i, chunk in enumerate(chunks):
        db_chunk = Chunk(
            resource_id=resource_id,
            course_id=course_id,
            chunk_index=chunk["chunk_index"],
            content=chunk["content"],
            token_count=chunk["token_count"],
            chroma_id=chroma_ids[i],
        )
        db_session.add(db_chunk)
    
    await db_session.flush()  # 生成 ID 但不提交（事务由外层控制）
```

**ChromaDB ↔ PostgreSQL 桥梁模式**：
- `chunks.chroma_id` 是连接两库的唯一键
- 删除资源时：先查 PostgreSQL 获取 `chroma_id` 列表 → 在 ChromaDB 中删除 → 再删 PostgreSQL 记录
- 知识库重建时：以 PostgreSQL 为 source of truth，按 `chunks.content` 重新 embedding 写 ChromaDB

---

### Pattern 2: RAG Retrieval Pipeline（检索管道）

#### 2.1 Retriever 核心实现

```python
# backend/app/rag/retriever.py

import json
from typing import Optional

class Retriever:
    """课程知识库检索器 —— 被 search_knowledge 工具调用"""
    
    def __init__(self, course_id: str):
        self.course_id = course_id
        self.collection = None  # 延迟初始化
        self.embedding_model = None
    
    async def _ensure_initialized(self):
        if self.collection is None:
            self.collection = await get_or_create_collection(self.course_id)
        if self.embedding_model is None:
            self.embedding_model = HuggingFaceEmbeddings(
                model_name="BAAI/bge-m3",
                model_kwargs={"device": "cpu"},
                encode_kwargs={"normalize_embeddings": True},
            )
    
    async def search(
        self,
        query: str,
        top_k: int = 5,
        resource_type: Optional[str] = None,
        similarity_threshold: float = 0.6,
    ) -> list[dict]:
        """
        语义检索课程知识库。
        
        Returns:
            [{content, metadata: {file_name, page, chapter, resource_id}, score, chunk_id}, ...]
        """
        await self._ensure_initialized()
        
        # 1. Embedding
        query_embedding = await self.embedding_model.aembed_query(query)
        
        # 2. 构建 metadata filter（可选）
        where_filter = None
        if resource_type:
            where_filter = {"resource_type": resource_type}
        
        # 3. ChromaDB 检索（MMR 模式）
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k * 4,  # 先多取 4 倍候选，给 MMR 足够空间
            where=where_filter,
            include=["documents", "metadatas", "distances"],
        )
        
        # 4. MMR 重排序（用 langchain 实现或手动）
        ranked = self._mmr_rerank(
            query_embedding=query_embedding,
            candidates=results,
            lambda_mult=0.7,  # 70% 相关性 + 30% 多样性
            top_k=top_k,
        )
        
        # 5. 相似度阈值过滤
        filtered = [r for r in ranked if r["score"] >= similarity_threshold]
        
        return filtered
    
    def _mmr_rerank(
        self, query_embedding, candidates, lambda_mult=0.7, top_k=5
    ) -> list[dict]:
        """
        Maximal Marginal Relevance 重排序。
        
        MMR 公式：λ * sim(d, Q) - (1-λ) * max_{已选} sim(d, d')
        """
        import numpy as np
        
        docs = candidates["documents"][0] or []
        metas = candidates["metadatas"][0] or []
        embeddings = candidates.get("embeddings")
        
        if not docs:
            return []
        
        # 距离转相似度：cosine distance → similarity = 1 - distance
        distances = candidates["distances"][0] or []
        similarities = [1 - d for d in distances]
        
        # Simple MMR
        selected = []
        remaining = list(range(len(docs)))
        
        for _ in range(min(top_k, len(docs))):
            mmr_scores = []
            for i in remaining:
                relevance = similarities[i]
                redundancy = 0
                if selected:
                    # 已选项的最大相似度
                    redundancy = max(
                        self._cosine_sim(
                            embeddings[selected[j]] if embeddings else None,
                            embeddings[i] if embeddings else None,
                        )
                        for j in range(len(selected))
                    )
                mmr = lambda_mult * relevance - (1 - lambda_mult) * redundancy
                mmr_scores.append((i, mmr))
            
            # 选最高 MMR
            best_idx, best_score = max(mmr_scores, key=lambda x: x[1])
            selected.append(best_idx)
            remaining.remove(best_idx)
        
        # 组装结果
        results = []
        for idx in selected:
            results.append({
                "content": docs[idx],
                "metadata": metas[idx],
                "score": round(similarities[idx], 4),
                "chunk_id": candidates["ids"][0][idx],
            })
        
        return results
    
    def _cosine_sim(self, emb1, emb2):
        """余弦相似度（嵌入已归一化时 = 点积）"""
        if emb1 is None or emb2 is None:
            return 0
        import numpy as np
        return float(np.dot(emb1, emb2))
    
    def format_results(self, results: list[dict]) -> str:
        """
        格式化检索结果为 JSON 字符串（供 Agent Tool 返回）。
        格式对齐 03 文档 §4.6 sources JSONB schema。
        """
        formatted = []
        for r in results:
            meta = r["metadata"]
            formatted.append({
                "resource_id": meta.get("resource_id", ""),
                "resource_name": meta.get("file_name", "未知文件"),
                "chunk_id": r["chunk_id"],
                "chunk_index": meta.get("chunk_index", 0),
                "score": r["score"],
                "text_preview": r["content"][:100],  # Tool 返回仅摘要
            })
        return json.dumps(formatted, ensure_ascii=False)
```

**关键参数速查**：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `top_k` | 5 | 最终返回给 LLM 的文档数（经 MMR + threshold 过滤后） |
| `fetch_k` | `top_k * 4` | 初始检索候选数（给 MMR 足够选择空间） |
| `lambda_mult` | 0.7 | MMR 多样性权重（0.7 = 70% 相关性 + 30% 多样性） |
| `similarity_threshold` | 0.6 | 相似度阈值（低于此值的直接丢弃） |

---

### Pattern 3: Query Rewrite（查询改写）

**用途**：学生口语化问题 → 适合向量检索的精炼查询语句。

```python
# backend/app/rag/query_rewriter.py

QUERY_REWRITE_PROMPT = """
将以下学生提出的口语化问题，改写为用于知识库检索的精炼查询语句。

要求：
1. 去除口语化表达（"那个""就是""怎么说呢"等）
2. 提取核心概念和关键词
3. 长度控制在 30 字以内
4. 如果问题本身已经很精炼，直接返回原问题
5. 只返回改写后的查询文本，不要加任何解释

学生问题：{question}
"""

async def rewrite_query(question: str, llm) -> str:
    """
    用 LLM 改写查询。
    
    此函数在 LangGraph 的 rewrite_query 节点中调用。
    使用轻量模型降低成本（如 gpt-4o-mini / DeepSeek-V3）。
    """
    from langchain_core.messages import SystemMessage, HumanMessage
    
    messages = [
        SystemMessage(content="你是一个查询改写助手。只返回改写后的查询文本。"),
        HumanMessage(content=QUERY_REWRITE_PROMPT.format(question=question)),
    ]
    
    response = await llm.ainvoke(messages)
    rewritten = response.content.strip()
    
    # 安全检查：改写结果不能是空的
    if not rewritten or len(rewritten) < 2:
        return question  # fallback 到原问题
    
    return rewritten
```

**重要约定**（来自 06 §4.1.1）：
- 改写用轻量模型（不用主模型），节省成本
- 改写结果 ≤ 30 字——过长反而降低检索精度
- 如果改写失败或结果为空，fallback 到原问题

---

### Pattern 4: Rerank with BGE-Reranker（重排序增强）

MMR 已经做了一轮重排，但如果检索结果较多（≥ 8 条），建议追加 BGE-Reranker 精排：

```python
# backend/app/rag/reranker.py

from typing import List

# ⚠️ 仅在候选结果 ≥ 8 条时启用 Reranker（避免不必要的开销）
RERANK_THRESHOLD = 8

async def rerank_with_bge(
    query: str,
    documents: List[dict],
    top_n: int = 3,
) -> List[dict]:
    """
    用 BGE-Reranker-v2-m3 对检索结果精排。
    
    仅当候选数 ≥ RERANK_THRESHOLD 时调用。
    """
    if len(documents) < RERANK_THRESHOLD:
        # 候选少，MMR 已足够好，跳过 Reranker
        return documents[:top_n]
    
    from FlagEmbedding import FlagReranker
    
    reranker = FlagReranker(
        "BAAI/bge-reranker-v2-m3",
        use_fp16=True,  # 省显存
    )
    
    pairs = [[query, doc["content"]] for doc in documents]
    scores = reranker.compute_score(pairs, normalize=True)
    
    # 按分数排序
    scored = list(zip(documents, scores))
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return [doc for doc, _ in scored[:top_n]]
```

**为什么不每次都用 Reranker？**
- BGE-Reranker 加载模型耗时 ~2s（首次），推理每次 ~200ms
- 候选数 < 8 时，MMR 的精度损失可忽略，不值得额外开销
- 生产环境建议将 Reranker 作为独立微服务（降低加载开销）

---

### Pattern 5: Post-Processing & Context Injection（后处理与上下文注入）

检索结果注入 LLM 之前，必须格式化为统一格式。此格式对齐 06 §2.4 的 `format_knowledge_for_prompt()`：

```python
# backend/app/rag/post_processor.py

MAX_SOURCES = 5          # 最多注入 5 条
MAX_SOURCE_CHARS = 1000  # 每条最多 1000 字符
MAX_TOTAL_TOKENS = 3000  # 注入总 token 上限

def format_knowledge_for_prompt(results: list[dict]) -> str:
    """
    将检索结果格式化为 LLM 可直接阅读的文本。
    格式对齐 06 文档 §2.4。
    
    输入：[{content, metadata: {file_name, page, chapter}, score}, ...]
    输出：结构化的纯文本（非 JSON）
    """
    if not results:
        return "（知识库中未找到相关内容）"
    
    blocks = []
    total_chars = 0
    
    for i, r in enumerate(results[:MAX_SOURCES], 1):
        meta = r.get("metadata", {})
        
        # 构建来源头
        header_parts = [f"【参考资料 {i}】"]
        header_parts.append(f"来源：{meta.get('file_name', '未知文件')}")
        if meta.get("page"):
            header_parts.append(f"第{meta.get('page')}页")
        if meta.get("chapter"):
            header_parts.append(meta.get("chapter"))
        header_parts.append(f"| 相关度：{r.get('score', 0):.2f}")
        
        header = " ".join(header_parts)
        
        # 截断内容
        content = r.get("content", "")
        if len(content) > MAX_SOURCE_CHARS:
            content = content[:MAX_SOURCE_CHARS] + "..."
        
        blocks.append(f"{header}\n{content}")
        total_chars += len(content)
        
        # Token 预算检查
        if total_chars > MAX_TOTAL_TOKENS:
            blocks.append("（后续参考资料因长度限制已截断）")
            break
    
    return "\n\n---\n\n".join(blocks)


def format_sources_for_db(results: list[dict]) -> list[dict]:
    """
    格式化 sources 为 qa_records.sources JSONB 格式。
    格式对齐 03 文档 §4.6。
    """
    return [
        {
            "resource_id": r["metadata"].get("resource_id", ""),
            "resource_name": r["metadata"].get("file_name", ""),
            "chunk_id": r["chunk_id"],
            "chunk_index": r["metadata"].get("chunk_index", 0),
            "score": r["score"],
            "text_preview": r["content"][:100],
        }
        for r in results
    ]
```

---

### Pattern 6: Three-Tier Degradation Strategy（三级降级）

来自 05 §9.1，这是 RAG 管道鲁棒性的核心保障：

```python
# backend/app/rag/degradation.py

from enum import Enum

class DegradationLevel(Enum):
    FULL = 1        # RAG + LLM 完整功能
    RAG_ONLY = 2    # 仅 RAG（LLM 不可用时返回原文片段）
    UNAVAILABLE = 3 # 服务不可用

async def execute_with_degradation(
    query: str,
    course_id: str,
    llm,  # LLM 实例
) -> dict:
    """
    带降级的 RAG 执行。
    
    返回：{
        "answer": str,
        "sources": list[dict],
        "level": DegradationLevel,
        "warning": Optional[str],
    }
    """
    try:
        # === Layer 1: 完整 RAG + LLM ===
        results = await retriever.search(query, top_k=5)
        
        if not results:
            # RAG 检索无结果（score < 0.6），但仍可用 LLM
            context = "（知识库中未找到直接相关内容）"
            warning = "以下回答基于模型知识，未在课程资料中找到直接对应内容。"
        else:
            context = format_knowledge_for_prompt(results)
            warning = None
        
        try:
            answer = await llm.ainvoke_with_context(query, context)
            return {
                "answer": answer,
                "sources": format_sources_for_db(results) if results else [],
                "level": DegradationLevel.FULL,
                "warning": warning,
            }
        except (TimeoutError, ConnectionError):
            # LLM 不可用 → 降级到 Layer 2
            pass
    
    except Exception as e:
        # ChromaDB 或 Embedding 不可用 → 直接跳到 Layer 3
        if _is_vector_db_error(e):
            return _layer3_response()
        raise
    
    # === Layer 2: 仅 RAG（LLM 不可用） ===
    try:
        results = await retriever.search(query, top_k=5)
        if results:
            return {
                "answer": _format_rag_only_response(results),
                "sources": format_sources_for_db(results),
                "level": DegradationLevel.RAG_ONLY,
                "warning": "AI 服务暂时降级，以下为知识库直接检索结果。",
            }
    except Exception:
        pass
    
    # === Layer 3: 服务不可用 ===
    return _layer3_response()


def _format_rag_only_response(results: list[dict]) -> str:
    """Layer 2 降级：仅返回检索到的原文片段"""
    blocks = ["⚠️ AI 服务暂时不可用，以下是知识库中相关度最高的内容：\n"]
    for i, r in enumerate(results[:3], 1):
        meta = r["metadata"]
        blocks.append(f"**{i}.** [{meta.get('file_name', '')}] {r['content'][:500]}")
    return "\n\n".join(blocks)


def _layer3_response() -> dict:
    """Layer 3：完全不可用"""
    return {
        "answer": "智能体服务暂时不可用，请稍后重试。",
        "sources": [],
        "level": DegradationLevel.UNAVAILABLE,
        "warning": "知识库和 AI 服务均不可用。",
    }


def _is_vector_db_error(e: Exception) -> bool:
    """判断是否为 ChromaDB 错误"""
    error_str = str(e).lower()
    return any(kw in error_str for kw in [
        "chromadb", "chroma", "connection refused",
        "could not connect", "timeout",
    ])
```

---

## Project-Specific Constraints（本项目特殊约束）

以下约束来自各设计文档，实施时必须严格遵守：

### 约束 1：工具优先原则（05 §1.3）

```
Agent 处理用户请求时，必须：
1. 先调用 search_knowledge 检索知识库（RAG）
2. 再调用 LLM 生成回答
3. 禁止凭空编造课程相关知识
```

在代码中体现为：LangGraph 工作流中 `rag_search` 节点必须排在 `llm_answer` 节点之前。

### 约束 2：课程级知识隔离（05 §5.2）

- 每个课程独立的 ChromaDB Collection：`course_{course_id}`
- RAG 检索时，必须传入 `course_id`，通过 `metadata.course_id` 过滤
- 切换课程时，清空对话记忆（Redis key: `conversation:{course_id}:{user_id}`）

### 约束 3：chunks 表桥梁模式（03 §4.5）

`chunks` 表是 PostgreSQL 与 ChromaDB 之间的唯一桥梁：
- `chunks.chroma_id` 是连接键
- 删除资源流程：查 chunks → 取 chroma_ids → 删 ChromaDB → 删 chunks → 删 resources
- 知识库重建：以 chunks 表为 source of truth

### 约束 4：检索结果阈值（05 §3.2）

- `similarity_threshold = 0.6`：低于此值的检索结果丢弃
- 如果所有结果 score < 0.6，LLM 必须在回答开头告知"未在课程资料中找到直接对应内容"

### 约束 5：并发检索去重（05 §7.2）

对比类问题会发起多次并发检索（如"比较概念 A 和 B"），必须：
1. 按 `chunk_id` 去重
2. 去重后按 score 降序排列
3. 最多保留 5 条

---

## RAG 相关文件映射

CodeBuddy 应按以下目录结构生成 RAG 相关代码：

```
backend/app/rag/
├── __init__.py          # 导出核心接口
├── parsers.py           # 文件解析器（Pattern 1.1）
├── chunker.py           # 文档分块（Pattern 1.2）
├── vector_store.py      # ChromaDB 连接管理（Pattern 1.3）
├── indexer.py           # Embedding + 双库写入（Pattern 1.4）
├── retriever.py         # 检索器（Pattern 2.1）
├── query_rewriter.py    # 查询改写（Pattern 3）
├── reranker.py          # 重排序（Pattern 4）
├── post_processor.py    # 后处理与格式化（Pattern 5）
└── degradation.py       # 三级降级（Pattern 6）
```

---

## Anti-Patterns（What NOT to Do）

### ❌ Anti-Pattern 1：Chunk Size 过大

```python
# 错误：chunk_size=2048 超出 BGE-M3 的 max_seq_length=512
splitter = RecursiveCharacterTextSplitter(chunk_size=2048)
# 后果：BGE-M3 静默截断到 512 token，后 1536 token 的信息彻底丢失
```

✅ **正确**：`chunk_size=512`

---

### ❌ Anti-Pattern 2：用 ILIKE 做语义检索

```python
# 错误：用 SQL ILIKE 做关键词匹配
cursor.execute("SELECT * FROM chunks WHERE content ILIKE '%牛顿定律%'")
# 后果：只能匹配关键词，无法理解"惯性原理"就是"牛顿第一定律"
```

✅ **正确**：用 ChromaDB 做语义检索，`ILIKE` 只能用于管理后台的简单搜索

---

### ❌ Anti-Pattern 3：忘记写 PostgreSQL chunks 表

```python
# 错误：只写 ChromaDB，忘了写 PostgreSQL
collection.add(ids=ids, embeddings=embs, documents=docs, metadatas=metas)
# 缺少：db_session.add(Chunk(...))
# 后果：无法追踪向量来源，删除资源时无法清理 ChromaDB
```

✅ **正确**：每次 ChromaDB 写入后，同步写 PostgreSQL chunks 表（见 Pattern 1.4）

---

### ❌ Anti-Pattern 4：所有课程共用一个 Collection

```python
# 错误：全部课程的数据存在一个 collection 里
collection = client.get_or_create_collection("all_courses")
# 后果：课程 A 的问题检索到课程 B 的内容，知识污染
```

✅ **正确**：`collection_name = f"course_{course_id}"`（见 Pattern 1.3）

---

### ❌ Anti-Pattern 5：Rerank 每次都执行

```python
# 错误：不管候选数多少都调 Reranker
results = await rerank_with_bge(query, candidates, top_n=3)
# 后果：候选数 3 条时也加载 Reranker 模型（2s 开销），收益为 0
```

✅ **正确**：候选数 < 8 时跳过 Reranker（见 Pattern 4 的 `RERANK_THRESHOLD`）

---

### ❌ Anti-Pattern 6：忘记降级策略

```python
# 错误：LLM 挂了直接 raise，前端白屏
answer = await llm.ainvoke(messages)  # 没有 try-except
```

✅ **正确**：实现三层降级（见 Pattern 6），确保任何情况下都有可用的响应

---

### ❌ Anti-Pattern 7：sources 格式不一致

```python
# 错误：Tool 返回、LLM Prompt、DB 存储三种不同的 sources 格式
# 后果：前端展示不一致，引用来源对不上
```

✅ **正确**：
- Tool 返回：`format_results()` — JSON 字符串，仅摘要
- LLM Prompt：`format_knowledge_for_prompt()` — 纯文本
- DB 存储：`format_sources_for_db()` — JSONB array，对齐 03 §4.6 schema

---

## Quick Reference（速查表）

| 你需要做什么 | 看哪个 Pattern | 对应文件 |
|------------|:------------:|---------|
| 文档上传 → 知识入库 | Pattern 1 | `indexer.py` + `chunker.py` + `parsers.py` |
| 实现检索功能 | Pattern 2 | `retriever.py` |
| 优化学生口语化查询 | Pattern 3 | `query_rewriter.py` |
| 提升检索精度 | Pattern 4 | `reranker.py` |
| 格式化检索结果给 LLM | Pattern 5 | `post_processor.py` |
| 处理服务异常 | Pattern 6 | `degradation.py` |
| ChromaDB 初始化 | Pattern 1.3 | `vector_store.py` |
| 删除资源时清理向量 | 约束 3 | 见约束详情 |

---

## 关联文档

- `docs/05_AI智能体行为定义.md` §3：工具定义（search_knowledge）
- `docs/05_AI智能体行为定义.md` §4.2：QA 工作流（RAG 节点位置）
- `docs/05_AI智能体行为定义.md` §9：三层降级策略
- `docs/06_提示词模板.md` §2.4：知识库上下文格式化
- `docs/06_提示词模板.md` §4.1.1-4.1.4：QA 场景模板（含 RAG 注入）
- `docs/03_数据模型与数据库设计.md` §4.5：chunks 表定义
- `docs/03_数据模型与数据库设计.md` §5：ChromaDB Collection 设计
- `docs/02_技术架构文档.md` §2：ChromaDB 服务配置
