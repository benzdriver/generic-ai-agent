import pytest
from httpx import AsyncClient
import os

# 获取在容器内运行的API服务的URL
# 在docker-compose网络中，服务可以通过其名称被访问
BASE_URL = "http://api:8080" 

@pytest.mark.asyncio
async def test_health_check():
    """
    测试 /health 端点是否正常返回200 OK
    """
    async with AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/health/")
        assert response.status_code == 200
        # 检查响应体是否符合预期
        json_response = response.json()
        assert json_response["status"] == "healthy"
        assert "version" in json_response

@pytest.mark.asyncio
async def test_create_crawl_job_validation_error():
    """
    测试 /api/v1/crawl 端点在接收到无效数据时是否返回422 Unprocessable Entity
    """
    invalid_payload = {
        "invalid_key": "some_value" # 提供一个无效的payload
    }
    async with AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/v1/crawl", json=invalid_payload)
        # 根据FastAPI的默认行为，验证错误应该返回422
        assert response.status_code == 422

@pytest.mark.asyncio
async def test_create_crawl_job_success():
    """
    测试创建一个有效的爬取任务是否成功
    """
    valid_payload = {
        "urls": ["https://example.com"],
        "config": {
            "max_depth": 1,
            "ai_evaluation": False
        }
    }
    async with AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/api/v1/crawl", json=valid_payload)
        assert response.status_code == 200
        json_response = response.json()
        assert "job_id" in json_response
        assert json_response["status"] == "queued"
        assert len(json_response["job_id"]) > 10 # 确保job_id是一个合理的字符串 