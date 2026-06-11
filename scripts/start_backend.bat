@echo off
cd /d "d:\agent_project_v2\backend"
call venv\Scripts\activate
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
set REDIS_HOST=localhost
set REDIS_PORT=6379
set CHROMA_HOST=localhost
set CHROMA_PORT=8001
set MINIO_ENDPOINT=localhost:9000
set DEBUG=true
set NO_PROXY=*
set no_proxy=*
alembic upgrade head
uvicorn app.main:app --host 0.0.0.0 --port 8000
pause
