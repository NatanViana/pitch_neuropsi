import streamlit as st

st.set_page_config(page_title="Despesas Globais", layout="wide")
st.title("💰 Cadastro de Despesas Globais da Clínica")

# Inicializar lista de despesas se não existir
if "despesas" not in st.session_state:
    st.session_state.despesas = []

# Formulário para adicionar nova despesa
with st.form("form_add_despesa", clear_on_submit=True):
    col1, col2 = st.columns([2, 1])
    nome = col1.text_input("Nome da despesa")
    valor = col2.number_input("Valor (R$)", min_value=0.0, step=100.0)
    submitted = st.form_submit_button("➕ Adicionar despesa")

    if submitted and nome:
        st.session_state.despesas.append({"nome": nome, "valor": valor})
        st.success(f"Despesa '{nome}' adicionada!")

# Exibição e edição da lista de despesas
st.markdown("### 🧾 Despesas Cadastradas")
total = 0.0
for i, item in enumerate(st.session_state.despesas):
    col1, col2, col3 = st.columns([3, 2, 1])
    col1.text_input("Categoria", value=item["nome"], key=f"nome_{i}", disabled=True)
    novo_valor = col2.number_input("Valor (R$)", value=item["valor"], min_value=0.0, step=100.0, key=f"valor_{i}")
    st.session_state.despesas[i]["valor"] = novo_valor
    total += novo_valor
    if col3.button("🗑️ Remover", key=f"remove_{i}"):
        st.session_state.despesas.pop(i)
        st.rerun()

# Mostrar total
st.markdown("---")
st.subheader(f"💵 Total de despesas fixas: R$ {total:,.2f}")

# Armazena o total como custo fixo inicial para uso no simulador
st.session_state["custo_fixo_inicial"] = total

st.info("Esse valor será usado como custo fixo inicial no simulador financeiro.")