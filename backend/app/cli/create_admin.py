"""
Create the first admin user from the command line.

Usage (inside the backend container):
    python -m app.cli.create_admin

This solves the chicken-and-egg problem: you need an admin to create
users via the API, but who creates the first admin?
"""

import asyncio
import sys

from app.core.database import async_session_factory, engine, Base
from app.core.security import hash_password
from app.models.user import User, UserRole


async def main() -> None:
    print("\n── Moimio: Create First Admin ──\n")

    email = input("Email: ").strip()
    if not email:
        print("Email is required.")
        sys.exit(1)

    full_name = input("Full name: ").strip()
    if not full_name:
        print("Full name is required.")
        sys.exit(1)

    password = input("Password: ").strip()
    if len(password) < 8:
        print("Password must be at least 8 characters.")
        sys.exit(1)

    # Create tables if they don't exist yet
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session_factory() as session:
        # Check if user already exists
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            print(f"\nUser {email} already exists.")
            sys.exit(1)

        user = User(
            email=email,
            hashed_password=hash_password(password),
            full_name=full_name,
            role=UserRole.SUPER_ADMIN,
            can_manage_users=True,
            can_create_events=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        print("\nAdmin created successfully:")
        print(f"  ID:    {user.id}")
        print(f"  Email: {user.email}")
        print(f"  Name:  {user.full_name}")
        print(f"  Role:  {user.role.value} (Super Admin)")
        print()

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
