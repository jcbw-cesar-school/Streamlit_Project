
import os
import pandas as pd
import plotly.express as px
import streamlit as st
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO DA PÁGINA
# ==========================================

st.set_page_config(
    page_title="Dashboard de Arrecadação",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard de Arrecadação por Estado")
st.markdown(
    "Análise interativa da arrecadação dos estados brasileiros."
)

# ==========================================
# LEITURA DA BASE DE DADOS
# ==========================================

@st.cache_data
def carregar_dados():
    arquivo = "arrecadacao-estado.csv"

    if not os.path.exists(arquivo):
        return None

    # Detecta automaticamente separador
    df = pd.read_csv(arquivo, sep=";", encoding="latin1" , engine="python")

    # Padronização dos nomes das colunas
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    return df


df = carregar_dados()

if df is None:
    st.error("Arquivo arrecadacao-estado.csv não encontrado.")
    st.stop()


# ==========================================
# IDENTIFICAÇÃO DAS COLUNAS
# ==========================================

# Localiza a coluna UF
col_estado = next(
    (c for c in df.columns if c.strip().lower() == "uf"),
    None
)

if col_estado is None:
    st.error("Coluna UF não encontrada na base de dados.")
    st.write("Colunas disponíveis:", df.columns.tolist())
    st.stop()

# Identifica mês e ano
col_mes = next(
    (c for c in df.columns if c in ["mes", "mês"]),
    None
)

col_ano = next(
    (c for c in df.columns if c == "ano"),
    None
)


# ==========================================
# TRATAMENTO DOS DADOS
# ==========================================

dados = df.copy()

if col_mes is None or col_ano is None:
    st.error("Não foi possível identificar as colunas de mês e ano.")
    st.stop()

# Identifica todas as colunas de impostos
colunas_impostos = [
    c for c in dados.columns
    if c not in [col_estado, col_mes, col_ano]
]

# Converte os valores dos impostos para números
for coluna in colunas_impostos:

    if dados[coluna].dtype == "object":

        valor = (
            dados[coluna]
            .astype(str)
            .str.replace("R$", "", regex=False)
            .str.strip()
        )

        # Trata números no formato brasileiro
        valor = valor.apply(
            lambda x: x.replace(".", "").replace(",", ".")
            if "," in x else x
        )

        dados[coluna] = pd.to_numeric(
            valor, errors="coerce"
        )

    else:
        dados[coluna] = pd.to_numeric(
            dados[coluna], errors="coerce"
        )

# Soma todos os impostos de cada linha
dados["arrecadacao_total"] = dados[
    colunas_impostos
].sum(axis=1, min_count=1)

# Remove registros inválidos
dados = dados.dropna(
    subset=[col_estado, "arrecadacao_total"]
)

# Exibe conferência dos resultados
#st.subheader("Conferência da arrecadação")

#st.dataframe(
#    dados[
#        [col_estado, col_mes, col_ano, "arrecadacao_total"]
#    ].head(10),
#    use_container_width=True
#)

# Define a coluna de arrecadação utilizada nos gráficos
#col_arrecadacao = "arrecadacao_total"

def formatar_reais(valor):
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


# ==========================================
# WIDGET 1 - FILTRO DE ESTADOS
# ==========================================

st.sidebar.subheader("🔎 Filtro de Estados")

estados = sorted(
    dados[col_estado].dropna().astype(str).str.strip().unique()
)

estados_selecionados = st.sidebar.multiselect(
    "Selecione os estados:",
    options=estados,
    default=estados
)


# ==========================================
# WIDGET 2 - FILTRO DE ANOS
# ==========================================

st.sidebar.subheader("📅 Filtro de Anos")

anos = sorted(
    dados[col_ano].dropna().unique()
)

# Seleciona automaticamente o último ano
ultimo_ano = anos[-1] if len(anos) > 0 else None

anos_selecionados = st.sidebar.multiselect(
    "Selecione os anos:",
    options=anos,
    default=[ultimo_ano] if ultimo_ano is not None else []
)



# ==========================================
# WIDGET 3 - FILTRO DOS ÚLTIMOS 6 MESES
# ==========================================

st.sidebar.subheader("🗓️ Filtro de Meses")

meses = dados[col_mes].dropna().unique().tolist()

ordem_meses = [
    "Jan", "Fev", "Mar", "Abr", "Mai", "Jun",
    "Jul", "Ago", "Set", "Out", "Nov", "Dez"
]

# Ordenação cronológica
meses = sorted(
    meses,
    key=lambda x: ordem_meses.index(
        str(x).strip().title()[:3]
    )
    if str(x).strip().title()[:3] in ordem_meses
    else 99
)

# Identifica o mês e ano atuais
data_atual = datetime.now()

# Calcula os últimos 6 meses, incluindo o atual
ultimos_6_meses = []

for i in range(8, -1, -1):
    mes_num = (data_atual.month - 1 - i) % 12 + 1

    ultimos_6_meses.append(
        ordem_meses[mes_num - 1]
    )

# Seleciona os meses disponíveis na base
meses_padrao = [
    m for m in meses
    if str(m).strip().title()[:3] in ultimos_6_meses
]

meses_selecionados = st.sidebar.multiselect(
    "Selecione os meses:",
    options=meses,
    default=meses_padrao
)

# ==========================================
# APLICAÇÃO DOS FILTROS
# ==========================================

dados_filtrados = dados[
    (dados[col_estado].astype(str).str.strip().isin(estados_selecionados)) &
    (dados[col_ano].isin(anos_selecionados)) &
    (dados[col_mes].isin(meses_selecionados))
].copy()


# ==========================================
# TABELA DE CONFERÊNCIA
# ==========================================

st.subheader("📋 Conferência da arrecadação")

st.write(
    f"Total de registros encontrados: {len(dados_filtrados)}"
)

if dados_filtrados.empty:
    st.warning("Nenhum registro encontrado com os filtros selecionados.")

else:
    # Ordena da maior para a menor arrecadação
    dados_ordenados = dados_filtrados.sort_values(
        by="arrecadacao_total",
        ascending=False
    )

    st.dataframe(
        dados_ordenados[
            [col_estado, col_mes, col_ano, "arrecadacao_total"]
        ],
        use_container_width=True,
        height=400,
        hide_index=True,
        column_config={
            "arrecadacao_total": st.column_config.NumberColumn(
                "Arrecadação Total",
                format="R$ %.2f"
            )
        }
    )

# ==========================================
# GRÁFICO 1 - BOXPLOT POR ESTADO
# ==========================================

st.divider()

st.subheader("📦 Distribuição da Arrecadação por Estado")

st.markdown(
    """
    O gráfico apresenta a dispersão dos valores de arrecadação
    por estado, permitindo identificar medianas, quartis,
    variabilidade e possíveis valores extremos.
    """
)

if dados_filtrados.empty:

    st.warning("Não existem dados para gerar o gráfico.")

else:

    fig_box = px.box(
        dados_filtrados,
        x=col_estado,
        y="arrecadacao_total",
        color=col_estado,
        points="all",
        title="Boxplot - Distribuição da Arrecadação por Estado",
        labels={
            col_estado: "Estado (UF)",
            "arrecadacao_total": "Arrecadação Total (R$)"
        },
        hover_data=[
            col_mes,
            col_ano,
            "arrecadacao_total"
        ]
    )

    # Configurações visuais
    fig_box.update_layout(
        template="plotly_white",
        showlegend=False,
        xaxis_title="Estados",
        yaxis_title="Arrecadação (R$)",
        height=600,
        hovermode="closest"
    )

    # Formatação dos valores monetários
    fig_box.update_yaxes(
        tickprefix="R$ ",
        tickformat=",.2f",
        separatethousands=True
    )

    fig_box.update_traces(
        hovertemplate=
        "<b>Estado:</b> %{x}<br>" +
        "<b>Arrecadação:</b> R$ %{y:,.2f}<extra></extra>"
    )

    # Exibe o gráfico
    st.plotly_chart(
        fig_box,
        use_container_width=True
    )


# ==========================================
# GRÁFICO - TOP 10 TIPOS DE IMPOSTOS
# ==========================================

st.divider()

st.subheader("🏆 Top 10 - Maiores Arrecadações por Tipo de Imposto")

if dados_filtrados.empty:

    st.warning("Não existem dados para gerar o gráfico.")

else:

    # Identifica as colunas de impostos
    colunas_impostos = [
        c for c in dados_filtrados.columns
        if c not in [
            col_estado,
            col_mes,
            col_ano,
            "arrecadacao_total"
        ]
    ]

    # Soma a arrecadação de cada tipo de imposto
    arrecadacao_impostos = (
        dados_filtrados[colunas_impostos]
        .sum()
        .reset_index()
    )

    # Renomeia as colunas
    arrecadacao_impostos.columns = [
        "tipo_imposto",
        "arrecadacao"
    ]

    # Ordena do maior para o menor
    top10_impostos = (
        arrecadacao_impostos
        .sort_values(
            by="arrecadacao",
            ascending=False
        )
        .head(10)
    )

    # Cria o gráfico de barras
    fig_impostos = px.bar(
        top10_impostos,
        x="arrecadacao",
        y="tipo_imposto",
        orientation="h",
        color="arrecadacao",
        text_auto=".2s",
        title="Top 10 Tipos de Impostos por Arrecadação",
        labels={
            "tipo_imposto": "Tipo de Imposto",
            "arrecadacao": "Arrecadação (R$)"
        },
        color_continuous_scale="Blues"
    )

    # Configurações visuais
    fig_impostos.update_layout(
        template="plotly_white",
        height=600,
        yaxis={
            "categoryorder": "total ascending"
        },
        xaxis_title="Arrecadação (R$)",
        yaxis_title="Tipo de Imposto",
        coloraxis_showscale=False
    )

    fig_impostos.update_xaxes(
        tickprefix="R$ ",
        tickformat=",.2f",
        separatethousands=True
    )

    fig_impostos.update_traces(
        texttemplate="R$ %{x:,.2f}",
        hovertemplate=
        "<b>Imposto:</b> %{y}<br>" +
        "<b>Arrecadação:</b> R$ %{x:,.2f}<extra></extra>"
    )

    # Exibe o gráfico
    st.plotly_chart(
        fig_impostos,
        use_container_width=True
    )
