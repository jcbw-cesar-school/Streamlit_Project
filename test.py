import os
import pandas as pd
import plotly.express as px
import streamlit as st


@st.cache_data
def load_data():
    """Carrega o arquivo de arrecadação por estado."""
    caminhos = [
        "arrecadacao-estado.csv",
        "data/arrecadacao-estado.csv",
        os.path.join("c:", "Users", "julio", "Documents", "Vscode", "Streamlit_Project", "arrecadacao-estado.csv"),
    ]

    for caminho in caminhos:
        if os.path.exists(caminho):
            #return pd.read_csv(caminho)
            #return pd.read_csv(caminho, encoding='latin-1')
            return pd.read_csv(caminho, encoding='latin-1', sep=';')

    return pd.DataFrame(
        {
            "estado": ["SP", "RJ", "MG", "RS", "PR", "SC"],
            "arrecadacao": [1200000, 850000, 640000, 520000, 470000, 400000],
        }
    )


st.title("Arrecadação por Estado")

df = load_data()

if df.empty:
    st.warning("Nenhum dado foi encontrado para a base de arrecadação por estado.")
    st.stop()

# Tenta identificar colunas automaticamente
state_col = None
value_col = None

for col in df.columns:
    nome = col.lower().strip().replace(" ", "")
    if state_col is None and any(alias in nome for alias in ["estado", "uf", "sigla"]):
        state_col = col
    if value_col is None and any(alias in nome for alias in ["arrecadacao", "receita", "valor", "total"]):
        value_col = col

if state_col is None or value_col is None:
    st.error("O arquivo precisa ter colunas como 'estado' e 'arrecadacao'.")
    st.write(df.head())
    st.stop()

# Ajusta o dataframe para o gráfico
chart_df = df[[state_col, value_col]].copy()
chart_df = chart_df.rename(columns={state_col: "estado", value_col: "arrecadacao"})
chart_df["arrecadacao"] = pd.to_numeric(chart_df["arrecadacao"], errors="coerce").fillna(0)
chart_df = chart_df.sort_values("arrecadacao", ascending=False)

st.subheader("Dados")
st.dataframe(chart_df.head(10), use_container_width=True)

fig = px.bar(
    chart_df,
    x="estado",
    y="arrecadacao",
    color="estado",
    title="Arrecadação por Estado",
    labels={"estado": "Estado", "arrecadacao": "Arrecadação"},
)

fig.update_layout(xaxis_tickangle=-45)
st.plotly_chart(fig, use_container_width=True)

# Exemplo de filtro por estado
estados = chart_df["estado"].tolist()
estado_selecionado = st.selectbox("Selecione um estado", ["Todos"] + estados)

if estado_selecionado != "Todos":
    dados_filtrados = chart_df[chart_df["estado"] == estado_selecionado]
    st.metric("Arrecadação do estado selecionado", f"R$ {dados_filtrados['arrecadacao'].sum():,.2f}")
