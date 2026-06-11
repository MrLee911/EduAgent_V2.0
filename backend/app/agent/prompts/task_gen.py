# Task Agent 场景模板：主模板/追加/难度评估 3 个模板
# 对应文档：06 §4.2

# === 4.2.1 任务出题主模板 ===
# Token 预算：~600 token

TASK_GENERATION_TEMPLATE = """
## 出题要求
请根据以下课程资料，生成一份符合指定类型和难度的教学任务。

### 任务类型：{task_type}
### 难度等级：{difficulty}

### 课程资料
{knowledge_context}

### 课程统计信息
{course_stats}

### 教师额外指令
{additional_instructions}

---
请严格按照你的角色设定（System Prompt）中的格式要求，生成完整的教学任务。

## 输出前自检清单
生成完毕后，请逐条确认：
- [ ] 所有题目是否都来自参考资料（而非编造）？
- [ ] 是否每道题标注了关联的知识点来源？
- [ ] 难度是否符合 {difficulty} 的要求？
- [ ] 结构是否符合 {task_type} 的要求？
- [ ] 是否包含了"参考答案（仅供教师审阅）"部分？
- [ ] 选择题答案是否附了简要解析？
- [ ] 任务开头是否注明了题量、总分、建议时间？
"""


# === 4.2.2 任务补充生成模板（追加题目） ===
# Token 预算：~300 token

TASK_APPEND_TEMPLATE = """
当前已有任务（简要）：{existing_task_summary}

教师要求追加内容：{additional_instructions}

课程资料：{knowledge_context}

---
请基于以上信息，生成追加的题目。
- 新题目不得与已有任务中的题目重复
- 难度保持与已有任务一致
- 使用同样的格式（Markdown 层级不变）
- 追加的题目末尾标注「📎 追加题目」
"""


# === 4.2.3 难度评估模板 ===
# Token 预算：~300 token

DIFFICULTY_ASSESSMENT_TEMPLATE = """
评估以下知识点在教学中的难度等级，以及推荐的任务类型搭配。

知识点主题：{topic}
关联资源片段（前 2000 字）：{resource_snippets}
在课程中的位置：{chapter_position}

## 评估维度
1. 概念抽象程度（1-5）：1=非常直观，5=高度抽象
2. 前置知识数量：需要多少先修知识点
3. 实践复杂度（1-5）：1=纯理论记忆，5=需要大量动手
4. 常见学生困惑率：学生普遍感觉难以理解的频率

## 输出格式
返回一个 JSON 对象：
{{
  "recommended_level": "easy" | "medium" | "hard",
  "abstractness_score": 1-5,
  "prerequisite_count": 整数,
  "practice_complexity": 1-5,
  "reasoning": "一句话理由",
  "task_type_suggestions": ["适合的任务类型列表"]
}}
"""
