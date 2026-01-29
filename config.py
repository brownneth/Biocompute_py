import os

class Config:
    # Example: mysql://user:pass@host:port/dbname
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", "3306"))
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_NAME = os.getenv("DB_NAME", "mydb")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "xyzabc_cantguessme")
