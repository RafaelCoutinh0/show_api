from fastapi import FastAPI
import psycopg2
import os

app = FastAPI()

DATABASE_URL = os.environ["DATABASE_URL"]

def get_conn():
    return psycopg2.connect(DATABASE_URL)

@app.get("/")
def home():
    return {"status": "API ON"}

@app.post("/register")
def register(data: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO usuarios (nome, matricula, email, senha)
        VALUES (%s, %s, %s, %s)
    """, (
        data["nome"],
        data["matricula"],
        data["email"],
        data["senha"]
    ))
    conn.commit()
    cur.close()
    conn.close()
    return {"success": True}

@app.post("/login")
def login(data: dict):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM usuarios
        WHERE matricula=%s AND senha=%s
    """, (
        data["matricula"],
        data["senha"]
    ))
    user = cur.fetchone()
    cur.close()
    conn.close()

    return {"success": bool(user)}
