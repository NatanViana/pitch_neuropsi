from functions import listar_tarefas, adicionar_tarefa, atualizar_tarefa, criar_tabela_plano_estrategico, atualizar_titulo_categoria
from datetime import datetime, date
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard da Clínica", layout="wide")
st.title("🧾 Painel de Acompanhamento do Planejamento")
# Garante que a largura seja total
st.markdown("""
    <style>
    section.main > div { max-width: 100% !important; }
    .stTabs [data-baseweb="tab-list"] {
        justify-content: stretch;
    }
    .stTabs [data-baseweb="tab"] {
        flex: 1;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)
aba1, aba2 = st.tabs(["📋 Planejamento", "👥 Resumo por Responsável"])

with aba1:
    
    

    # Inicializa banco e dados
    criar_tabela_plano_estrategico()
    df_db = listar_tarefas()

    # Responsáveis disponíveis
    responsaveis_disponiveis = ["Noélia", "Luiza", "Advogado", "Contador", "Arquiteta", "Natan", "Ulisses"]

    # Função para verificar se já existe
    def tarefa_existe(tarefa, categoria):
        return not df_db[(df_db["tarefa"] == tarefa) & (df_db["categoria"] == categoria)].empty

    # Métricas superiores em 3 colunas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ Concluídas", sum(df_db["status"] == "OK"))
    with col2:
        st.metric("⚠️ Pendentes", sum(df_db["status"] == "PENDENTE"))
    with col3:
        st.metric("🚨 Urgentes", sum(df_db["status"] == "URGENTE"))

    # Botão para nova tarefa
    with st.expander("➕ Adicionar nova tarefa"):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            nova_cat = st.text_input("📁 Categoria")
        with col_b:
            nova_tarefa = st.text_input("📝 Nome da Tarefa")
        with col_c:
            nova_data = st.date_input("📅 Data limite", value=date.today())

        if st.button("Salvar Tarefa"):
            if nova_cat and nova_tarefa:
                adicionar_tarefa(
                    categoria=nova_cat,
                    tarefa=nova_tarefa,
                    status="PENDENTE",
                    data_limite=nova_data,
                    responsaveis=""
                )
                st.success("✅ Tarefa adicionada!")
                st.experimental_rerun()
            else:
                st.warning("Preencha todos os campos para adicionar.")

    # Agrupamento e exibição por categoria
    for categoria in sorted(df_db["categoria"].unique()):
        with st.expander(f"📂 {categoria}"):
            cat_df = df_db[df_db["categoria"] == categoria]

            total_cat = len(cat_df)
            concluidas = sum(cat_df["status"] == "OK")
            progresso = int((concluidas / total_cat) * 100) if total_cat else 0
            st.progress(progresso / 100, f"{progresso}% concluído ({concluidas}/{total_cat})")

            for _, row in cat_df.iterrows():
                tarefa_id = row["id"]
                tarefa = row["tarefa"]

                # Tentativa de parse da data
                try:
                    parsed_date = datetime.strptime(str(row["data_limite"]).replace("‑", "-").replace("–", "-"), "%Y-%m-%d").date()
                except ValueError:
                    parsed_date = date.today()

                dias_restantes = (parsed_date - date.today()).days

                col1, col2, col3, col4, col5, col6, col7 = st.columns([4, 2, 2, 2, 1.3, 1.5, 0.5])

                with col1:
                    novo_titulo = st.text_input("📝 Tarefa", value=row["tarefa"], key=f"t_{tarefa_id}")
                with col2:
                    nova_categoria = st.text_input("📁 Categoria", value=row["categoria"], key=f"cat_{tarefa_id}")
                with col3:
                    responsaveis_selecionados = st.multiselect(
                        "Responsáveis",
                        responsaveis_disponiveis,
                        default=row["responsaveis"].split(", ") if row["responsaveis"] else [],
                        key=f"resp_{tarefa_id}"
                    )
                    responsaveis_txt = ", ".join(responsaveis_selecionados)
                with col4:
                    data_limite = st.date_input("📆 Data limite", value=parsed_date, key=f"date_{tarefa_id}")

                with col5:
                    st.markdown("Feita")
                    status_val = "OK" if row["status"] == "OK" else ("URGENTE" if dias_restantes < 0 else "PENDENTE")
                    checked = st.checkbox("", value=(status_val == "OK"), key=f"chk_{tarefa_id}")
                    novo_status = "OK" if checked else ("URGENTE" if dias_restantes < 0 else "PENDENTE")

                with col6:
                    if novo_status == "OK":
                        st.success("✅ Concluído")
                    elif dias_restantes < 0:
                        st.error(f"🚨 {-dias_restantes}d atraso")
                    elif dias_restantes <= 3:
                        st.warning(f"⚠️ {dias_restantes}d")
                    else:
                        st.success(f"⏳ {dias_restantes}d")

                with col7:
                    if st.button("🗑️", key=f"del_{tarefa_id}"):
                        from functions import excluir_tarefa
                        excluir_tarefa(tarefa_id)
                        st.warning(f"Tarefa removida: {tarefa}")
                        st.experimental_rerun()

                # Verifica se houve mudança
                alterou = (
                    row["tarefa"] != novo_titulo
                    or row["categoria"] != nova_categoria
                    or row["status"] != novo_status
                    or row["responsaveis"] != responsaveis_txt
                    or str(row["data_limite"]) != data_limite.isoformat()
                )

                if alterou:
                    atualizar_tarefa(tarefa_id, novo_status, data_limite, responsaveis_txt)
                    atualizar_titulo_categoria(tarefa_id, novo_titulo, nova_categoria)
                    st.success(f"🔄 Atualizado: {novo_titulo}")

with aba2:
    st.header("📌 Tarefas Pendentes por Responsável")

    # Recarrega dados do banco antes de gerar o resumo
    df_db = listar_tarefas()

    # Filtra tarefas não concluídas
    pendentes_df = df_db[df_db["status"] != "OK"].copy()

    # Explode lista de responsáveis
    pendentes_df["responsaveis"] = pendentes_df["responsaveis"].fillna("")
    pendentes_df["responsaveis"] = pendentes_df["responsaveis"].apply(lambda x: [r.strip() for r in x.split(",") if r.strip()])
    pendentes_exploded = pendentes_df.explode("responsaveis")

    if pendentes_exploded.empty:
        st.success("🎉 Nenhuma tarefa pendente ou urgente!")
    else:
        for responsavel in sorted(pendentes_exploded["responsaveis"].dropna().unique()):
            with st.expander(f"👤 {responsavel}"):
                tarefas = pendentes_exploded[
                    pendentes_exploded["responsaveis"] == responsavel
                ][["categoria", "tarefa", "status", "data_limite"]].sort_values(by="data_limite")

                for _, row in tarefas.iterrows():
                    status_emoji = "⚠️" if row["status"] == "PENDENTE" else "🚨"
                    st.markdown(
                        f"- **[{row['categoria']}]** {row['tarefa']} — `{row['data_limite']}` {status_emoji}"
                )