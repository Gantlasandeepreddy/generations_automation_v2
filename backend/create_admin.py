#!/usr/bin/env python3
"""
Script to create an initial admin user for the automation system.

Usage:
    python create_admin.py

This script will:
1. Initialize the database if it doesn't exist
2. Prompt for admin email and password
3. Create the admin user in the database
"""

import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))

import getpass
from db.database import SessionLocal, init_db
from db import crud


def create_admin_user():
    """Interactive script to create an admin user"""

    print("=" * 60)
    print(" Create Initial Admin User")
    print("=" * 60)
    print()

    # Initialize database
    print("Initializing database...")
    init_db()
    print("✓ Database initialized")
    print()

    # Get admin details
    email = input("Enter admin email: ").strip()

    if not email:
        print("Error: Email cannot be empty")
        sys.exit(1)

    # Check if user already exists
    db = SessionLocal()
    try:
        existing_user = crud.get_user_by_email(db, email)
        if existing_user:
            print(f"\n❌ Error: User with email '{email}' already exists")
            print(f"   Role: {existing_user.role}")
            print(f"   Active: {existing_user.is_active}")
            sys.exit(1)

        # Get password (hidden input)
        password = getpass.getpass("Enter admin password: ")
        password_confirm = getpass.getpass("Confirm password: ")

        if not password:
            print("\n❌ Error: Password cannot be empty")
            sys.exit(1)

        if password != password_confirm:
            print("\n❌ Error: Passwords do not match")
            sys.exit(1)

        if len(password) < 8:
            print("\n⚠️  Warning: Password is short (recommended: 8+ characters)")
            confirm = input("Continue anyway? (y/N): ").strip().lower()
            if confirm != 'y':
                print("Cancelled")
                sys.exit(0)

        # Create admin user
        print("\nCreating admin user...")
        admin = crud.create_user(
            db=db,
            email=email,
            password=password,
            role="admin"
        )

        print("\n" + "=" * 60)
        print("✓ Admin user created successfully!")
        print("=" * 60)
        print(f"  Email: {admin.email}")
        print(f"  Role: {admin.role}")
        print(f"  ID: {admin.id}")
        print(f"  Created: {admin.created_at}")
        print("=" * 60)
        print("\nYou can now login to the application with these credentials.")

    except Exception as e:
        print(f"\n❌ Error creating admin user: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    try:
        create_admin_user()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
        sys.exit(0)
