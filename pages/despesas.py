import streamlit as st
import pandas as pd
from functions import (
    criar_tabela_despesas,
    adicionar_despesa,
    atualizar_despesa,
    excluir_despesa,
    get_mysql_conn,
    migrar_tabela_despesas_add_campos_periodo,  # <-- nova função
)

st.set_page_config(page_title="Despesas Globais", layout="wide")
st.title("💰 Cadastro de Despesas Globais da Clínica")

# ------------------------------------------------------------
# Criar tabela e (opcional) migrar colunas
# ------------------------------------------------------------
criar_tabela_despesas()

st.markdown("### 🛠️ Estrutura do Banco (Despesas)")
col_m1, col_m2 = st.columns([1, 3])
with col_m1:
    if st.button("➕ Criar colunas de período"):
        try:
            migrar_tabela_despesas_add_campos_periodo()
            st.success("OK! Colunas criadas/atualizadas: mes_inicio, duracao_meses.")
            st.rerun()
        except Exception as e:
            st.error(f"Erro ao atualizar tabela despesas: {e}")
with col_m2:
    st.caption("Se ainda não tiver rodado a migração, clique no botão acima (é seguro rodar mais de uma vez).")


def colunas_existentes() -> set:
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SHOW COLUMNS FROM despesas")
            cols = cursor.fetchall()
            return {c["Field"] for c in cols}


COLS = colunas_existentes()
TEM_PERIODO = ("mes_inicio" in COLS) and ("duracao_meses" in COLS)

if not TEM_PERIODO:
    st.info("Sua tabela ainda não tem colunas de período. Clique em **Criar colunas de período** para habilitar início e duração.")


# ------------------------------------------------------------
# Carregar dados
# ------------------------------------------------------------
def carregar_despesas():
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM despesas ORDER BY id")
            return pd.DataFrame(cursor.fetchall())


df_despesas = carregar_despesas()


# ------------------------------------------------------------
# Formulário: adicionar despesa
# ------------------------------------------------------------
st.markdown("### ➕ Adicionar nova despesa")

with st.form("form_add_despesa", clear_on_submit=True):
    if TEM_PERIODO:
        col1, col2, col3, col4 = st.columns([2.4, 1.2, 1.0, 1.4])
        nome = col1.text_input("Nome da despesa")
        valor = col2.number_input("Valor (R$)", min_value=0.0, step=100.0, value=0.0)
        mes_inicio = col3.number_input("Início (mês)", min_value=1, value=1)
        duracao = col4.number_input("Duração (meses) — 0 = infinito", min_value=0, value=0)
    else:
        col1, col2 = st.columns([2, 1])
        nome = col1.text_input("Nome da despesa")
        valor = col2.number_input("Valor (R$)", min_value=0.0, step=100.0, value=0.0)
        mes_inicio = 1
        duracao = 0

    submitted = st.form_submit_button("➕ Adicionar despesa")

    if submitted and nome:
        try:
            duracao_meses = None if (not TEM_PERIODO or int(duracao) == 0) else int(duracao)
            # Requer adicionar_despesa aceitar esses params (veja patch no functions.py)
            adicionar_despesa(nome, valor, mes_inicio=int(mes_inicio), duracao_meses=duracao_meses)
            st.success(f"Despesa '{nome}' adicionada!")
            st.rerun()
        except TypeError:
            st.error("Seu functions.py ainda não foi atualizado para aceitar mes_inicio/duracao_meses em adicionar_despesa().")
        except Exception as e:
            st.error(f"Erro ao adicionar despesa: {e}")


# ------------------------------------------------------------
# Lista / edição
# ------------------------------------------------------------
st.markdown("### 🧾 Despesas Cadastradas")

total_mes1 = 0.0

def despesa_ativa_no_mes(mes: int, inicio: int, duracao_meses) -> bool:
    # duracao_meses None -> infinito
    if duracao_meses is None or (isinstance(duracao_meses, float) and pd.isna(duracao_meses)):
        return mes >= inicio
    dur = int(duracao_meses)
    fim = inicio + dur - 1
    return inicio <= mes <= fim


for _, row in df_despesas.iterrows():
    id_despesa = row["id"]

    nome_atual = row.get("nome", "")
    valor_atual = float(row.get("valor", 0) or 0)

    if TEM_PERIODO:
        inicio_atual = int(row.get("mes_inicio", 1) or 1)
        duracao_atual = row.get("duracao_meses", None)
        duracao_ui = 0 if (duracao_atual is None or (isinstance(duracao_atual, float) and pd.isna(duracao_atual))) else int(duracao_atual)
    else:
        inicio_atual = 1
        duracao_atual = None
        duracao_ui = 0

    # soma total do mês 1 (mais útil para custo fixo inicial)
    if TEM_PERIODO:
        if despesa_ativa_no_mes(1, inicio_atual, duracao_atual):
            total_mes1 += valor_atual
    else:
        total_mes1 += valor_atual

    if TEM_PERIODO:
        col1, col2, col3, col4, col5 = st.columns([3, 2, 1, 1.5, 1])
        novo_nome = col1.text_input("Categoria", value=nome_atual, key=f"nome_{id_despesa}")
        novo_valor = col2.number_input("Valor (R$)", value=float(valor_atual), min_value=0.0, step=100.0, key=f"valor_{id_despesa}")
        novo_inicio = col3.number_input("Início", value=int(inicio_atual), min_value=1, key=f"inicio_{id_despesa}")
        nova_duracao = col4.number_input("Duração (0=infinito)", value=int(duracao_ui), min_value=0, key=f"dur_{id_despesa}")
        remover = col5.button("🗑️ Remover", key=f"remove_{id_despesa}")

        mudou = (
            novo_nome != nome_atual
            or float(novo_valor) != float(valor_atual)
            or int(novo_inicio) != int(inicio_atual)
            or int(nova_duracao) != int(duracao_ui)
        )

        if mudou:
            try:
                duracao_meses = None if int(nova_duracao) == 0 else int(nova_duracao)
                atualizar_despesa(
                    id_despesa,
                    nome=novo_nome,
                    valor=float(novo_valor),
                    mes_inicio=int(novo_inicio),
                    duracao_meses=duracao_meses,
                )
            except TypeError:
                st.error("Seu functions.py ainda não foi atualizado para aceitar mes_inicio/duracao_meses em atualizar_despesa().")
            except Exception as e:
                st.error(f"Erro ao atualizar despesa {id_despesa}: {e}")

    else:
        col1, col2, col3 = st.columns([3, 2, 1])
        novo_nome = col1.text_input("Categoria", value=nome_atual, key=f"nome_{id_despesa}")
        novo_valor = col2.number_input("Valor (R$)", value=float(valor_atual), min_value=0.0, step=100.0, key=f"valor_{id_despesa}")
        remover = col3.button("🗑️ Remover", key=f"remove_{id_despesa}")

        if novo_nome != nome_atual or float(novo_valor) != float(valor_atual):
            atualizar_despesa(id_despesa, nome=novo_nome, valor=float(novo_valor))

    if remover:
        excluir_despesa(id_despesa)
        st.rerun()


# ------------------------------------------------------------
# Total + session_state
# ------------------------------------------------------------
st.markdown("---")

if TEM_PERIODO:
    st.subheader(f"💵 Total de despesas ativas no MÊS 1: R$ {total_mes1:,.2f}")
    st.session_state["custo_fixo_inicial"] = float(total_mes1)
    st.info("Esse valor (mês 1) será usado como custo fixo inicial padrão no simulador financeiro.")
else:
    st.subheader(f"💵 Total de despesas fixas: R$ {total_mes1:,.2f}")
    st.session_state["custo_fixo_inicial"] = float(total_mes1)
    st.info("Esse valor será usado como custo fixo inicial no simulador financeiro.")
