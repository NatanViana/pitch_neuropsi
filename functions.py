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


def criar_tabela_despesas():
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS despesas (
                    id BIGINT PRIMARY KEY,
                    nome VARCHAR(255),
                    valor DECIMAL(10, 2)
                )
            """)
        conn.commit()

def criar_tabela_categorias():
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS categorias_plano_estrategico (
                    id BIGINT PRIMARY KEY,
                    nome VARCHAR(255) UNIQUE
                )
            """)
        conn.commit()

def criar_tabela_responsaveis():
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS responsaveis_plano_estrategico (
                    id BIGINT PRIMARY KEY,
                    nome VARCHAR(255) UNIQUE
                )
            """)
        conn.commit()

def listar_categorias():
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM categorias_plano_estrategico ORDER BY nome")
            rows = cursor.fetchall()
            cols = ["id", "nome"]
            return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)

def listar_responsaveis():
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM responsaveis_plano_estrategico ORDER BY nome")
            rows = cursor.fetchall()
            cols = ["id", "nome"]
            return pd.DataFrame(rows, columns=cols) if rows else pd.DataFrame(columns=cols)

def adicionar_categoria(nome):
    if not nome:
        return
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(id) as max_id FROM categorias_plano_estrategico")
            next_id = (cursor.fetchone()['max_id'] or 0) + 1
            try:
                cursor.execute("""
                    INSERT INTO categorias_plano_estrategico (id, nome) VALUES (%s, %s)
                """, (next_id, nome.strip()))
            except pymysql.err.IntegrityError:
                pass  # já existe
        conn.commit()

def adicionar_responsavel(nome):
    if not nome:
        return
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(id) as max_id FROM responsaveis_plano_estrategico")
            next_id = (cursor.fetchone()['max_id'] or 0) + 1
            try:
                cursor.execute("""
                    INSERT INTO responsaveis_plano_estrategico (id, nome) VALUES (%s, %s)
                """, (next_id, nome.strip()))
            except pymysql.err.IntegrityError:
                pass  # já existe
        conn.commit()

def excluir_categoria(categoria_id):
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM categorias_plano_estrategico WHERE id = %s", (categoria_id,))
        conn.commit()

def excluir_responsavel(responsavel_id):
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM responsaveis_plano_estrategico WHERE id = %s", (responsavel_id,))
        conn.commit()

def renomear_categoria(categoria_id, novo_nome):
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE categorias_plano_estrategico SET nome = %s WHERE id = %s
            """, (novo_nome.strip(), categoria_id))
        conn.commit()

def renomear_responsavel(responsavel_id, novo_nome):
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE responsaveis_plano_estrategico SET nome = %s WHERE id = %s
            """, (novo_nome.strip(), responsavel_id))
        conn.commit()

def seed_categorias_e_responsaveis():
    df = listar_tarefas()
    # categorias
    for cat in sorted(set(df["categoria"].dropna().astype(str))):
        if cat.strip():
            adicionar_categoria(cat.strip())

    # responsaveis (coluna é string com nomes separados por vírgula)
    responsaveis_raw = []
    for txt in df["responsaveis"].fillna(""):
        responsaveis_raw.extend([r.strip() for r in str(txt).split(",") if r.strip()])
    for r in sorted(set(responsaveis_raw)):
        adicionar_responsavel(r)


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
    if isinstance(data_limite, str):
        data_limite = data_limite.replace("‑", "-").replace("–", "-")
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


def excluir_despesa(despesa_id):
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM despesas WHERE id = %s", (despesa_id,))
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

def migrar_tabela_despesas_add_campos_periodo():
    """
    Adiciona campos de período na tabela despesas:
    - mes_inicio (INT, default 1)
    - duracao_meses (INT, NULL)  -> NULL = duração infinita

    Seguro para rodar várias vezes (idempotente).
    """
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            # garante que a tabela existe
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS despesas (
                    id BIGINT PRIMARY KEY,
                    nome VARCHAR(255),
                    valor DECIMAL(10, 2)
                )
            """)

            def coluna_existe(nome_coluna: str) -> bool:
                cursor.execute("SHOW COLUMNS FROM despesas LIKE %s", (nome_coluna,))
                return cursor.fetchone() is not None

            # adiciona mes_inicio
            if not coluna_existe("mes_inicio"):
                cursor.execute("""
                    ALTER TABLE despesas
                    ADD COLUMN mes_inicio INT NOT NULL DEFAULT 1
                """)

            # adiciona duracao_meses
            if not coluna_existe("duracao_meses"):
                cursor.execute("""
                    ALTER TABLE despesas
                    ADD COLUMN duracao_meses INT NULL
                """)

        conn.commit()

def adicionar_despesa(nome, valor, mes_inicio=1, duracao_meses=None):
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(id) as max_id FROM despesas")
            next_id = (cursor.fetchone()['max_id'] or 0) + 1

            # tenta inserir com colunas novas; se não existirem, cai no insert antigo
            try:
                cursor.execute("""
                    INSERT INTO despesas (id, nome, valor, mes_inicio, duracao_meses)
                    VALUES (%s, %s, %s, %s, %s)
                """, (next_id, nome, valor, int(mes_inicio), duracao_meses))
            except Exception:
                cursor.execute("""
                    INSERT INTO despesas (id, nome, valor)
                    VALUES (%s, %s, %s)
                """, (next_id, nome, valor))
        conn.commit()


def atualizar_despesa(id, nome=None, valor=None, mes_inicio=None, duracao_meses=None):
    updates = []
    params = []

    if nome is not None:
        updates.append("nome = %s")
        params.append(nome)
    if valor is not None:
        updates.append("valor = %s")
        params.append(valor)

    # colunas novas (se existirem)
    if mes_inicio is not None:
        updates.append("mes_inicio = %s")
        params.append(int(mes_inicio))
    if duracao_meses is not None or duracao_meses is None:
        # se você passar duracao_meses, atualiza (inclusive pra NULL)
        updates.append("duracao_meses = %s")
        params.append(duracao_meses)

    if not updates:
        return

    query = f"UPDATE despesas SET {', '.join(updates)} WHERE id = %s"
    params.append(id)

    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute(query, params)
        conn.commit()
