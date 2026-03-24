import sys
import os

from app.core.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

def create_admin():
    db = SessionLocal()
    email = "admin@canaleducacao.com"
    
    # Check if admin already exists
    existing_user = db.query(User).filter(User.email == email).first()
    if existing_user:
        print(f"User {email} already exists.")
        db.close()
        return

    admin_user = User(
        email=email,
        hashed_password=get_password_hash("admin123"),
        full_name="Admin",
        is_active=True,
        role="admin",
        email_confirmed=True
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    print(f"Admin user created successfully! Email: {email} | Password: admin123")
    db.close()

if __name__ == "__main__":
    create_admin()
