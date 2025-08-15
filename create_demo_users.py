#!/usr/bin/env python3
"""Script to create demo users for testing the authentication system."""

import asyncio
from pathlib import Path

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text, select, func
from advanced_alchemy.base import UUIDAuditBase

from server.backend.models import User


async def create_demo_users():
    """Create demo users in the database."""
    # Create database engine
    db_path = Path("demo_data/backend.sqlite")
    db_path.parent.mkdir(exist_ok=True)
    
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(UUIDAuditBase.metadata.create_all)

    # Create session
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Check if users already exist
        existing_users = await session.execute(
            select(func.count(User.id))
        )
        count = existing_users.scalar()
        
        if count > 0:
            print(f"Database already has {count} users. Skipping user creation.")
            return
        
        # Create demo users
        demo_users = [
            {
                "username": "demo",
                "password": "password123",
                "email": "demo@example.com"
            },
            {
                "username": "admin",
                "password": "admin123",
                "email": "admin@example.com"
            },
            {
                "username": "test",
                "password": "test123",
                "email": "test@example.com"
            }
        ]
        
        for user_data in demo_users:
            user = User(
                username=user_data["username"],
                password_hash=User.hash_password(user_data["password"]),
                email=user_data["email"],
                is_active=True
            )
            session.add(user)
        
        await session.commit()
        print(f"Created {len(demo_users)} demo users:")
        for user_data in demo_users:
            print(f"  - Username: {user_data['username']}, Password: {user_data['password']}")


if __name__ == "__main__":
    asyncio.run(create_demo_users())
