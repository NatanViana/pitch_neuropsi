import streamlit as st
import pandas as pd
from functions import criar_tabela_despesas, adicionar_despesa, atualizar_despesa, excluir_despesa, get_mysql_conn

st.set_page_config(page_title="Despesas Globais", layout="wide")
st.title("💰 Cadastro de Despesas Globais da Clínica")

# Criar a tabela no banco se não existir
criar_tabela_despesas()

# Carregar dados do banco
def carregar_despesas():
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM despesas ORDER BY id")
            return pd.DataFrame(cursor.fetchall())

df_despesas = carregar_despesas()

# Formulário para adicionar nova despesa
with st.form("form_add_despesa", clear_on_submit=True):
    col1, col2 = st.columns([2, 1])
    nome = col1.text_input("Nome da despesa")
    valor = col2.number_input("Valor (R$)", min_value=0.0, step=100.0)
    submitted = st.form_submit_button("➕ Adicionar despesa")

    if submitted and nome:
        adicionar_despesa(nome, valor)
        st.success(f"Despesa '{nome}' adicionada!")
        st.rerun()

# Exibição e edição da lista de despesas
st.markdown("### 🧾 Despesas Cadastradas")
total = 0.0
for _, row in df_despesas.iterrows():
    id_despesa = row["id"]
    col1, col2, col3 = st.columns([3, 2, 1])
    novo_nome = col1.text_input("Categoria", value=row["nome"], key=f"nome_{id_despesa}")
    novo_valor = col2.number_input("Valor (R$)", value=float(row["valor"]), min_value=0.0, step=100.0, key=f"valor_{id_despesa}")
    total += novo_valor

    if novo_nome != row["nome"] or float(novo_valor) != float(row["valor"]):
        atualizar_despesa(id_despesa, nome=novo_nome, valor=novo_valor)

    if col3.button("🗑️ Remover", key=f"remove_{id_despesa}"):
        excluir_despesa(id_despesa)
        st.rerun()

# Mostrar total
st.markdown("---")
st.subheader(f"💵 Total de despesas fixas: R$ {total:,.2f}")
st.session_state["custo_fixo_inicial"] = total
st.info("Esse valor será usado como custo fixo inicial no simulador financeiro.")
