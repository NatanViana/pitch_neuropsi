from functions import listar_tarefas, adicionar_tarefa, atualizar_tarefa, criar_tabela_plano_estrategico, atualizar_titulo_categoria, criar_tabela_categorias, criar_tabela_responsaveis, seed_categorias_e_responsaveis, adicionar_categoria, adicionar_responsavel, listar_categorias, listar_responsaveis

from datetime import datetime, date
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Dashboard da Clínica", layout="wide")
st.title("💾 Painel de Acompanhamento do Planejamento")

criar_tabela_plano_estrategico()
criar_tabela_categorias()
criar_tabela_responsaveis()

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

st.markdown("### 📚 Cadastros")
with st.expander("📚 Cadastros", expanded=False):

    col_cat, col_resp = st.columns(2)

    with col_cat:
        st.subheader("📁 Nova categoria")
        with st.form("form_nova_categoria", clear_on_submit=True):
            nome_cat = st.text_input("Nome da categoria")
            ok_cat = st.form_submit_button("Salvar categoria")
            if ok_cat:
                if nome_cat.strip():
                    adicionar_categoria(nome_cat.strip())
                    st.success("✅ Categoria adicionada!")
                    st.rerun()
                else:
                    st.warning("Informe um nome.")

    with col_resp:
        st.subheader("👤 Novo responsável")
        with st.form("form_novo_responsavel", clear_on_submit=True):
            nome_resp = st.text_input("Nome do responsável")
            ok_resp = st.form_submit_button("Salvar responsável")
            if ok_resp:
                if nome_resp.strip():
                    adicionar_responsavel(nome_resp.strip())
                    st.success("✅ Responsável adicionado!")
                    st.rerun()
                else:
                    st.warning("Informe um nome.")

    # 🔼 Formulário de nova tarefa (fora das abas)
    st.markdown("### ➕ Adicionar nova tarefa")
    with st.form("form_nova_tarefa"):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            df_cats = listar_categorias()
            opcoes_cat = df_cats["nome"].tolist()
            nova_cat = st.selectbox(
                "📁 Categoria",
                options=opcoes_cat,
                index=0 if opcoes_cat else None,
                placeholder="Selecione..."
            )
        with col_b:
            nova_tarefa = st.text_input("📝 Nome da Tarefa")
        with col_c:
            nova_data = st.date_input("📅 Data limite", value=date.today())

        # 👥 Responsáveis (multiselect)
        df_resps = listar_responsaveis()
        opcoes_resp = df_resps["nome"].tolist()
        responsaveis_sel = st.multiselect(
            "👥 Responsáveis",
            options=opcoes_resp,
            default=[],
            placeholder="Selecione um ou mais responsáveis..."
        )

        submitted = st.form_submit_button("Salvar Tarefa")

        if submitted:
            if nova_cat and nova_tarefa:
                adicionar_tarefa(
                    categoria=nova_cat,
                    tarefa=nova_tarefa,
                    status="PENDENTE",
                    data_limite=nova_data,
                    responsaveis=", ".join(responsaveis_sel)  # <-- salva como texto
                )
                st.success("✅ Tarefa adicionada!")
                st.rerun()
            else:
                st.warning("Preencha todos os campos para adicionar.")


# 🔽 Abas principais
aba1, aba2 = st.tabs(["📜 Planejamento", "👥 Resumo por Responsável"])

with aba1:
    st.header("📜 Tarefas por Categoria")
    df_db = listar_tarefas()

    df_resps = listar_responsaveis()
    responsaveis_disponiveis = df_resps["nome"].tolist()
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ Concluídas", sum(df_db["status"] == "OK"))
    with col2:
        st.metric("⚠️ Pendentes", sum(df_db["status"] == "PENDENTE"))
    with col3:
        st.metric("🚨 Urgentes", sum(df_db["status"] == "URGENTE"))

    for categoria in sorted(df_db["categoria"].unique()):
        with st.expander(f"📂 {categoria}"):
            # ✅ filtra e prepara para ordenar
            cat_df = df_db[df_db["categoria"] == categoria].copy()

            # garante data válida
            cat_df["data_limite"] = pd.to_datetime(cat_df["data_limite"], errors="coerce").dt.date

            # dias restantes (negativo = atrasado)
            cat_df["dias_restantes"] = cat_df["data_limite"].apply(
                lambda d: (d - date.today()).days if pd.notnull(d) else 999999
            )

            # 0 = pendente/urgente, 1 = OK (assim OK vai para o final)
            cat_df["status_order"] = (cat_df["status"] == "OK").astype(int)

            # 🔽 ordenação: primeiro pendentes/urgentes; dentro deles, mais atrasados primeiro,
            # depois os que estão por vencer (dias_restantes crescendo). OK ficam no final.
            cat_df = cat_df.sort_values(
                by=["status_order", "dias_restantes", "data_limite"],
                ascending=[True, True, True]
            )

            total_cat = len(cat_df)
            concluidas = sum(cat_df["status"] == "OK")
            progresso = int((concluidas / total_cat) * 100) if total_cat else 0
            st.progress(progresso / 100, f"{progresso}% concluído ({concluidas}/{total_cat})")

            for _, row in cat_df.iterrows():
                with st.form(f"form_tarefa_{row['id']}"):
                    tarefa_id = row["id"]
                    # já está convertido acima; se vier NaT, usa hoje
                    parsed_date = row["data_limite"] if isinstance(row["data_limite"], date) else date.today()
                    dias_restantes = int(row["dias_restantes"])

                    dias_restantes = (parsed_date - date.today()).days

                    col1, col2, col3, col4, col5, col6, col7 = st.columns([4, 2, 2, 2, 1.3, 1.5, 0.5])
                    with col1:
                        novo_titulo = st.text_input("📝 Tarefa", value=row["tarefa"], key=f"t_{tarefa_id}")
                    with col2:
                        st.text_input(
                            "📁 Categoria",
                            value=row["categoria"],
                            key=f"cat_{tarefa_id}",
                            disabled=True
                        )
                        nova_categoria = row["categoria"]  # mantém compatibilidade com o resto do código
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
                        st.markdown("Check")
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
                        if st.form_submit_button("🗑️"):
                            from functions import excluir_tarefa
                            excluir_tarefa(tarefa_id)
                            st.rerun()

                    alterou = (
                        row["tarefa"] != novo_titulo
                        or row["categoria"] != nova_categoria
                        or row["status"] != novo_status
                        or row["responsaveis"] != responsaveis_txt
                        or str(row["data_limite"]) != data_limite.isoformat()
                    )

                    if st.form_submit_button("📂 Atualizar"):
                        if alterou:
                            atualizar_tarefa(tarefa_id, novo_status, data_limite, responsaveis_txt)
                            atualizar_titulo_categoria(tarefa_id, novo_titulo, nova_categoria)
                            st.success(f"🔄 Atualizado: {novo_titulo}")
                            st.rerun()

with aba2:
    st.header("📌 Tarefas Pendentes por Responsável")
    df_db = listar_tarefas()
    pendentes_df = df_db[df_db["status"] != "OK"].copy()
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
