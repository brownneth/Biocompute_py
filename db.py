import pymysql
from flask import g
from config import Config

def get_conn():
    if "db_conn" not in g:
        g.db_conn = pymysql.connect(
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            database=Config.DB_NAME,
            autocommit=False,
            cursorclass=pymysql.cursors.DictCursor,
        )
    return g.db_conn

def close_conn(e=None):
    conn = g.pop("db_conn", None)
    if conn:
        conn.close()

def query_one(sql, params=()):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()

def query_all(sql, params=()):
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()

def execute(sql, params=()):
    conn = get_conn()
    with conn.cursor() as cur:
        affected = cur.execute(sql, params)
        last_id = cur.lastrowid
    return affected, last_id

def commit():
    get_conn().commit()

def rollback():
    get_conn().rollback()
