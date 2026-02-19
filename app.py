import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from functions import get_mysql_conn

st.set_page_config(page_title="Simulador Clínico", layout="wide")
st.title("📊 Simulador Financeiro de Clínica")


# =========================
# DB: Despesas
# =========================
def carregar_despesas() -> pd.DataFrame:
    with get_mysql_conn() as conn:
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM despesas ORDER BY id")
            return pd.DataFrame(cursor.fetchall())


df_despesas = carregar_despesas()
if df_despesas.empty:
    df_despesas = pd.DataFrame(columns=["id", "nome", "valor", "mes_inicio", "duracao_meses"])


def despesa_ativa_no_mes(row: dict, mes: int) -> bool:
    inicio = int(row.get("mes_inicio", 1) or 1)
    dur = row.get("duracao_meses", None)

    # NULL = infinito
    if dur is None or (isinstance(dur, float) and pd.isna(dur)):
        return mes >= inicio

    dur = int(dur)
    fim = inicio + dur - 1
    return inicio <= mes <= fim


def soma_por_nome(df: pd.DataFrame, mes: int, nome_exato: str) -> float:
    if df is None or df.empty:
        return 0.0
    total = 0.0
    alvo = nome_exato.strip().upper()
    for _, r in df.iterrows():
        nome = str(r.get("nome", "")).strip().upper()
        if nome == alvo and despesa_ativa_no_mes(r, mes):
            total += float(r.get("valor", 0) or 0)
    return float(total)


def soma_operacional(df: pd.DataFrame, mes: int, nomes_excluir: set[str]) -> float:
    if df is None or df.empty:
        return 0.0
    total = 0.0
    for _, r in df.iterrows():
        nome = str(r.get("nome", "")).strip().upper()
        if nome in nomes_excluir:
            continue
        if despesa_ativa_no_mes(r, mes):
            total += float(r.get("valor", 0) or 0)
    return float(total)


# nomes “financeiros” que queremos acompanhar separadamente
NOMES_FINANCEIROS = {"PRONAMPE", "BB GIRO 1", "BB GIRO 2", "INVESTIDOR"}


def highlight_negatives(val):
    return "color: red;" if val < 0 else ""


# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.header("🔢 Parâmetros Financeiros")

    valor_sessao = st.number_input("Valor de cada sessão (R$)", min_value=1.0, value=300.0)
    porcent_clinica = (
        st.number_input("% da sessão para a clínica", min_value=0.0, max_value=100.0, value=60.0) / 100
    )
    base_imposto = st.selectbox("Imposto incide sobre:", ["Total do faturamento", "Apenas % da clínica"])
    porcent_imposto = st.number_input("% de imposto", min_value=0.0, max_value=100.0, value=15.0) / 100

    st.markdown("---")
    st.header("Montante Saúde Inicial")
    investimento_inicial_saude = st.number_input("Montante Inicial de Saúde Financeira", min_value=0, value=0)

    st.markdown("---")
    st.header("💸 Investidor")
    investidor_inicio_mes = st.number_input("Mês de início do pagamento ao investidor", min_value=1, value=8)
    st.caption("O valor mensal do investidor vem da despesa 'INVESTIDOR' no cadastro de despesas.")

    st.markdown("---")
    st.header("📅 Início da Clínica")
    meses_sem_funcionar = st.number_input("Meses de aluguel antes de operar", min_value=0, max_value=60, value=0)
    clientes_iniciais = st.number_input("Clientes iniciais (mês 1 após início)", min_value=0, value=15)

    st.markdown("---")
    st.header("👩‍⚕️ Psicólogas")
    opcao_teto = st.selectbox("Sessões consideradas no teto:", ["Nenhuma", "Apenas Luiza", "Luiza e Noelia"])
    st.caption("ℹ️ Apenas Luiza ocupa salas, e nenhuma psicóloga gera faturamento para a clínica.")

    st.subheader("Luiza")
    luiza_sessoes = st.number_input("Sessões/mês Luiza", min_value=0, value=100)
    luiza_valor_sessao = st.number_input("Valor sessão Luiza (R$)", min_value=0.0, value=300.0)

    st.subheader("Noelia")
    noelia_sessoes = st.number_input("Sessões/mês Noelia", min_value=0, value=150)
    noelia_valor_sessao = st.number_input("Valor sessão Noelia (R$)", min_value=0.0, value=350.0)

    st.markdown("---")
    st.header("⚙️ Operacional")
    dias_uteis = st.number_input("Dias úteis/semana", min_value=1, max_value=7, value=5)
    semanas = st.number_input("Semanas/mês", min_value=1, max_value=5, value=4)
    horas_dia = st.number_input("Horas/dia por sala", min_value=1, max_value=24, value=12)
    num_salas = st.number_input("Nº de salas", min_value=1, value=3)

    st.markdown("---")
    st.header("📈 Projeção")
    clientes_crescimento = st.number_input("Clientes adicionais/mês", min_value=0, value=5)

    st.markdown("---")
    st.header("📌 Expansão da Clínica")
    clientes_por_psicologo = st.number_input("Clientes trazidos por novo psicólogo", min_value=0, value=0)
    capacidade_psicologo = st.number_input("Capacidade de atendimento por psicólogo (clientes/mês)", min_value=1, value=30)


# =========================
# CÁLCULOS INICIAIS
# =========================
receita_clinica_bruta_por_sessao = valor_sessao * porcent_clinica
if base_imposto == "Apenas % da clínica":
    imposto_por_sessao = receita_clinica_bruta_por_sessao * porcent_imposto
else:
    imposto_por_sessao = valor_sessao * porcent_imposto
receita_liquida_por_sessao = receita_clinica_bruta_por_sessao - imposto_por_sessao

tempo_sessao = 1  # horas

total_horas = horas_dia * dias_uteis * semanas * num_salas
horas_ocupadas_luiza = luiza_sessoes * tempo_sessao
horas_ocupadas_noelia = noelia_sessoes * tempo_sessao

if opcao_teto == "Apenas Luiza":
    horas_disponiveis = max(0, total_horas - horas_ocupadas_luiza)
elif opcao_teto == "Luiza e Noelia":
    horas_disponiveis = max(0, total_horas - horas_ocupadas_luiza - horas_ocupadas_noelia)
else:
    horas_disponiveis = total_horas

sessoes_disponiveis = horas_disponiveis / tempo_sessao

# custo fixo do mês 1 (vindo do banco)
mes_ref = 1
custo_operacional_m1 = soma_operacional(df_despesas, mes_ref, NOMES_FINANCEIROS)
pag_pronampe_m1 = soma_por_nome(df_despesas, mes_ref, "PRONAMPE")
pag_bb1_m1 = soma_por_nome(df_despesas, mes_ref, "BB GIRO 1")
pag_bb2_m1 = soma_por_nome(df_despesas, mes_ref, "BB GIRO 2")

pag_invest_db_m1 = soma_por_nome(df_despesas, mes_ref, "INVESTIDOR")
pag_invest_m1 = pag_invest_db_m1 if mes_ref >= investidor_inicio_mes else 0.0

custo_fixo_m1 = custo_operacional_m1 + pag_pronampe_m1 + pag_bb1_m1 + pag_bb2_m1 + pag_invest_m1

sessoes_minimas = custo_fixo_m1 / receita_liquida_por_sessao if receita_liquida_por_sessao > 0 else 0
percent_ocupado = (sessoes_minimas / sessoes_disponiveis) * 100 if sessoes_disponiveis > 0 else 0
clientes_mes = sessoes_minimas / 4 if sessoes_minimas > 0 else 0

faturamento_maximo = sessoes_disponiveis * receita_liquida_por_sessao
# Lucro máximo aqui é “mês 1” só como referência
lucro_maximo = faturamento_maximo - custo_fixo_m1

# =========================
# MÉTRICAS
# =========================
st.header("📌 Indicadores Principais")

# ===== Helpers (explicações) =====
with st.expander("ℹ️ Como esses indicadores são calculados", expanded=False):
    st.markdown(
        f"""
**1) Receita líquida por sessão (para a clínica)**  
- Valor da sessão: **R$ {valor_sessao:,.2f}**  
- % para a clínica: **{porcent_clinica*100:.1f}%** → clínica bruta: **R$ {receita_clinica_bruta_por_sessao:,.2f}**  
- Imposto: **{porcent_imposto*100:.1f}%** (**{base_imposto}**) → imposto por sessão: **R$ {imposto_por_sessao:,.2f}**  
➡️ **Receita líquida por sessão** = **R$ {receita_liquida_por_sessao:,.2f}**

**2) Custo fixo do mês 1 (vindo do banco de despesas)**  
- Operacional (mês 1): **R$ {custo_operacional_m1:,.2f}**  
- PRONAMPE (mês 1): **R$ {pag_pronampe_m1:,.2f}**  
- BB Giro 1 (mês 1): **R$ {pag_bb1_m1:,.2f}**  
- BB Giro 2 (mês 1): **R$ {pag_bb2_m1:,.2f}**  
- Investidor (mês 1): **R$ {pag_invest_m1:,.2f}** *(só conta a partir do mês {investidor_inicio_mes})*  
➡️ **Custo fixo mês 1** = **R$ {custo_fixo_m1:,.2f}**

**3) Sessões mínimas (mês 1)**  
➡️ **Sessões mínimas** = Custo fixo mês 1 ÷ Receita líquida por sessão  
= **R$ {custo_fixo_m1:,.2f} ÷ R$ {receita_liquida_por_sessao:,.2f} = {sessoes_minimas:.0f} sessões**

**4) Sessões disponíveis**  
- Total de horas/mês: **{total_horas:.0f}h**  
- Regra de teto: **{opcao_teto}** → horas disponíveis: **{horas_disponiveis:.0f}h**  
➡️ **Sessões disponíveis** = horas disponíveis ÷ duração da sessão (1h)
"""
    )

# Mini helper inline (pra ficar visível sem abrir o expander)
st.caption(
    "💡 *Dica:* o custo fixo é calculado mês a mês a partir do cadastro de despesas (com início e duração). "
    "Quando um empréstimo acaba, ele sai automaticamente do custo fixo."
)

# ===== Métricas =====
col1, col2, col3 = st.columns(3)

col1.metric(
    "Sessões mínimas (Mês 1)",
    f"{sessoes_minimas:.0f}",
    help="Custo fixo do mês 1 ÷ receita líquida por sessão."
)

col2.metric(
    "Sessões disponíveis",
    int(sessoes_disponiveis),
    help="Capacidade máxima do mês (horas disponíveis ÷ 1h por sessão), considerando o teto escolhido."
)

col3.metric(
    "Capacidade ocupada",
    f"{percent_ocupado:.2f}%",
    help="(Sessões mínimas ÷ sessões disponíveis) × 100."
)

col4, col5, col6 = st.columns(3)

col4.metric(
    "Clientes mínimos/mês",
    f"{clientes_mes:.0f}",
    help="Sessões mínimas ÷ 4 (considerando 4 sessões por cliente por mês)."
)

col5.metric(
    "Faturamento MÁX líquido",
    f"R$ {faturamento_maximo:,.2f}",
    help="Sessões disponíveis × receita líquida por sessão."
)

col6.metric(
    "Lucro MÁX (ref. Mês 1)",
    f"R$ {lucro_maximo:,.2f}",
    help="Faturamento máximo líquido − custo fixo do mês 1 (referência)."
)


# =========================
# SIMULAÇÃO
# =========================
st.header("📊 Projeção de 60 Meses")

data = []
clientes = 0
psicologos_dinamicos = []
lucro_acumulado = 0.0


# acumulados (controle)
pag_pronampe_acum = 0.0
pag_bb1_acum = 0.0
pag_bb2_acum = 0.0
pag_invest_acum = 0.0

max_meses = 60

for mes in range(1, max_meses + 1):
    # custo fixo / pagamentos (sempre calculados via banco)
    custo_operacional = soma_operacional(df_despesas, mes, NOMES_FINANCEIROS)

    pag_pronampe_mes = soma_por_nome(df_despesas, mes, "PRONAMPE")
    pag_bb1_mes = soma_por_nome(df_despesas, mes, "BB GIRO 1")
    pag_bb2_mes = soma_por_nome(df_despesas, mes, "BB GIRO 2")

    pag_invest_db = soma_por_nome(df_despesas, mes, "INVESTIDOR")
    pag_invest_mes = pag_invest_db if mes >= investidor_inicio_mes else 0.0

    custo_fixo = custo_operacional + pag_pronampe_mes + pag_bb1_mes + pag_bb2_mes + pag_invest_mes

    # meses sem operar
    if mes <= meses_sem_funcionar:
        faturamento = 0.0
        lucro = -custo_fixo
        sessoes_mes = 0
        salas_utilizadas = 0
        total_psicologos = 0
        clientes_mes_loop = 0
    else:
        # clínica em operação
        if mes == meses_sem_funcionar + 1:
            clientes = clientes_iniciais
        else:
            clientes += clientes_crescimento

        # expansão por psicólogos (mesma lógica sua)
        capacidade_total = len(psicologos_dinamicos) * capacidade_psicologo * 4
        if clientes * 4 > capacidade_total:
            novos_psicologos = ((clientes * 4 - capacidade_total) // (capacidade_psicologo * 4)) + 1
            for _ in range(novos_psicologos):
                psicologos_dinamicos.append("Novo")
                if mes == meses_sem_funcionar + 1:
                    clientes += clientes_por_psicologo

        total_psicologos = 1 + len(psicologos_dinamicos)  # Luiza + dinâmicos
        clientes_mes_loop = clientes

        # teto de salas
        horas_ocupadas_luiza = luiza_sessoes * tempo_sessao
        horas_ocupadas_noelia = noelia_sessoes * tempo_sessao

        if opcao_teto == "Apenas Luiza":
            horas_disp = max(0, total_horas - horas_ocupadas_luiza)
        elif opcao_teto == "Luiza e Noelia":
            horas_disp = max(0, total_horas - horas_ocupadas_luiza - horas_ocupadas_noelia)
        else:
            horas_disp = total_horas

        sessoes_disp = horas_disp / tempo_sessao
        sessoes_mes = min(clientes * 4, sessoes_disp)

        faturamento = sessoes_mes * receita_liquida_por_sessao
        lucro = faturamento - custo_fixo

        salas_utilizadas = min(
            num_salas,
            int((horas_ocupadas_luiza + sessoes_mes) / (horas_dia * dias_uteis * semanas)) + 1,
        )

    # acumulados
    pag_pronampe_acum += pag_pronampe_mes
    pag_bb1_acum += pag_bb1_mes
    pag_bb2_acum += pag_bb2_mes
    pag_invest_acum += pag_invest_mes

    lucro_acumulado += lucro
    montante_saude = investimento_inicial_saude + lucro_acumulado

    data.append(
        {
            "Mês": mes,
            "Clientes": clientes_mes_loop,
            "Psicólogos": total_psicologos,
            "Salas Usadas": salas_utilizadas,
            "Sessões": sessoes_mes,
            "Custo Operacional (R$)": round(custo_operacional, 2),
            "Pagamento Investidor (mês) (R$)": round(pag_invest_mes, 2),
            "Pagamento PRONAMPE (mês) (R$)": round(pag_pronampe_mes, 2),
            "Pagamento BB Giro 1 (mês) (R$)": round(pag_bb1_mes, 2),
            "Pagamento BB Giro 2 (mês) (R$)": round(pag_bb2_mes, 2),
            "Custo Fixo Total (R$)": round(custo_fixo, 2),
            "Faturamento (R$)": round(faturamento, 2),
            "Lucro (R$)": round(lucro, 2),
            "Montante de Saúde (R$)": round(montante_saude, 2),
            "Investidor (acum) (R$)": round(pag_invest_acum, 2),
            "PRONAMPE (acum) (R$)": round(pag_pronampe_acum, 2),
            "BB Giro 1 (acum) (R$)": round(pag_bb1_acum, 2),
            "BB Giro 2 (acum) (R$)": round(pag_bb2_acum, 2),
        }
    )

df = pd.DataFrame(data)


# =========================
# TABELA
# =========================
st.dataframe(
    df.style.format(
        {
            "Custo Operacional (R$)": "R$ {:,.2f}",
            "Pagamento Investidor (mês) (R$)": "R$ {:,.2f}",
            "Pagamento PRONAMPE (mês) (R$)": "R$ {:,.2f}",
            "Pagamento BB Giro 1 (mês) (R$)": "R$ {:,.2f}",
            "Pagamento BB Giro 2 (mês) (R$)": "R$ {:,.2f}",
            "Custo Fixo Total (R$)": "R$ {:,.2f}",
            "Faturamento (R$)": "R$ {:,.2f}",
            "Lucro (R$)": "R$ {:,.2f}",
            "Montante de Saúde (R$)": "R$ {:,.2f}",
            "Investidor (acum) (R$)": "R$ {:,.2f}",
            "PRONAMPE (acum) (R$)": "R$ {:,.2f}",
            "BB Giro 1 (acum) (R$)": "R$ {:,.2f}",
            "BB Giro 2 (acum) (R$)": "R$ {:,.2f}",
        }
    ).applymap(highlight_negatives, subset=["Lucro (R$)", "Montante de Saúde (R$)"]),
    use_container_width=True,
)


# =========================
# ANÁLISES
# =========================
st.header("📍 Análises de Investimento")
meses_montante_positivo = df[df["Montante de Saúde (R$)"] >= 0].shape[0]
montante_quitacao = st.number_input("Valor Breakeven", min_value=0, value=250000)
ponto_quitacao = df[df["Montante de Saúde (R$)"] >= montante_quitacao]
mes_quitacao = int(ponto_quitacao["Mês"].iloc[0]) if not ponto_quitacao.empty else None

col1, col2 = st.columns(2)
col1.metric("Meses com saldo positivo", f"{meses_montante_positivo}")
col2.metric(f"Quitação R${montante_quitacao}", f"Mês {mes_quitacao}" if mes_quitacao else "Não atingido")


# =========================
# GRÁFICOS
# =========================
st.subheader("📈 Evolução do Montante de Saúde")
fig_montante = go.Figure()
fig_montante.add_trace(
    go.Scatter(x=df["Mês"], y=df["Montante de Saúde (R$)"], mode="lines+markers")
)
fig_montante.add_hline(
    y=200000,
    line=dict(color="red", dash="dash"),
    annotation_text="Meta: R$200.000",
    annotation_position="top right",
)
fig_montante.update_layout(
    title="Montante de Saúde", xaxis_title="Mês", yaxis_title="R$", template="plotly_white"
)
st.plotly_chart(fig_montante, use_container_width=True)

st.subheader("📉 Lucro Mensal")
fig_lucro = px.bar(df, x="Mês", y="Lucro (R$)", title="Lucro Mensal", color_discrete_sequence=["green"])
fig_lucro.add_hline(y=0, line_dash="dash", line_color="black")
fig_lucro.update_layout(template="plotly_white")
st.plotly_chart(fig_lucro, use_container_width=True)


# =========================
# SALÁRIOS (mantido como estava)
# =========================
st.header("💼 Salários das Psicólogas")
percent_simples = porcent_imposto
salario_fixo_luiza = luiza_sessoes * luiza_valor_sessao * (1 - percent_simples)
salario_fixo_noelia = noelia_sessoes * noelia_valor_sessao * (1 - percent_simples)

df_sal = df[["Mês", "Lucro (R$)"]].copy()
df_sal["Salário Luiza (R$)"] = 0.0
df_sal["Salário Noelia (R$)"] = 0.0

st.markdown(f"**💰 Salário Base Luiza:** R$ {salario_fixo_luiza:,.2f}")
st.markdown(f"**💰 Salário Base Noelia:** R$ {salario_fixo_noelia:,.2f}")

for i, row in df_sal.iterrows():
    lucro = row["Lucro (R$)"]
    participacao = lucro * 0.5 if lucro > 0 else 0
    df_sal.at[i, "Salário Luiza (R$)"] = salario_fixo_luiza + participacao
    df_sal.at[i, "Salário Noelia (R$)"] = salario_fixo_noelia + participacao

st.dataframe(
    df_sal.style.format(
        {
            "Lucro (R$)": "R$ {:,.2f}",
            "Salário Luiza (R$)": "R$ {:,.2f}",
            "Salário Noelia (R$)": "R$ {:,.2f}",
        }
    ).applymap(highlight_negatives, subset=["Lucro (R$)"]),
    use_container_width=True,
)


# =========================
# RESUMO FINAL
# =========================
st.subheader("📋 Resumo do Plano de Expansão")
st.markdown(
    f"""
- Clientes no último mês: **{df['Clientes'].iloc[-1]}**
- Psicólogos totais: **{df['Psicólogos'].iloc[-1]} (Incluindo Luiza)**
- Salas utilizadas: **{df['Salas Usadas'].iloc[-1]} / {num_salas}**
- Crescimento mensal de clientes: **{clientes_crescimento}**
- Cada novo psicólogo traz **{clientes_por_psicologo}** clientes e atende até **{capacidade_psicologo}**.
"""
)
