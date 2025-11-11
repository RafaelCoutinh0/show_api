# api.py
import os
from fastapi import FastAPI
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="ShowDoCouto Auth API")

# DATABASE_URL deve estar como variável de ambiente no Railway.
# Exemplo (não colocar no código): postgresql://postgres:EXAMPLE_PASS@host:port/railway
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não está definida. Defina no Railway (Project -> Variables).")

def connect():
    return psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)

def init_db():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome TEXT NOT NULL,
            matricula TEXT UNIQUE NOT NULL,
            email TEXT NOT NULL,
            senha TEXT NOT NULL
        );
    """)
    conn.commit()
    cur.close()
    conn.close()

init_db()

class RegisterIn(BaseModel):
    nome: str
    matricula: str
    email: str
    senha: str

@app.post("/register")
def register(payload: RegisterIn):
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO usuarios (nome, matricula, email, senha) VALUES (%s, %s, %s, %s)",
            (payload.nome.strip(), payload.matricula.strip(), payload.email.strip(), payload.senha)
        )
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "REGISTER_OK"}
    except psycopg2.IntegrityError:
        # matrícula duplicada
        conn.rollback()
        cur.close()
        conn.close()
        return {"status": "REGISTER_FAIL", "detail": "matricula_exists"}
    except Exception as e:
        return {"status": "REGISTER_FAIL", "detail": str(e)}

@app.get("/login")
def login(matricula: str, senha: str):
    conn = connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, nome, email FROM usuarios WHERE matricula=%s AND senha=%s",
        (matricula.strip(), senha)
    )
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user:
        return {"status": "LOGIN_OK", "user": user}
    else:
        return {"status": "LOGIN_FAIL"}

