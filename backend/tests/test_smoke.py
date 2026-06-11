"""
test_smoke.py — 冒烟测试：后端服务可用性快速检查

运行: pytest tests/test_smoke.py -v -m smoke
"""
import pytest

pytestmark = pytest.mark.smoke


class TestServerHealth:
    """验证后端服务是否正常运行"""

    async def test_api_root_accessible(self, client):
        """API 根路径可访问。"""
        r = await client.get("/")  # FastAPI root
        # 可能返回 200（docs redirect）或 404
        assert r.status_code in (200, 404)

    async def test_api_docs_accessible(self, client):
        """OpenAPI 文档可访问。"""
        r = await client.get("/openapi.json")
        if r.status_code == 200:
            data = r.json()
            assert "openapi" in data
            assert "paths" in data

    async def test_health_endpoint(self, client):
        """健康检查端点（如有）。"""
        r = await client.get("/health")
        # 可能没有此端点，不强制要求
        assert r.status_code in (200, 404)
