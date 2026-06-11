"""创建默认管理员账号脚本。

用法:
    cd backend && venv\Scripts\activate && python -m app.scripts.create_admin

默认账号: admin / admin
"""
import asyncio
import sys
import os

# 确保项目根目录在 sys.path 中
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import select
from app.database import async_session
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import hash_password


async def create_admin():
    async with async_session() as db:
        # 检查是否已存在 admin 用户
        result = await db.execute(select(User).where(User.username == "admin"))
        existing = result.scalar_one_or_none()
        if existing:
            print(f"[INFO] 管理员账号已存在: {existing.username} ({existing.email})")
            print(f"[INFO] 跳过创建。如需重置密码，请删除此用户后重新运行本脚本。")
            return

        # 创建管理员账号
        admin = User(
            username="admin",
            email="admin@eduagent.local",
            password_hash=hash_password("admin"),
            role=UserRole.ADMIN,
            display_name="系统管理员",
            is_active=True,
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        print(f"[OK] 管理员账号创建成功！")
        print(f"     用户名: admin")
        print(f"     密码:   admin")
        print(f"     角色:   admin")


if __name__ == "__main__":
    asyncio.run(create_admin())
