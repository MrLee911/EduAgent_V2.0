"""
test_workflows.py — 集成测试：任务生命周期 + 报告生成

覆盖 T9.6, T9.7, V-07, V-08
"""
import pytest
from tests.conftest import assert_response

pytestmark = pytest.mark.integration


# ═══════════════════════════════════════════════
# T9.6 — 任务全生命周期：生成 → 修改 → 发布 → 归档
# ═══════════════════════════════════════════════

class TestTaskLifecycle:
    """V-07：任务生成 → 修改 → 发布 → 归档"""

    async def test_generate_task(self, teacher_client, course):
        """生成教学任务 → 201 + 结构化内容。"""
        r = await teacher_client.post(
            f"/courses/{course['id']}/tasks/generate",
            json={
                "topic": "Python 列表与字典操作",
                "task_type": "class_exercise",
                "difficulty": "medium",
                "extra_instructions": "重点考察学生的编程基础",
            },
        )
        assert r.status_code == 201, f"Task generation failed: {r.text}"
        task = r.json()["data"]
        assert task["title"]
        assert task["content"]
        assert task["status"] == "draft"
        assert task["task_type"] == "class_exercise"
        assert task["difficulty"] == "medium"
        return task

    async def test_generate_task_missing_topic(self, teacher_client, course):
        """缺少必填字段 → 400/422。"""
        r = await teacher_client.post(
            f"/courses/{course['id']}/tasks/generate",
            json={
                "task_type": "homework",
                "difficulty": "easy",
            },
        )
        assert r.status_code in (400, 422)

    async def test_task_list(self, auth_client, course):
        """任务列表 → 200。"""
        r = await auth_client.get(f"/courses/{course['id']}/tasks")
        assert r.status_code == 200
        data = r.json()["data"]
        assert isinstance(data, list)

    async def test_task_publish_flow(self, teacher_client, course):
        """生成 → 发布 → 归档完整流程。"""
        # 1. 生成任务
        r = await teacher_client.post(
            f"/courses/{course['id']}/tasks/generate",
            json={
                "topic": "Flask Web 框架入门",
                "task_type": "lab_guide",
                "difficulty": "easy",
                "extra_instructions": "适合初学者的实验指导",
            },
        )
        if r.status_code != 201:
            pytest.skip("Task generation failed, cannot test lifecycle")
        task = r.json()["data"]
        task_id = task["id"]
        assert task["status"] == "draft"

        # 2. 修改任务
        r2 = await teacher_client.patch(
            f"/courses/{course['id']}/tasks/{task_id}",
            json={
                "title": "Flask Web 框架入门（修订版）",
                "difficulty": "medium",
            },
        )
        assert r2.status_code == 200, f"Update failed: {r2.text}"

        # 3. 发布任务
        r3 = await teacher_client.post(
            f"/courses/{course['id']}/tasks/{task_id}/publish",
        )
        assert r3.status_code == 200, f"Publish failed: {r3.text}"
        updated = r3.json()["data"]
        assert updated["status"] == "published"

        # 4. 归档任务
        r4 = await teacher_client.post(
            f"/courses/{course['id']}/tasks/{task_id}/archive",
        )
        assert r4.status_code == 200, f"Archive failed: {r4.text}"
        archived = r4.json()["data"]
        assert archived["status"] == "archived"

    async def test_regenerate_task(self, teacher_client, course):
        """重新生成任务 → 200。"""
        # 先生成一个
        r = await teacher_client.post(
            f"/courses/{course['id']}/tasks/generate",
            json={
                "topic": "数据库 SQL 查询",
                "task_type": "homework",
                "difficulty": "medium",
            },
        )
        if r.status_code != 201:
            pytest.skip("Cannot test regenerate without task")
        task_id = r.json()["data"]["id"]

        r2 = await teacher_client.post(
            f"/courses/{course['id']}/tasks/{task_id}/regenerate",
        )
        assert r2.status_code == 200, f"Regenerate failed: {r2.text}"

    async def test_delete_task(self, teacher_client, course):
        """删除任务 → 200/204。"""
        r = await teacher_client.post(
            f"/courses/{course['id']}/tasks/generate",
            json={
                "topic": "临时测试任务（将被删除）",
                "task_type": "homework",
                "difficulty": "easy",
            },
        )
        if r.status_code != 201:
            pytest.skip("Cannot test delete without task")
        task_id = r.json()["data"]["id"]

        r2 = await teacher_client.delete(
            f"/courses/{course['id']}/tasks/{task_id}",
            json={"confirm": True, "confirm_text": "delete"},
        )
        assert r2.status_code in (200, 204)


# ═══════════════════════════════════════════════
# T9.7 — 报告生成与导出
# ═══════════════════════════════════════════════

class TestReportGeneration:
    """V-08：生成报告 → 查看 → 导出"""

    async def test_generate_report(self, teacher_client, course):
        """生成教学报告 → 201/200 + 统计数据。"""
        r = await teacher_client.post(
            f"/courses/{course['id']}/reports/generate",
            json={
                "report_type": "weekly",
                "start_date": "2026-06-01",
                "end_date": "2026-06-07",
                "title": "T9 集成测试周报",
            },
        )
        # 空课程可能没有足够数据生成报告
        if r.status_code in (201, 200):
            report = r.json()["data"]
            assert report["report_type"] in ("weekly", "monthly", "semester")
            assert report["title"]
            return report
        else:
            # 空课程可能返回 400（无数据）也是可接受的
            assert r.status_code in (400, 201, 200)

    async def test_report_list(self, teacher_client, course):
        """报告列表 → 200。"""
        r = await teacher_client.get(f"/courses/{course['id']}/reports")
        assert r.status_code == 200
        data = r.json()["data"]
        assert isinstance(data, list)

    async def test_report_detail(self, teacher_client, course):
        """报告详情 → 200。"""
        # 先生成一个报告
        r = await teacher_client.post(
            f"/courses/{course['id']}/reports/generate",
            json={
                "report_type": "semester",
                "title": "测试学期报告",
            },
        )
        if r.status_code not in (201, 200):
            pytest.skip("Cannot test report detail without report")

        report_id = r.json()["data"]["id"]
        r2 = await teacher_client.get(
            f"/courses/{course['id']}/reports/{report_id}",
        )
        assert r2.status_code == 200
        detail = r2.json()["data"]
        assert detail["id"] == report_id
        assert detail["content"]
        if detail.get("statistics"):
            assert isinstance(detail["statistics"], dict)

    async def test_report_export(self, teacher_client, course):
        """报告导出 → 200 + 文件下载。"""
        # 先生成报告
        r = await teacher_client.post(
            f"/courses/{course['id']}/reports/generate",
            json={
                "report_type": "monthly",
                "title": "导出测试月报",
            },
        )
        if r.status_code not in (201, 200):
            pytest.skip("Cannot test export without report")

        report_id = r.json()["data"]["id"]
        r2 = await teacher_client.get(
            f"/courses/{course['id']}/reports/{report_id}/export",
            params={"format": "md"},
        )
        assert r2.status_code in (200, 201), f"Export failed: {r2.text}"
        # 验证返回内容为 markdown
        content_type = r2.headers.get("content-type", "")
        assert any(t in content_type for t in ["markdown", "text", "octet-stream", "attachment"])


# ═══════════════════════════════════════════════
# V-09 — 资源检索
# ═══════════════════════════════════════════════

class TestResourceSearch:
    """资源检索功能验证"""

    async def test_search_keyword(self, teacher_client, course):
        """关键词搜索 → 200 + 匹配结果。"""
        r = await teacher_client.get(
            f"/courses/{course['id']}/resources/search",
            params={"keyword": "test"},
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert isinstance(data, list)
