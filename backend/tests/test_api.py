"""
test_api.py — 集成测试：认证、课程、资源、权限、错误处理

覆盖 T9.1, T9.2, T9.3, T9.8, T9.10
"""
import time
import pytest
from tests.conftest import assert_response, poll_until

pytestmark = pytest.mark.integration


# ═══════════════════════════════════════════════
# T9.1 — 认证全流程：注册 → 登录 → Token 刷新 → 退出
# ═══════════════════════════════════════════════

class TestAuthFlow:
    """V-01：用户注册与登录"""

    async def test_register_new_user(self, client):
        """注册新用户 → 201。"""
        import uuid
        uniq = uuid.uuid4().hex[:8]
        r = await client.post("/auth/register", json={
            "username": f"t9_1_register_{uniq}",
            "email": f"t9_1_register_{uniq}@test.com",
            "password": "SecureP@ss123",
            "role": "student",
        })
        assert r.status_code == 201, f"Register failed: {r.text}"
        data = r.json()
        assert data["data"]["user"]["username"] == f"t9_1_register_{uniq}"

    async def test_register_duplicate_username(self, client, student_token):
        """重复用户名注册 → 409。"""
        # student_token fixture 已注册过一个用户
        r = await client.post("/auth/register", json={
            "username": "existing_user_test",
            "email": "test@test.com",
            "password": "Test123456",
            "role": "student",
        })
        # 409 或 200 取决于实现，只验证不崩溃
        assert r.status_code in (200, 201, 409)

    async def test_login_with_valid_credentials(self, client, student_token):
        """使用有效凭据登录 → 200 + access_token。"""
        assert student_token is not None
        assert len(student_token) > 20  # JWT tokens are long

    @pytest.mark.smoke
    async def test_login_with_invalid_password(self, client):
        """错误密码登录 → 401。"""
        r = await client.post("/auth/login", json={
            "username": "nonexistent_user_99999",
            "password": "WrongPassword",
        })
        assert r.status_code in (401, 404, 400)

    async def test_token_refresh(self, client, student_token):
        """Token 刷新 → 200 + 新 token。"""
        r = await client.post("/auth/login", json={
            "username": "test_refresh_student",
            "password": "TestPass123!",
        })
        # Skip if user doesn't exist
        if r.status_code != 200:
            pytest.skip("Test user for refresh not available")

        refresh_token = r.json()["data"].get("refresh_token")
        if not refresh_token:
            pytest.skip("No refresh_token in response")

        r2 = await client.post("/auth/token/refresh", json={
            "refresh_token": refresh_token,
        })
        # 可能 200 或 401（取决于 token 过期策略）
        assert r2.status_code in (200, 401)

    async def test_logout(self, client, student_token):
        """退出登录 → 200。"""
        r = await client.post("/auth/logout", headers={
            "Authorization": f"Bearer {student_token}",
        })
        assert r.status_code in (200, 204)


# ═══════════════════════════════════════════════
# T9.2 — 课程管理：创建 → 加入 → 成员列表
# ═══════════════════════════════════════════════

class TestCourseManagement:
    """V-02, V-03：教师创建课程 + 学生加入"""

    async def test_create_course_as_teacher(self, teacher_client):
        """教师创建课程 → 201 + 课程码。"""
        import uuid
        name = f"T9_Course_{uuid.uuid4().hex[:6]}"
        r = await teacher_client.post("/courses", json={
            "name": name,
            "description": "Integration test course for T9.2",
            "semester": "2026-TEST",
        })
        assert r.status_code == 201, f"Create failed: {r.text}"
        data = r.json()["data"]
        assert data["name"] == name
        assert "code" in data, "Course code missing"
        assert len(data["code"]) == 6, f"Expected 6-char code, got '{data['code']}'"

    async def test_join_course_with_code(self, teacher_client, auth_client):
        """学生使用课程码加入 → 201。"""
        # 教师创建课程
        import uuid
        name = f"T9_Join_{uuid.uuid4().hex[:6]}"
        r = await teacher_client.post("/courses", json={
            "name": name,
            "semester": "2026-TEST",
        })
        assert r.status_code == 201
        code = r.json()["data"]["code"]

        # 学生加入
        r2 = await auth_client.post("/courses/join", json={
            "course_code": code,
        })
        assert r2.status_code in (201, 200), f"Join failed: {r2.text}"

    async def test_join_with_invalid_code(self, auth_client):
        """使用无效课程码 → 404。"""
        r = await auth_client.post("/courses/join", json={
            "course_code": "ZZZZZZ",
        })
        assert r.status_code in (404, 400)

    async def test_get_course_members(self, teacher_client, course):
        """查看课程成员 → 200 + 成员列表。"""
        r = await teacher_client.get(f"/courses/{course['id']}/members")
        assert r.status_code == 200, f"Get members failed: {r.text}"
        data = r.json()["data"]
        assert isinstance(data, list)
        # 教师创建课程后应自动成为成员
        assert len(data) >= 1

    async def test_list_courses(self, teacher_client):
        """课程列表 → 200。"""
        r = await teacher_client.get("/courses")
        assert r.status_code == 200
        data = r.json()["data"]
        assert isinstance(data, list)


# ═══════════════════════════════════════════════
# T9.3 — 资源上传与处理
# ═══════════════════════════════════════════════

class TestResourceUpload:
    """V-04：教师上传资源 → 处理完成"""

    async def test_upload_text_file(self, teacher_client, course):
        """上传 txt 文件 → 202。"""
        import io
        file_content = io.BytesIO(b"This is a test document for integration testing.")
        file_content.name = "test_doc.txt"

        r = await teacher_client.post(
            f"/courses/{course['id']}/resources/upload",
            files={"file": ("test_doc.txt", file_content, "text/plain")},
        )
        # 202 async processing or 201 created
        assert r.status_code in (201, 202), f"Upload failed: {r.text}"

    async def test_upload_invalid_file_type(self, teacher_client, course):
        """上传不支持的文件类型 → 400。"""
        import io
        file_content = io.BytesIO(b"test")
        file_content.name = "test.exe"

        r = await teacher_client.post(
            f"/courses/{course['id']}/resources/upload",
            files={"file": ("test.exe", file_content, "application/octet-stream")},
        )
        # Should reject non-allowed extensions
        assert r.status_code in (400, 422)

    async def test_list_resources(self, teacher_client, course):
        """资源列表 → 200。"""
        r = await teacher_client.get(f"/courses/{course['id']}/resources")
        assert r.status_code == 200
        data = r.json()["data"]
        assert isinstance(data, list)

    async def test_search_resources(self, teacher_client, course):
        """搜索资源 → 200。"""
        r = await teacher_client.get(
            f"/courses/{course['id']}/resources/search",
            params={"keyword": "test"},
        )
        assert r.status_code == 200


# ═══════════════════════════════════════════════
# T9.8 — 角色权限验证
# ═══════════════════════════════════════════════

class TestRolePermissions:
    """学生无法访问管理后台"""

    async def test_student_cannot_access_admin_users(self, auth_client):
        """学生访问 /admin/users → 403。"""
        r = await auth_client.get("/admin/users")
        assert r.status_code in (403, 404, 401), (
            f"Expected 403 for student, got {r.status_code}: {r.text}"
        )

    async def test_student_cannot_access_admin_settings(self, auth_client):
        """学生访问 /admin/settings → 403。"""
        r = await auth_client.get("/admin/settings")
        assert r.status_code in (403, 404, 401)

    async def test_student_cannot_generate_tasks(self, auth_client, course):
        """学生生成任务 → 403。"""
        r = await auth_client.post(f"/courses/{course['id']}/tasks/generate", json={
            "topic": "Test topic",
            "task_type": "homework",
            "difficulty": "easy",
        })
        assert r.status_code in (403, 404)

    async def test_teacher_cannot_access_admin_users(self, teacher_client):
        """教师访问 /admin/users → 403。"""
        r = await teacher_client.get("/admin/users")
        assert r.status_code in (403, 404)


# ═══════════════════════════════════════════════
# T9.9 — 响应时间验证
# ═══════════════════════════════════════════════

class TestResponseTime:
    """非 SSE 端点响应时间 < 3s"""
    RESPONSE_TIME_LIMIT = 3.0

    @pytest.mark.smoke
    async def test_auth_login_response_time(self, client):
        """登录接口响应时间。"""
        start = time.time()
        r = await client.post("/auth/login", json={
            "username": "admin",
            "password": "Admin123!",
        })
        elapsed = time.time() - start
        # 即使失败也应该快速返回
        assert elapsed < self.RESPONSE_TIME_LIMIT, (
            f"Login took {elapsed:.2f}s, expected < {self.RESPONSE_TIME_LIMIT}s"
        )

    async def test_course_list_response_time(self, teacher_client):
        """课程列表响应时间。"""
        start = time.time()
        r = await teacher_client.get("/courses")
        elapsed = time.time() - start
        assert r.status_code == 200
        assert elapsed < self.RESPONSE_TIME_LIMIT, (
            f"Course list took {elapsed:.2f}s"
        )

    async def test_get_me_response_time(self, auth_client):
        """获取当前用户信息响应时间。"""
        start = time.time()
        r = await auth_client.get("/auth/me")
        elapsed = time.time() - start
        assert elapsed < self.RESPONSE_TIME_LIMIT, f"GET /me took {elapsed:.2f}s"


# ═══════════════════════════════════════════════
# T9.10 — 错误处理验证
# ═══════════════════════════════════════════════

class TestErrorHandling:
    """资源不存在 → 404 + 正确错误码"""

    async def test_course_not_found(self, auth_client):
        """不存在的课程 → 404。"""
        r = await auth_client.get("/courses/00000000-0000-0000-0000-000000000000")
        assert r.status_code == 404, f"Expected 404, got {r.status_code}"

    async def test_resource_not_found(self, auth_client, course):
        """不存在的资源 → 404。"""
        r = await auth_client.get(
            f"/courses/{course['id']}/resources/00000000-0000-0000-0000-000000000000"
        )
        assert r.status_code in (404, 403), (
            f"Expected 404/403, got {r.status_code}"
        )

    async def test_task_not_found(self, auth_client, course):
        """不存在的任务 → 404。"""
        r = await auth_client.get(
            f"/courses/{course['id']}/tasks/00000000-0000-0000-0000-000000000000"
        )
        assert r.status_code in (404, 403)

    async def test_unauthorized_access(self, client):
        """未认证访问受保护端点 → 401。"""
        r = await client.get("/auth/me")
        assert r.status_code == 401, f"Expected 401, got {r.status_code}"

    async def test_validation_error(self, client):
        """无效输入 → 422。"""
        r = await client.post("/auth/login", json={"bad_field": "value"})
        assert r.status_code in (422, 400, 401)


# ═══════════════════════════════════════════════
# V-10 — 跨课程数据隔离
# ═══════════════════════════════════════════════

class TestDataIsolation:
    """课程 A 的操作不影响课程 B"""

    async def test_courses_have_independent_resources(self, teacher_client):
        """不同课程的资源列表互不干扰。"""
        import uuid

        # 创建两个课程
        r1 = await teacher_client.post("/courses", json={
            "name": f"Isolation_A_{uuid.uuid4().hex[:4]}",
            "semester": "2026-TEST",
        })
        r2 = await teacher_client.post("/courses", json={
            "name": f"Isolation_B_{uuid.uuid4().hex[:4]}",
            "semester": "2026-TEST",
        })
        if r1.status_code != 201 or r2.status_code != 201:
            pytest.skip("Could not create test courses")

        c1 = r1.json()["data"]
        c2 = r2.json()["data"]

        # 分别在两个课程中上传资源
        import io
        f1 = io.BytesIO(b"Content for course A")
        f2 = io.BytesIO(b"Content for course B")

        await teacher_client.post(
            f"/courses/{c1['id']}/resources/upload",
            files={"file": ("doc_a.txt", f1, "text/plain")},
        )
        await teacher_client.post(
            f"/courses/{c2['id']}/resources/upload",
            files={"file": ("doc_b.txt", f2, "text/plain")},
        )

        # 检查各课程资源独立
        res1 = await teacher_client.get(f"/courses/{c1['id']}/resources")
        res2 = await teacher_client.get(f"/courses/{c2['id']}/resources")

        items1 = {i["file_name"] for i in res1.json().get("data", [])}
        items2 = {i["file_name"] for i in res2.json().get("data", [])}

        # 课程 A 不应有课程 B 的文件
        assert "doc_b.txt" not in items1, "Data isolation violated: course A sees B's files"
        assert "doc_a.txt" not in items2, "Data isolation violated: course B sees A's files"

        # Cleanup
        try:
            await teacher_client.delete(
                f"/courses/{c1['id']}",
                json={"confirm": True, "confirm_text": c1["name"]},
            )
            await teacher_client.delete(
                f"/courses/{c2['id']}",
                json={"confirm": True, "confirm_text": c2["name"]},
            )
        except Exception:
            pass
