"""Database seeding script for initial data setup."""

import asyncio
import json
from uuid import uuid4

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal, init_db
from app.models.user import Role, User, UserPreferences


async def seed_database() -> None:
    """Seed database with initial roles and test user."""
    print("🌱 Initializing database...")
    await init_db()
    print("✅ Database initialized\n")

    async with AsyncSessionLocal() as session:
        # Check if roles already exist
        result = await session.execute(select(Role))
        existing_roles = result.scalars().all()

        if existing_roles:
            print("⚠️  Database already seeded with roles. Skipping role creation.")
        else:
            print("📝 Creating roles...")

            # Admin role with all permissions
            admin_role = Role(
                id="ROLE-ADMIN",
                name="Admin",
                permissions=json.dumps(["*"]),
                description="Full system access",
            )

            # Operator role with camera and attendance permissions
            operator_role = Role(
                id="ROLE-OPERATOR",
                name="Operator",
                permissions=json.dumps([
                    "cameras:read",
                    "cameras:write",
                    "detections:read",
                    "attendance:read",
                    "attendance:write",
                    "faces:read",
                    "faces:write",
                    "users:read",
                    "system:read",
                ]),
                description="Operational access to cameras and attendance",
            )

            # Viewer role with read-only permissions
            viewer_role = Role(
                id="ROLE-VIEWER",
                name="Viewer",
                permissions=json.dumps([
                    "cameras:read",
                    "detections:read",
                    "attendance:read",
                    "faces:read",
                    "system:read",
                ]),
                description="Read-only access to system",
            )

            session.add(admin_role)
            session.add(operator_role)
            session.add(viewer_role)
            print("   ✓ Admin, Operator, Viewer roles created")

        # Check if admin user already exists
        result = await session.execute(select(User).where(User.email == "admin@example.com"))
        existing_admin = result.scalar_one_or_none()

        if existing_admin:
            print("⚠️  Admin user already exists. Skipping user creation.")
        else:
            print("📝 Creating test users...")

            # Create admin user
            admin_user = User(
                id=str(uuid4()),
                email="admin@example.com",
                name="System Administrator",
                hashed_password=hash_password("admin123"),
                role_id="ROLE-ADMIN",
                status="active",
            )

            # Create operator user
            operator_user = User(
                id=str(uuid4()),
                email="operator@example.com",
                name="Camera Operator",
                hashed_password=hash_password("operator123"),
                role_id="ROLE-OPERATOR",
                status="active",
            )

            # Create viewer user
            viewer_user = User(
                id=str(uuid4()),
                email="viewer@example.com",
                name="System Viewer",
                hashed_password=hash_password("viewer123"),
                role_id="ROLE-VIEWER",
                status="active",
            )

            session.add(admin_user)
            session.add(operator_user)
            session.add(viewer_user)

            print("   ✓ Admin user created (admin@example.com / admin123)")
            print("   ✓ Operator user created (operator@example.com / operator123)")
            print("   ✓ Viewer user created (viewer@example.com / viewer123)")

            # Create default preferences for users
            for user in [admin_user, operator_user, viewer_user]:
                prefs = UserPreferences(
                    id=str(uuid4()),
                    user_id=user.id,
                    theme="light",
                    grid_mode=True,
                    auto_rotate=False,
                    language="en",
                    timezone="UTC",
                    preferences=json.dumps({}),
                )
                session.add(prefs)

            print("   ✓ User preferences created")

        await session.commit()
        print("\n✅ Database seeding completed successfully!\n")
        print("📌 Test Credentials:")
        print("   Admin:    admin@example.com / admin123")
        print("   Operator: operator@example.com / operator123")
        print("   Viewer:   viewer@example.com / viewer123\n")


if __name__ == "__main__":
    asyncio.run(seed_database())
