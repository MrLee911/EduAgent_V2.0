# 后处理器：3 种输出格式 + Token 预算控制
# 对应文档：S2 Pattern 5, 06 §2.4

# 格式参数（来自 S2 Pattern 5）
MAX_SOURCES = 10         # 最多注入 10 条，覆盖完整章节型课程资料
MAX_SOURCE_CHARS = 800   # 每条最多 800 字符
MAX_TOTAL_TOKENS = 6000  # 注入总 token 上限（中文按字符数粗略估算）


def format_knowledge_for_prompt(results: list[dict], max_docs: int = MAX_SOURCES) -> str:
    """
    将检索结果格式化为 LLM 直接阅读的文本（纯文本格式）。
    格式对齐 06 文档 §2.4。

    输入：[{content, metadata: {file_name, page, chapter}, score}, ...]
    输出：结构化的纯文本（非 JSON）
    """
    if not results:
        return "（课程知识库中暂无相关内容）"

    blocks = []
    total_chars = 0

    for i, r in enumerate(results[:max_docs], 1):
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
            "resource_id": r.get("metadata", {}).get("resource_id", ""),
            "resource_name": r.get("metadata", {}).get("file_name", ""),
            "chunk_id": r.get("chunk_id", ""),
            "chunk_index": r.get("metadata", {}).get("chunk_index", 0),
            "score": r.get("score", 0),
            "text_preview": r.get("content", "")[:100],
        }
        for r in results
    ]


def format_results_for_tool(results: list[dict]) -> list[dict]:
    """
    格式化检索结果为 Tool 返回格式（JSON 摘要）。
    格式对齐 03 文档 §5.4 sources JSONB schema。
    """
    return [
        {
            "resource_id": r.get("metadata", {}).get("resource_id", ""),
            "resource_name": r.get("metadata", {}).get("file_name", "未知文件"),
            "chunk_id": r.get("chunk_id", ""),
            "chunk_index": r.get("metadata", {}).get("chunk_index", 0),
            "score": r.get("score", 0),
            "text_preview": r.get("content", "")[:100],
        }
        for r in results
    ]
