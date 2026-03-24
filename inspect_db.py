import sys
import os
from sqlalchemy import inspect
from app.core.database import engine

def inspect_users_table():
    inspector = inspect(engine)
    if 'users' in inspector.get_table_names():
        columns = inspector.get_columns('users')
        print("Columns in 'users' table:")
        for col in columns:
            print(f" - {col['name']} ({col['type']})")
    else:
        print("The 'users' table does NOT exist.")

if __name__ == "__main__":
    inspect_users_table()
