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
    "postgresql://postgres:NrjGBvEfvzUBsVrZELAQZLJgVnIydcua@gondola.proxy.rlwy.net:11995/railway"
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


@app.post("/save_progress")
async def save_progress(request: Request):
    data = await request.json()
    matricula = data.get("matricula")
    nivel = data.get("nivel")
    historico = json.dumps(data.get("historico", []))

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO progresso (matricula, nivel, historico)
            VALUES (%s, %s, %s)
            ON CONFLICT (matricula) DO UPDATE
            SET nivel = EXCLUDED.nivel, historico = EXCLUDED.historico
        """, (matricula, nivel, historico))
        conn.commit()
        return {"success": True, "message": "Progresso salvo com sucesso!"}
    except psycopg2.Error as e:
        conn.rollback()
        return {"success": False, "message": str(e)}
    finally:
        cur.close()
        conn.close()

@app.get("/load_progress")
async def load_progress(matricula: str):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT nivel, historico FROM progresso WHERE matricula = %s", (matricula,))
        row = cur.fetchone()
        if row:
            nivel, historico = row
            return {"success": True, "nivel": nivel, "historico": json.loads(historico)}
        return {"success": False, "message": "Progresso não encontrado."}
    except psycopg2.Error as e:
        return {"success": False, "message": str(e)}
    finally:
        cur.close()
        conn.close()

# Inicializa a tabela de progresso
def init_progress_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS progresso (
            matricula TEXT PRIMARY KEY,
            nivel INTEGER NOT NULL,
            historico TEXT NOT NULL
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

init_progress_table()
