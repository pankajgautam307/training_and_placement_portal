
from flask import Flask
print("Flask imported")
try:
    from app import create_app, db
    print("App imported successfully")
except Exception as e:
    print(f"Import failed: {e}")
