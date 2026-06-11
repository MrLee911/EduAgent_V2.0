# Few-Shot 示例库：QA Agent 4 个示例 + Task Agent 1 个示例 + 注入策略
# 对应文档：06 §6

from typing import Optional


# === 6.1 QA Agent Few-Shot 示例 ===

QA_FEW_SHOT_EXAMPLES = [
    {
        "trigger": "学生问概念（CONCEPT）",
        "user": "老师，Python 里的装饰器是什么？我一直搞不懂。",
        "assistant": (
            "**装饰器**是 Python 中一种特殊的函数，它可以在不修改原函数代码的情况下，给函数增加额外的功能。\n\n"
            "你可以这样理解：\n"
            "> 想象你去咖啡店点一杯美式咖啡。装饰器就像是你额外加的\"糖浆\"——咖啡本身（原函数）没变，"
            "但加了糖浆后（装饰后）味道更丰富了。\n\n"
            "来看一个最简单的例子：\n"
            "```python\n"
            "def my_decorator(func):\n"
            "    def wrapper():\n"
            '        print("函数执行前...")\n'
            "        func()\n"
            '        print("函数执行后...")\n'
            "    return wrapper\n"
            "```\n\n"
            "现在出一道题检验你是否理解了：\n"
            "> 如果有一个函数 `def greet(): print(\"Hello\")`，请写出用 `@my_decorator` 装饰它后的完整代码。\n\n"
            "📚 参考来源：课件《Python 高级特性》第 12 页"
        )
    },
    {
        "trigger": "学生问做题（PROBLEM）",
        "user": "这道题怎么做？用递归实现斐波那契数列的前 N 项。",
        "assistant": (
            "这道题考察的是**递归函数**的设计。咱们先分析一下：\n\n"
            "**知识点分析：**\n"
            "1. 斐波那契数列的定义：F(0)=0, F(1)=1, F(n)=F(n-1)+F(n-2)\n"
            "2. 递归的两个关键要素：**基准条件**（什么时候停止递归）和**递归条件**（怎么调用自己）\n\n"
            "**解题思路：**\n"
            "1. 先写基准条件：当 n=0 返回 0，n=1 返回 1\n"
            "2. 再写递归条件：返回 fib(n-1) + fib(n-2)\n"
            "3. 考虑：这个基础版本有什么问题？（提示：重复计算）\n\n"
            "我给你一个伪代码框架，你来补全：\n"
            "```\n"
            "def fibonacci(n):\n"
            "    if ___ <= 1:\n"
            "        return ___\n"
            "    return fibonacci(___) + fibonacci(___)\n"
            "```\n\n"
            "> 💡 进阶思考：这个递归方案的时间复杂度是多少？有没有更高效的实现方式？试试用记忆化搜索（memoization）优化它。\n\n"
            "📚 参考来源：课件《函数与递归》第 8 页，教材《编程基础》第 5 章"
        )
    },
    {
        "trigger": "学生比较概念（COMPARISON）",
        "user": "列表（list）和元组（tuple）有什么区别？",
        "assistant": (
            "很好的问题！列表和元组是 Python 中最常用的两种序列类型，核心区别在于**可变性**。\n\n"
            "| 维度 | 列表 (list) | 元组 (tuple) |\n"
            "|------|------------|-------------|\n"
            "| 可变性 | ✅ 可变（可增删改元素） | ❌ 不可变（创建后不能修改） |\n"
            "| 语法 | `[1, 2, 3]` | `(1, 2, 3)` |\n"
            "| 性能 | 稍慢（需预留空间） | 更快（固定大小） |\n"
            "| 使用场景 | 动态数据集合 | 固定数据、字典 key、函数多返回值 |\n"
            "| 方法数量 | 多（append, remove, sort...） | 少（count, index） |\n\n"
            "> 🧠 记忆技巧：把列表想象成\"可擦写的白板\"，元组想象成\"刻在石头上的文字\"。\n\n"
            "来做一道题检验理解：\n"
            "> 如果要存储一年 12 个月份的英文名称，用 list 还是 tuple 更合适？为什么？\n\n"
            "📚 参考来源：课件《Python 数据结构》第 5-7 页"
        )
    },
    {
        "trigger": "学生继续追问同一概念（FOLLOW_UP）",
        "user": "我还是不太明白递归的基准条件是什么意思。",
        "assistant": (
            "没关系，递归确实需要一点时间来理解。咱们换个角度：\n\n"
            "**基准条件 = 终点线**\n\n"
            "把递归想象成一个人下楼梯：每一步都\"递归\"往下走一级。"
            "基准条件就是——**到了一楼（不能再往下走了）**。如果没有一楼这个终点，人就会一直往下走，掉到地下室里去。\n\n"
            "技术上讲，基准条件就是**函数不再调用自己的那个情况**。\n\n"
            "看这个最简单的例子：\n"
            "```python\n"
            "def countdown(n):\n"
            "    if n <= 0:          # ← 这就是基准条件！n<=0 时停止\n"
            '        print("发射！")\n'
            "        return\n"
            "    print(n)\n"
            "    countdown(n - 1)    # ← 这是递归调用\n"
            "```\n"
            "当 n=0 时函数直接 return 了——这就是\"到了一楼\"，不会再调用自己。\n\n"
            "现在试着回答：如果调用 `countdown(5)`，会打印什么？\n\n"
            "📚 参考来源：教材《编程基础》第 5 章第 2 节"
        )
    },
]


# === 6.2 Task Agent Few-Shot 示例 ===

TASK_FEW_SHOT_EXAMPLES = [
    {
        "trigger": "生成 lab_guide 实验指导",
        "task_type": "lab_guide",
        "difficulty": "medium",
        "output_snippet": (
            "# 实验二：Python 函数与递归\n\n"
            "本实验预计 2.5 小时完成，请先完整阅读实验背景和目标。\n\n"
            "## 实验背景\n"
            "函数是代码复用的基本单元，递归是解决分治问题的有力工具。"
            "在本次实验中，你将实现多种函数类型和递归算法。\n\n"
            "## 实验目标\n"
            "1. 掌握函数的定义、参数传递和返回值\n"
            "2. 理解作用域和闭包概念\n"
            "3. 能用递归解决树形结构遍历问题\n\n"
            "## 实验环境要求\n"
            "- Python 3.10+\n"
            "- 编辑器：VS Code / PyCharm\n"
            "- 需要的库：无（仅用标准库）\n\n"
            "## 任务一：参数传递探索（30 分钟）\n"
            "编写函数 `modify_list(lst)` 和 `reassign_list(lst)`...\n\n"
            "## 任务二：递归目录遍历（45 分钟）\n"
            "实现 `find_files(directory, extension)`...\n\n"
            "## 任务三：汉诺塔可视化（60 分钟）\n"
            "实现汉诺塔问题的递归解法，并打印每一步...\n\n"
            "## 思考题\n"
            "1. Python 的默认递归深度是多少？如何修改？\n\n"
            "---\n"
            "## 参考答案（仅供教师审阅）\n"
            "..."
        )
    },
]


# === 6.3 注入策略 ===

def select_few_shots(agent_type: str, intent: str = "",
                     difficulty: Optional[str] = None) -> list[dict]:
    """
    根据当前场景选择合适的 Few-Shot 示例。

    选择逻辑：
    - QA Agent + CONCEPT → 概念解释示例
    - QA Agent + PROBLEM → 做题引导示例
    - QA Agent + COMPARISON → 概念对比示例
    - QA Agent + 连续追问（同一知识点第 3 轮） → FOLLOW_UP 示例
    - Task Agent + lab_guide → 实验指导格式示例

    返回的示例以 SystemMessage 形态注入到对话中，
    放在 conversation_history 之前。
    """
    selected = []

    if agent_type == "qa":
        if intent == "CONCEPT":
            selected = [e for e in QA_FEW_SHOT_EXAMPLES if "概念" in e["trigger"]]
        elif intent == "PROBLEM":
            selected = [e for e in QA_FEW_SHOT_EXAMPLES if "做题" in e["trigger"]]
        elif intent == "COMPARISON":
            selected = [e for e in QA_FEW_SHOT_EXAMPLES if "比较" in e["trigger"]]

    elif agent_type == "task":
        if difficulty == "hard" or intent == "lab_guide":
            selected = [e for e in TASK_FEW_SHOT_EXAMPLES
                       if e.get("task_type") == "lab_guide"]

    return selected[:2]  # 最多注入 2 个示例（控制 token 消耗）


def format_few_shots(shots: list[dict]) -> str:
    """格式化 Few-Shot 示例为提示词文本"""
    if not shots:
        return ""

    blocks = ["## 回答示例（参考你的风格和格式）\n"]
    for i, shot in enumerate(shots, 1):
        blocks.append(f"**示例 {i}**")
        if "user" in shot:
            blocks.append(f"学生：{shot['user']}")
        if "assistant" in shot:
            blocks.append(f"助教：{shot['assistant']}")
        if "output_snippet" in shot:
            blocks.append(f"输出片段：\n{shot['output_snippet']}")
        blocks.append("")

    return "\n".join(blocks)
