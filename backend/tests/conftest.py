"""
conftest.py — Pytest 共享 Fixtures & 测试基础设施

提供：
- async HTTP 客户端（连接 localhost:8000）
- 认证 token 管理（注册/登录/刷新）
- 测试数据准备（课程、资源等）
"""
import pytest
import httpx
import os
import time
import uuid
from typing import Optional

# ── 配置 ──
BASE_URL = os.getenv("TEST_BASE_URL", "http://localhost:8000")
API_V1 = f"{BASE_URL}/api/v1"
TEST_PREFIX = f"test_{uuid.uuid4().hex[:6]}"


def _unique(prefix: str) -> str:
    """生成唯一测试标识。"""
    return f"{TEST_PREFIX}_{prefix}"


# ═══════════════════════════════════════════════
# HTTP 客户端 Fixtures
# ═══════════════════════════════════════════════

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client() -> httpx.AsyncClient:
    """未认证的 HTTP 客户端。"""
    async with httpx.AsyncClient(base_url=API_V1, timeout=30.0) as c:
        yield c


@pytest.fixture
async def auth_client(client, student_token) -> httpx.AsyncClient:
    """已认证的客户端（学生角色）。"""
    client.headers["Authorization"] = f"Bearer {student_token}"
    yield client
    client.headers.pop("Authorization", None)


@pytest.fixture
async def teacher_client(client, teacher_token) -> httpx.AsyncClient:
    """已认证的客户端（教师角色）。"""
    client.headers["Authorization"] = f"Bearer {teacher_token}"
    yield client
    client.headers.pop("Authorization", None)


@pytest.fixture
async def admin_client(client, admin_token) -> httpx.AsyncClient:
    """已认证的客户端（管理员角色）。"""
    client.headers["Authorization"] = f"Bearer {admin_token}"
    yield client
    client.headers.pop("Authorization", None)


# ═══════════════════════════════════════════════
# 认证 Fixtures（T9.1）
# ═══════════════════════════════════════════════

@pytest.fixture(scope="session")
def _test_users():
    """生成唯一测试用户凭证（session 级复用）。"""
    return {
        "student": {
            "username": _unique("student"),
            "email": f"{_unique('student')}@test.com",
            "password": "TestPass123!",
            "role": "student",
        },
        "teacher": {
            "username": _unique("teacher"),
            "email": f"{_unique('teacher')}@test.com",
            "password": "TestPass123!",
            "role": "teacher",
        },
    }


@pytest.fixture
async def student_token(client):
    """注册+登录学生 → 返回 access_token。"""
    username = _unique("student")
    email = f"{username}@test.com"
    password = "TestPass123!"

    # 注册
    r = await client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": password,
        "role": "student",
    })
    # 如果已存在则登录
    if r.status_code == 409:
        pass

    # 登录
    r = await client.post("/auth/login", json={
        "username": username,
        "password": password,
    })
    assert r.status_code == 200, f"Login failed: {r.text}"
    data = r.json()
    return data["data"]["access_token"]


@pytest.fixture
async def teacher_token(client):
    """注册+登录教师 → 返回 access_token。"""
    username = _unique("teacher")
    email = f"{username}@test.com"
    password = "TestPass123!"

    r = await client.post("/auth/register", json={
        "username": username,
        "email": email,
        "password": password,
        "role": "teacher",
    })
    if r.status_code == 409:
        pass

    r = await client.post("/auth/login", json={
        "username": username,
        "password": password,
    })
    assert r.status_code == 200, f"Teacher login failed: {r.text}"
    data = r.json()
    return data["data"]["access_token"]


async def _get_admin_token(client) -> Optional[str]:
    """尝试登录 admin 账户，不存在则返回 None。"""
    r = await client.post("/auth/login", json={
        "username": "admin",
        "password": "Admin123!",
    })
    if r.status_code == 200:
        return r.json()["data"]["access_token"]
    return None


@pytest.fixture
async def admin_token(client):
    """获取管理员 token。"""
    token = await _get_admin_token(client)
    if token:
        return token
    # 如果没有 admin 账户，使用 teacher token 作为降级
    pytest.skip("No admin account available for testing")


# ═══════════════════════════════════════════════
# 测试数据 Fixtures（T9.2）
# ═══════════════════════════════════════════════

@pytest.fixture
async def course(teacher_client):
    """创建测试课程 → 返回课程数据。"""
    semester = f"2026-TEST-{uuid.uuid4().hex[:4]}"
    r = await teacher_client.post("/courses", json={
        "name": _unique("course"),
        "description": "Auto-created test course for integration testing",
        "semester": semester,
    })
    assert r.status_code == 201, f"Course creation failed: {r.text}"
    data = r.json()
    course = data["data"]
    yield course

    # cleanup: try to delete
    try:
        await teacher_client.delete(
            f"/courses/{course['id']}",
            json={"confirm": True, "confirm_text": course["name"]},
        )
    except Exception:
        pass  # best-effort cleanup


@pytest.fixture
async def course_code(course):
    """返回课程邀请码。"""
    return course["code"]


# ═══════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════

async def assert_response(response: httpx.Response, expected_status: int, msg_prefix: str = ""):
    """断言响应状态码并提供详细错误信息。"""
    assert response.status_code == expected_status, (
        f"{msg_prefix} Expected {expected_status}, got {response.status_code}: {response.text[:300]}"
    )


async def poll_until(
    fetch_fn,
    check_fn,
    timeout: float = 30.0,
    interval: float = 1.0,
    label: str = "condition",
):
    """轮询直到条件满足或超时。"""
    started = time.time()
    last_error = None
    while time.time() - started < timeout:
        try:
            result = await fetch_fn()
            if check_fn(result):
                return result
        except Exception as e:
            last_error = e
        time.sleep(interval)

    msg = f"Timeout waiting for {label} after {timeout}s"
    if last_error:
        msg += f": {last_error}"
    raise TimeoutError(msg)
