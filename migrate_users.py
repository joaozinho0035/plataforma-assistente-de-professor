import sys
from sqlalchemy import text
from app.core.database import engine

def migrate_users():
    with engine.connect() as conn:
        try:
            print("Renaming 'username' to 'email'...")
            conn.execute(text("ALTER TABLE users RENAME COLUMN username TO email;"))
            
            print("Adding missing columns...")
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_confirmed BOOLEAN DEFAULT FALSE NOT NULL;"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS invite_token VARCHAR(255) NULL;"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS invite_expires_at TIMESTAMP WITH TIME ZONE NULL;"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS invited_by UUID NULL REFERENCES users(id);"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL;"))
            conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL;"))
            conn.commit()
            print("Migration successful.")
        except Exception as e:
            print(f"Error during migration: {e}")

if __name__ == "__main__":
    migrate_users()
