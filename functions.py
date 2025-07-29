import pymysql
import pandas as pd
import os
from datetime import datetime

def manual_load_dotenv(path="env.env"):
    if not os.path.exists(path):
        print("Arquivo inexistente")
        return

    with open(path) as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                key, value = line.strip().split("=", 1)
                os.environ[key] = value
               
#rodar no Localhost
#manual_load_dotenv()
#print("Host do banco:", os.getenv("GCS_KEY_BASE64"))

def get_mysql_conn():
    return pymysql.connect(
        host=os.getenv("host"),
        user=os.getenv("username"),
        password=os.getenv("password"),
        port=int(os.getenv("port")),
        database=os.getenv("database"),
        cursorclass=pymysql.cursors.DictCursor,
        ssl={"ssl": True}  # adapte conforme seu contexto SSL
    )

def criar_tabela_plano_estrategico():
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plano_estrategico (
                    id BIGINT PRIMARY KEY,
                    categoria VARCHAR(255),
                    tarefa TEXT,
                    status VARCHAR(20),
                    data_limite DATE,
                    responsaveis TEXT
                )
            """)
        conn.commit()

def listar_tarefas():
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM plano_estrategico")
            rows = cursor.fetchall()

            colunas = ["id", "categoria", "tarefa", "status", "data_limite", "responsaveis"]
            if not rows:
                return pd.DataFrame(columns=colunas)
            return pd.DataFrame(rows, columns=colunas)

def adicionar_tarefa(categoria, tarefa, status, data_limite, responsaveis):
    # Corrige possíveis hífens invisíveis no campo de data
    if isinstance(data_limite, str):
        data_limite = data_limite.replace("‑", "-").replace("–", "-")  # NB-hyphen e en-dash
        data_limite = datetime.strptime(data_limite, "%Y-%m-%d").date()

    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(id) as max_id FROM plano_estrategico")
            next_id = (cursor.fetchone()['max_id'] or 0) + 1

            cursor.execute("""
                INSERT INTO plano_estrategico (id, categoria, tarefa, status, data_limite, responsaveis)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (next_id, categoria, tarefa, status, data_limite, responsaveis))
        conn.commit()

def atualizar_titulo_categoria(id, nova_tarefa, nova_categoria):
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE plano_estrategico
                SET tarefa = %s, categoria = %s
                WHERE id = %s
            """, (nova_tarefa, nova_categoria, id))
        conn.commit()

def atualizar_tarefa(id, status=None, data_limite=None, responsaveis=None):
    updates = []
    params = []

    if status is not None:
        updates.append("status = %s")
        params.append(status)
    if data_limite is not None:
        updates.append("data_limite = %s")
        params.append(data_limite)
    if responsaveis is not None:
        updates.append("responsaveis = %s")
        params.append(responsaveis)

    if not updates:
        return

    query = f"UPDATE plano_estrategico SET {', '.join(updates)} WHERE id = %s"
    params.append(id)

    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
        conn.commit()

def excluir_tarefa(tarefa_id):
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM plano_estrategico WHERE id = %s", (tarefa_id,))
        conn.commit()

def tarefa_existe(df_db, tarefa, categoria):
    return not df_db[(df_db["tarefa"] == tarefa) & (df_db["categoria"] == categoria)].empty