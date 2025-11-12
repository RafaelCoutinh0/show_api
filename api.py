from fastapi import FastAPI, Request
import psycopg2
import os
import json

app = FastAPI()

# =============================
# CONEXÃO AUTOMÁTICA AO POSTGRES
# =============================
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:pdaUDKzpwZxnGaqHbgXdPERAHmqgThWV@hopper.proxy.rlwy.net:52495/railway"
)

def get_connection():
    return psycopg2.connect(DATABASE_URL)

# =============================
# CRIA A TABELA SE NÃO EXISTIR
# =============================
def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            matricula TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            senha TEXT NOT NULL
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

# =============================
# ROTAS
# =============================

@app.get("/")
def root():
    return {"status": "API ON"}

@app.post("/register")
async def register(request: Request):
    data = await request.json()

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO usuarios (nome, matricula, email, senha)
            VALUES (%s, %s, %s, %s)
        """, (data["nome"], data["matricula"], data["email"], data["senha"]))
        conn.commit()
        return {"success": True, "message": "Usuário registrado com sucesso!"}
    except psycopg2.Error as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cur.close()
        conn.close()


@app.post("/login")
async def login(request: Request):
    data = await request.json()

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM usuarios WHERE matricula = %s AND senha = %s",
                (data["matricula"], data["senha"]))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user:
        return {"success": True, "message": "Login realizado com sucesso!"}
    else:
        return {"success": False, "message": "Matrícula ou senha incorreta."}
