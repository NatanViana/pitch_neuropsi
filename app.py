import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Simulador Clínico", layout="wide")
st.title("📊 Simulador Financeiro de Clínica")

# ==== SIDEBAR ====
with st.sidebar:
    st.header("🔢 Parâmetros Financeiros")
    valor_padrao_custo = st.session_state.get("custo_fixo_inicial", 16200.0)
    custo_fixo_inicial = st.number_input("Custo fixo inicial (R$)", min_value=0.0, value=valor_padrao_custo, key="simulador_custo_fixo")

    valor_sessao = st.number_input("Valor de cada sessão (R$)", min_value=1.0, value=300.0)
    porcent_clinica = st.number_input("% da sessão para a clínica", min_value=0.0, max_value=100.0, value=60.0) / 100
    porcent_imposto = st.number_input("% de imposto sobre a clínica", min_value=0.0, max_value=100.0, value=20.0) / 100

    st.markdown("---")
    st.header("📅 Início da Clínica")
    meses_sem_funcionar = st.number_input("Meses de aluguel antes de operar", min_value=0, max_value=60, value=0)
    clientes_iniciais = st.number_input("Clientes iniciais (mês 1 após início)", min_value=0, value=0)

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
    clientes_por_psicologo = st.number_input("Clientes trazidos por novo psicólogo", min_value=0, value=20)
    capacidade_psicologo = st.number_input("Capacidade de atendimento por psicólogo (clientes/mês)", min_value=1, value=40)
                                           
# ==== FUNÇÕES AUXILIARES ====
def calcular_custo_fixo(mes):
    if mes <= 6:
        return custo_fixo_inicial
    elif mes <= 12:
        return custo_fixo_inicial + 2000
    else:
        return custo_fixo_inicial + 7000

def highlight_negatives(val):
    return 'color: red;' if val < 0 else ''

# ==== CÁLCULOS INICIAIS ====
receita_liquida_por_sessao = valor_sessao * porcent_clinica * (1 - porcent_imposto)
tempo_sessao = 1  # duração da sessão em horas

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
sessoes_minimas = calcular_custo_fixo(1) / receita_liquida_por_sessao

percent_ocupado = (sessoes_minimas / sessoes_disponiveis) * 100 if sessoes_disponiveis > 0 else 0
clientes_mes = sessoes_minimas / 4
faturamento_maximo = sessoes_disponiveis * receita_liquida_por_sessao
lucro_maximo = faturamento_maximo - calcular_custo_fixo(13)

# ==== MÉTRICAS ====
st.header("📌 Indicadores Principais")
col1, col2, col3 = st.columns(3)
col1.metric("Sessões mínimas (Mês 1)", f"{sessoes_minimas:.0f}")
col2.metric("Sessões disponíveis", int(sessoes_disponiveis))
col3.metric("Capacidade ocupada", f"{percent_ocupado:.2f}%")

col4, col5, col6 = st.columns(3)
col4.metric("Clientes mínimos/mês", f"{clientes_mes:.0f}")
col5.metric("Faturamento MÁX liquido", f"R$ {faturamento_maximo:,.2f}")
col6.metric("Lucro MÁX liquido", f"R$ {lucro_maximo:,.2f}")

# ==== SIMULAÇÃO ====
st.header("📊 Projeção de 60 Meses")

data = []
clientes = 0
psicologos_dinamicos = []
lucro_acumulado = 0
pagamento_investidor_acumulado = 0
investimento_inicial_saude = 50000.0
max_meses = 60

for mes in range(1, max_meses + 1):
    # Meses em que a clínica ainda não está operando
    if mes <= meses_sem_funcionar:
        custo_fixo = 10000.0
        faturamento = 0.0
        lucro = -custo_fixo
        pagamento_investidor_mes = 0
        pagamento_investidor_acumulado += pagamento_investidor_mes
        lucro_acumulado += lucro
        montante_saude = investimento_inicial_saude + lucro_acumulado

        data.append({
            "Mês": mes,
            "Clientes": 0,
            "Psicólogos": 0,
            "Salas Usadas": 0,
            "Sessões": 0,
            "Custo Fixo (R$)": custo_fixo,
            "Faturamento (R$)": faturamento,
            "Lucro (R$)": lucro,
            "Montante de Saúde (R$)": montante_saude,
            "Pagamento ao Investidor (R$)": pagamento_investidor_acumulado
        })
        continue  # pula para o próximo mês

    # Clínica em operação
    if mes == meses_sem_funcionar + 1:
        clientes = clientes_iniciais
    else:
        clientes += clientes_crescimento

    custo_fixo = calcular_custo_fixo(mes)

    capacidade_total = len(psicologos_dinamicos) * capacidade_psicologo * 4
    if clientes * 4 > capacidade_total:
        novos_psicologos = ((clientes * 4 - capacidade_total) // (capacidade_psicologo * 4)) + 1
        for _ in range(novos_psicologos):
            psicologos_dinamicos.append("Novo")
            if mes == meses_sem_funcionar + 1:
                clientes += clientes_por_psicologo

    total_psicologos = 1 + len(psicologos_dinamicos)  # Luiza + dinâmicos

    horas_ocupadas_luiza = luiza_sessoes * tempo_sessao
    horas_ocupadas_noelia = noelia_sessoes * tempo_sessao

    if opcao_teto == "Apenas Luiza":
        horas_disponiveis = max(0, total_horas - horas_ocupadas_luiza)
    elif opcao_teto == "Luiza e Noelia":
        horas_disponiveis = max(0, total_horas - horas_ocupadas_luiza - horas_ocupadas_noelia)
    else:
        horas_disponiveis = total_horas

    sessoes_disponiveis = horas_disponiveis / tempo_sessao
    sessoes_mes = min(clientes * 4, sessoes_disponiveis)

    faturamento = sessoes_mes * receita_liquida_por_sessao
    lucro = faturamento - custo_fixo
    pagamento_investidor_mes = 5000 if mes >= 13 else 0
    pagamento_investidor_acumulado += pagamento_investidor_mes
    lucro_acumulado += lucro
    montante_saude = investimento_inicial_saude + lucro_acumulado

    salas_utilizadas = min(num_salas, int((horas_ocupadas_luiza + sessoes_mes) / (horas_dia * dias_uteis * semanas)) + 1)

    data.append({
        "Mês": mes,
        "Clientes": clientes,
        "Psicólogos": total_psicologos,
        "Salas Usadas": salas_utilizadas,
        "Sessões": sessoes_mes,
        "Custo Fixo (R$)": custo_fixo,
        "Faturamento (R$)": round(faturamento, 2),
        "Lucro (R$)": round(lucro, 2),
        "Montante de Saúde (R$)": round(montante_saude, 2),
        "Pagamento ao Investidor (R$)": pagamento_investidor_acumulado
    })

    if sessoes_mes >= sessoes_disponiveis:
        break

df = pd.DataFrame(data)

# ==== TABELA ====
st.dataframe(
    df.style.format({
        "Custo Fixo (R$)": "R$ {:,.2f}",
        "Faturamento (R$)": "R$ {:,.2f}",
        "Lucro (R$)": "R$ {:,.2f}",
        "Montante de Saúde (R$)": "R$ {:,.2f}",
        "Pagamento ao Investidor (R$)": "R$ {:,.2f}"
    }).applymap(highlight_negatives, subset=["Lucro (R$)", "Montante de Saúde (R$)"]),
    use_container_width=True
)

# ==== ANÁLISES ====
st.header("📍 Análises de Investimento")
meses_montante_positivo = df[df["Montante de Saúde (R$)"] >= 0].shape[0]
ponto_quitacao = df[df["Montante de Saúde (R$)"] >= 200000]
mes_quitacao = int(ponto_quitacao["Mês"].iloc[0]) if not ponto_quitacao.empty else None

col1, col2 = st.columns(2)
col1.metric("Meses com saldo positivo", f"{meses_montante_positivo}")
col2.metric("Quitação R$200mil", f"Mês {mes_quitacao}" if mes_quitacao else "Não atingido")

# ==== GRÁFICOS ====
st.subheader("📈 Evolução do Montante de Saúde")
fig_montante = go.Figure()
fig_montante.add_trace(go.Scatter(x=df["Mês"], y=df["Montante de Saúde (R$)"], mode='lines+markers'))
fig_montante.add_hline(y=200000, line=dict(color='red', dash='dash'), annotation_text="Meta: R$200.000", annotation_position="top right")
fig_montante.update_layout(title="Montante de Saúde", xaxis_title="Mês", yaxis_title="R$", template="plotly_white")
st.plotly_chart(fig_montante, use_container_width=True)

st.subheader("📉 Lucro Mensal")
fig_lucro = px.bar(df, x="Mês", y="Lucro (R$)", title="Lucro Mensal", color_discrete_sequence=["green"])
fig_lucro.add_hline(y=0, line_dash="dash", line_color="black")
fig_lucro.update_layout(template="plotly_white")
st.plotly_chart(fig_lucro, use_container_width=True)

# ==== SALÁRIOS ====
st.header("💼 Salários das Psicólogas")
percent_simples = porcent_imposto
salario_fixo_luiza = luiza_sessoes * luiza_valor_sessao * (1 - percent_simples)
salario_fixo_noelia = noelia_sessoes * noelia_valor_sessao * (1 - percent_simples)

df["Salário Luiza (R$)"] = 0.0
df["Salário Noelia (R$)"] = 0.0

# Exibe os salários fixos no topo
st.markdown(f"**💰 Salário Base Luiza:** R$ {salario_fixo_luiza:,.2f}")
st.markdown(f"**💰 Salário Base Noelia:** R$ {salario_fixo_noelia:,.2f}")

for i, row in df.iterrows():
    lucro = row["Lucro (R$)"]
    participacao = lucro * 0.5 if lucro > 0 else 0
    df.at[i, "Salário Luiza (R$)"] = salario_fixo_luiza + participacao
    df.at[i, "Salário Noelia (R$)"] = salario_fixo_noelia + participacao

st.dataframe(
    df[["Mês", "Lucro (R$)", "Salário Luiza (R$)", "Salário Noelia (R$)"]].style.format({
        "Lucro (R$)": "R$ {:,.2f}",
        "Salário Luiza (R$)": "R$ {:,.2f}",
        "Salário Noelia (R$)": "R$ {:,.2f}",
    }).applymap(highlight_negatives, subset=["Lucro (R$)"]),
    use_container_width=True
)

# ==== RESUMO FINAL ====
st.subheader("📋 Resumo do Plano de Expansão")
st.markdown(f"""
- Clientes no último mês: **{df['Clientes'].iloc[-1]}**
- Psicólogos totais: **{df['Psicólogos'].iloc[-1]} (Incluindo Luiza)**
- Salas utilizadas: **{df['Salas Usadas'].iloc[-1]} / {num_salas}**
- Crescimento mensal de clientes: **{clientes_crescimento}**
- Cada novo psicólogo traz **{clientes_por_psicologo}** clientes e atende até **{capacidade_psicologo}**.
""")
