from pathlib import Path
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
PASTA = Path(__file__).resolve().parent.parent
BASE_PADRAO = PASTA / "dados" / "mulheres_municipios.csv"
FAIXAS = {
    "0_4": "0 a 4 anos", "5_9": "5 a 9 anos", "10_14": "10 a 14 anos", "15_19": "15 a 19 anos",
    "20_24": "20 a 24 anos", "25_29": "25 a 29 anos", "30_39": "30 a 39 anos", "40_49": "40 a 49 anos",
    "50_59": "50 a 59 anos", "60_69": "60 a 69 anos", "70_mais": "70 anos ou mais",
}
RACAS = {"branca": "Branca", "preta": "Preta", "parda": "Parda", "amarela": "Amarela", "indigena": "Indígena"}
COLUNAS = (["ano", "regiao", "uf", "cod_municipio", "municipio", "situacao", "resp_mulheres", "resp_homens"]
           + ["mulheres_" + f for f in FAIXAS] + ["homens_" + f for f in FAIXAS])
ORDEM_REGIAO = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]
CORES_REGIAO = {"Norte": "#2a78d6", "Nordeste": "#eb6834", "Centro-Oeste": "#1baf7a",
                "Sudeste": "#eda100", "Sul": "#e87ba4"}
COR_MULHERES = "#6250d6"
COR_HOMENS = "#1baf7a"
CORES_RACA = {"Branca": "#2a78d6", "Preta": "#eb6834", "Parda": "#1baf7a", "Amarela": "#eda100", "Indígena": "#e87ba4"}
INDICADORES = ["Mulheres na população", "Domicílios chefiados por mulheres", "Mulheres por cor ou raça"]
def numero(valor, casas=0):
    return f"{valor:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")
def pct(valor, casas=1):
    return numero(valor, casas) + "%"
def ler_arquivo(arquivo):
    if arquivo.name.lower().endswith(".xlsx"):
        return pd.read_excel(arquivo)
    return pd.read_csv(arquivo, sep=None, engine="python", encoding="utf-8-sig")
@st.cache_data
def ler_base_padrao():
    return pd.read_csv(BASE_PADRAO, encoding="utf-8-sig")
def limpar(df):
    df = df.copy()
    df.columns = [str(c).strip().lower() for c in df.columns]
    faltando = [c for c in COLUNAS if c not in df.columns]
    if faltando:
        return None, faltando
    for raca in RACAS:
        if "mulheres_" + raca not in df.columns:
            df["mulheres_" + raca] = np.nan
    numericas = [c for c in df.columns if c.startswith(("mulheres_", "homens_", "resp_"))] + ["ano", "cod_municipio"]
    for col in numericas:
        if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
            texto = df[col].astype(str).str.strip()
            com_virgula = texto.str.contains(",", regex=False)
            texto[com_virgula] = texto[com_virgula].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
            df[col] = texto
        df[col] = pd.to_numeric(df[col], errors="coerce")
    for col in ["regiao", "uf", "municipio", "situacao"]:
        df[col] = df[col].astype(str).str.strip()
    df = df.dropna(subset=["ano", "cod_municipio"])
    contagens = [c for c in numericas if c not in ("ano", "cod_municipio")]
    df = df[(df[contagens].fillna(0) >= 0).all(axis=1)]
    df = df.drop_duplicates()
    df["ano"] = df["ano"].astype(int)
    df["situacao"] = df["situacao"].str.title()
    return df, []
def calcular(df, indicador, faixas, racas):
    chaves = ["ano", "regiao", "uf", "cod_municipio", "municipio"]
    somar = [c for c in df.columns if c.startswith(("mulheres_", "homens_", "resp_"))]
    tabela = df.groupby(chaves, as_index=False)[somar].sum(min_count=1)
    if indicador == INDICADORES[0]:
        tabela["parte"] = tabela[["mulheres_" + f for f in faixas]].sum(axis=1)
        tabela["outra"] = tabela[["homens_" + f for f in faixas]].sum(axis=1)
        tabela["total"] = tabela["parte"] + tabela["outra"]
    elif indicador == INDICADORES[1]:
        tabela["parte"] = tabela["resp_mulheres"]
        tabela["total"] = tabela["resp_mulheres"] + tabela["resp_homens"]
    else:
        todas = ["mulheres_" + r for r in RACAS]
        tabela = tabela.dropna(subset=todas, how="all")
        tabela["parte"] = tabela[["mulheres_" + r for r in racas]].sum(axis=1)
        tabela["total"] = tabela[todas].sum(axis=1)
    tabela = tabela[tabela["total"] > 0].copy()
    tabela["valor"] = tabela["parte"] / tabela["total"] * 100
    return tabela
def estatisticas(serie):
    q1 = serie.quantile(0.25)
    q3 = serie.quantile(0.75)
    iqr = q3 - q1
    return {
        "media": serie.mean(),
        "mediana": serie.median(),
        "moda": serie.round().mode()[0],
        "q1": q1,
        "q3": q3,
        "iqr": iqr,
        "minimo": serie.min(),
        "maximo": serie.max(),
        "amplitude": serie.max() - serie.min(),
        "variancia": serie.var(ddof=0),
        "desvio": serie.std(ddof=0),
        "cv": serie.std(ddof=0) / serie.mean() * 100,
        "lim_inf": q1 - 1.5 * iqr,
        "lim_sup": q3 + 1.5 * iqr,
    }

st.sidebar.header("Mulheres no Brasil")
arquivo = st.sidebar.file_uploader("Enviar base do IBGE (CSV ou XLSX)", type=["csv", "xlsx"])
if arquivo is not None:
    try:
        bruto = ler_arquivo(arquivo)
        st.sidebar.success(f"Arquivo carregado: {arquivo.name}")
    except Exception as erro:
        st.sidebar.error(f"Não consegui ler o arquivo: {erro}")
        st.stop()
else:
    bruto = ler_base_padrao()
    st.sidebar.caption("Usando a base padrão do projeto (Censo 2010 e 2022).")
base, faltando = limpar(bruto)
if base is None:
    st.error("O arquivo enviado não tem as colunas esperadas. Faltam: " + ", ".join(faltando))
    st.stop()
st.sidebar.subheader("Filtros")
anos = sorted(base["ano"].unique())
ano = st.sidebar.radio("Ano do Censo", anos, index=len(anos) - 1, horizontal=True)
tem_raca = base.loc[base["ano"] == ano, ["mulheres_" + r for r in RACAS]].notna().any().any()
opcoes = INDICADORES if tem_raca else INDICADORES[:2]
indicador = st.sidebar.radio("O que analisar", opcoes)
if not tem_raca:
    st.sidebar.caption("Cor ou raça por sexo só está disponível na base de 2022.")
regioes_existentes = [r for r in ORDEM_REGIAO if r in base["regiao"].unique()]
regioes = st.sidebar.multiselect("Região", regioes_existentes, default=regioes_existentes)
ufs_existentes = sorted(base[base["regiao"].isin(regioes)]["uf"].unique())
ufs = st.sidebar.multiselect("UF", ufs_existentes, default=ufs_existentes)
situacoes_existentes = sorted(base["situacao"].unique(), reverse=True)
situacoes = st.sidebar.multiselect("Situação do domicílio", situacoes_existentes, default=situacoes_existentes)
faixas = list(FAIXAS)
racas = ["preta", "parda"]
if indicador == INDICADORES[0]:
    nomes_faixas = st.sidebar.multiselect("Faixa etária", list(FAIXAS.values()), default=list(FAIXAS.values()))
    faixas = [f for f, nome in FAIXAS.items() if nome in nomes_faixas]
if indicador == INDICADORES[2]:
    nomes_racas = st.sidebar.multiselect("Cor ou raça", list(RACAS.values()), default=["Preta", "Parda"])
    racas = [r for r, nome in RACAS.items() if nome in nomes_racas]
if not faixas or not racas or not regioes or not ufs or not situacoes:
    st.warning("Marque pelo menos uma opção em cada filtro da barra lateral.")
    st.stop()
filtro = base["regiao"].isin(regioes) & base["uf"].isin(ufs) & base["situacao"].isin(situacoes)
recorte = base[filtro]
dados = calcular(recorte[recorte["ano"] == ano], indicador, faixas, racas)
if dados.empty:
    st.warning("Nenhum município com esses filtros.")
    st.stop()
if indicador == INDICADORES[0]:
    rotulo = "Mulheres na população (%)"
    explicacao = "percentual de mulheres entre os moradores" + ("" if len(faixas) == len(FAIXAS) else " das faixas etárias escolhidas")
elif indicador == INDICADORES[1]:
    rotulo = "Domicílios chefiados por mulheres (%)"
    explicacao = "percentual de domicílios em que a pessoa responsável é uma mulher"
else:
    rotulo = "Mulheres das cores escolhidas (%)"
    explicacao = "percentual das mulheres que se declararam " + ", ".join(RACAS[r].lower() for r in racas)
est = estatisticas(dados["valor"])
geral = dados["parte"].sum() / dados["total"].sum() * 100
dados["outlier"] = np.where(dados["valor"] > est["lim_sup"], "Acima do limite",
                            np.where(dados["valor"] < est["lim_inf"], "Abaixo do limite", "Dentro do padrão"))
acima = dados[dados["outlier"] == "Acima do limite"]
abaixo = dados[dados["outlier"] == "Abaixo do limite"]
sem_outliers = dados[dados["outlier"] == "Dentro do padrão"]
st.title("Mulheres no Brasil")
st.caption(f"Indicador 4 · IBGE, Censo Demográfico {ano} · cada ponto dos gráficos é um município")
st.markdown(
    "Quantas são, onde estão e quem são as mulheres brasileiras? Como startup de análise de dados, "
    "usamos o Censo para mostrar aos gestores públicos **como a presença feminina, a chefia dos lares "
    "e o perfil das mulheres mudam de um território para outro**."
)
st.info(f"Indicador escolhido: **{indicador}** ({explicacao}).")
abas = st.tabs(["Visão geral", "Perfil das mulheres", "Outliers", "2010 x 2022",
                "Perguntas de negócio", "Notícias", "Dados e método"])
with abas[0]:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Municípios no recorte", numero(len(dados)))
    c2.metric("Média", pct(est["media"], 2))
    c3.metric("Mediana", pct(est["mediana"], 2))
    c4.metric("Desvio padrão", numero(est["desvio"], 2) + " p.p.",
              help="p.p. = pontos percentuais, a distância entre duas porcentagens.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("1º quartil (Q1)", pct(est["q1"], 2))
    c2.metric("3º quartil (Q3)", pct(est["q3"], 2))
    c3.metric("Intervalo interquartil (IQR)", numero(est["iqr"], 2) + " p.p.")
    c4.metric("Amplitude", numero(est["amplitude"], 2) + " p.p.")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Moda (valor mais comum)", pct(est["moda"], 0),
              help="Valores arredondados para o número inteiro mais próximo antes de contar o mais frequente.")
    c2.metric("Variância", numero(est["variancia"], 2))
    c3.metric("Municípios outliers", numero(len(acima) + len(abaixo)))
    c4.metric("Recorte todo junto", pct(geral, 2),
              help="Soma de todas as pessoas do recorte. Aqui cada pessoa conta uma vez, então as cidades grandes "
                   "pesam mais do que nas medidas acima, que contam cada município uma vez.")
    st.subheader("Distribuição entre os municípios")
    hist = px.histogram(dados, x="valor", nbins=80, labels={"valor": rotulo},
                        color_discrete_sequence=["#86b6ef"])
    hist.update_traces(marker_line_color="white", marker_line_width=1,
                       hovertemplate="Faixa: %{x}<br>Municípios: %{y}<extra></extra>")
    hist.add_vline(x=est["media"], line_color="#eb6834", line_width=2,
                   annotation_text="Média " + pct(est["media"], 2), annotation_position="top right",
                   annotation_y=0.9)
    hist.add_vline(x=est["mediana"], line_color="#0d366b", line_width=2, line_dash="dash",
                   annotation_text="Mediana " + pct(est["mediana"], 2), annotation_position="top left")
    hist.update_layout(yaxis_title="Quantidade de municípios", bargap=0.02)
    st.plotly_chart(hist, width="stretch")
    lado = "esquerda" if dados["valor"].skew() < 0 else "direita"
    st.caption(f"Assimetria de {numero(dados['valor'].skew(), 2)}: a cauda mais comprida fica à {lado}. "
               "A média vai para o lado da cauda, enquanto a mediana fica no meio da fila.")
    st.subheader("Boxplot por região")
    regioes_no_recorte = [r for r in ORDEM_REGIAO if r in dados["regiao"].unique()]
    caixa = px.box(dados, x="regiao", y="valor", color="regiao", points="outliers",
                   category_orders={"regiao": regioes_no_recorte}, color_discrete_map=CORES_REGIAO,
                   hover_data={"municipio": True, "uf": True, "regiao": False},
                   labels={"regiao": "Região", "valor": rotulo, "municipio": "Município", "uf": "UF"})
    caixa.update_layout(showlegend=False)
    st.plotly_chart(caixa, width="stretch")
    st.caption("A caixa vai do Q1 ao Q3 (metade central dos municípios), a linha no meio é a mediana "
               "e os pontos soltos são os outliers pela regra de 1,5 × IQR.")
    st.subheader("Comparação entre as UFs")
    por_uf = dados.groupby(["uf", "regiao"], as_index=False).agg(
        parte=("parte", "sum"), total=("total", "sum"), media=("valor", "mean"), mediana=("valor", "median"),
        desvio=("valor", lambda s: s.std(ddof=0)), q1=("valor", lambda s: s.quantile(0.25)),
        q3=("valor", lambda s: s.quantile(0.75)), municipios=("valor", "count"))
    por_uf["uf_toda"] = por_uf["parte"] / por_uf["total"] * 100
    por_uf["iqr"] = por_uf["q3"] - por_uf["q1"]
    por_uf = por_uf.sort_values("uf_toda", ascending=False)
    barras = px.bar(por_uf, x="uf", y="uf_toda", color="regiao", color_discrete_map=CORES_REGIAO,
                    category_orders={"regiao": regioes_no_recorte, "uf": por_uf["uf"].tolist()},
                    labels={"uf": "UF", "uf_toda": rotulo, "regiao": "Região"},
                    hover_data={"mediana": ":.2f", "municipios": True})
    barras.update_layout(legend_title_text="Região")
    faixa_y = por_uf["uf_toda"]
    if faixa_y.max() - faixa_y.min() < 15:
        barras.update_yaxes(range=[max(0, faixa_y.min() - 3), faixa_y.max() + 1.5])
        st.caption("O eixo vertical não começa no zero para as diferenças entre as UFs ficarem visíveis.")
    st.plotly_chart(barras, width="stretch")
    tabela_uf = por_uf.rename(columns={"uf": "UF", "regiao": "Região", "municipios": "Municípios",
                                       "uf_toda": "UF toda (%)", "media": "Média", "mediana": "Mediana",
                                       "desvio": "Desvio padrão", "q1": "Q1", "q3": "Q3", "iqr": "IQR"})
    tabela_uf = tabela_uf[["UF", "Região", "Municípios", "UF toda (%)", "Média", "Mediana", "Q1", "Q3", "IQR", "Desvio padrão"]]
    st.dataframe(tabela_uf, hide_index=True, width="stretch",
                 column_config={c: st.column_config.NumberColumn(format="%.2f")
                                for c in ["UF toda (%)", "Média", "Mediana", "Q1", "Q3", "IQR", "Desvio padrão"]})
with abas[1]:
    no_ano = recorte[recorte["ano"] == ano]
    piramide = pd.DataFrame({
        "faixa": list(FAIXAS.values()),
        "mulheres": [no_ano["mulheres_" + f].sum() for f in FAIXAS],
        "homens": [no_ano["homens_" + f].sum() for f in FAIXAS],
    })
    piramide["pct_mulheres"] = piramide["mulheres"] / (piramide["mulheres"] + piramide["homens"]) * 100
    st.subheader("Pirâmide etária do recorte")
    fig = go.Figure()
    fig.add_bar(y=piramide["faixa"], x=-piramide["homens"], orientation="h", name="Homens",
                marker_color=COR_HOMENS, customdata=piramide["homens"],
                hovertemplate="%{y}<br>Homens: %{customdata:,.0f}<extra></extra>")
    fig.add_bar(y=piramide["faixa"], x=piramide["mulheres"], orientation="h", name="Mulheres",
                marker_color=COR_MULHERES, customdata=piramide["mulheres"],
                hovertemplate="%{y}<br>Mulheres: %{customdata:,.0f}<extra></extra>")
    maximo = max(piramide["mulheres"].max(), piramide["homens"].max())
    potencia = 10 ** np.floor(np.log10(maximo / 3))
    passo = min([1, 2, 5, 10], key=lambda m: abs(maximo / 3 - m * potencia)) * potencia
    lado_marcas = np.arange(passo, maximo + passo / 2, passo)
    marcas = np.concatenate([-lado_marcas[::-1], [0], lado_marcas])
    fig.update_layout(barmode="relative", bargap=0.08, xaxis_title="Pessoas", yaxis_title="Faixa etária",
                      legend={"orientation": "h", "y": 1.08},
                      xaxis={"tickvals": marcas, "ticktext": [numero(abs(v)) for v in marcas]})
    st.plotly_chart(fig, width="stretch")
    st.caption("As barras de cada faixa têm larguras diferentes (10 anos a partir dos 30, 5 anos antes disso), "
               "por isso a pirâmide fica mais larga no meio.")
    st.subheader("Percentual de mulheres em cada faixa etária")
    perc = px.bar(piramide, x="faixa", y="pct_mulheres", labels={"faixa": "Faixa etária", "pct_mulheres": "Mulheres (%)"},
                  color_discrete_sequence=[COR_MULHERES], text=piramide["pct_mulheres"].map(lambda v: pct(v)))
    perc.add_hline(y=50, line_dash="dash", line_color="#52514e", annotation_text="50%", annotation_position="top left")
    perc.update_yaxes(range=[40, max(60, piramide["pct_mulheres"].max() + 2)])
    st.plotly_chart(perc, width="stretch")
    maioria = piramide[piramide["pct_mulheres"] > 50]
    if not maioria.empty:
        st.caption(f"No recorte, as mulheres passam a ser maioria a partir da faixa de {maioria['faixa'].iloc[0]} "
                   f"e chegam a {pct(piramide['pct_mulheres'].iloc[-1])} entre quem tem 70 anos ou mais: "
                   "elas vivem mais que os homens. O eixo vertical começa em 40%.")
    if no_ano[["mulheres_" + r for r in RACAS]].notna().any().any():
        st.subheader("Mulheres por cor ou raça em cada região")
        cor = no_ano.groupby("regiao")[["mulheres_" + r for r in RACAS]].sum()
        cor.columns = list(RACAS.values())
        cor = cor.div(cor.sum(axis=1), axis=0).mul(100).reset_index().melt(
            id_vars="regiao", var_name="Cor ou raça", value_name="Percentual")
        barras_cor = px.bar(cor, x="regiao", y="Percentual", color="Cor ou raça", color_discrete_map=CORES_RACA,
                            category_orders={"regiao": [r for r in ORDEM_REGIAO if r in cor["regiao"].unique()],
                                             "Cor ou raça": list(RACAS.values())},
                            labels={"regiao": "Região", "Percentual": "Mulheres (%)"})
        barras_cor.update_traces(marker_line_color="white", marker_line_width=2,
                                 hovertemplate="%{x}<br>%{fullData.name}: %{y:.1f}%<extra></extra>")
        st.plotly_chart(barras_cor, width="stretch")
    else:
        st.info("A base deste ano não traz cor ou raça separada por sexo.")
with abas[2]:
    st.subheader("Regra de 1,5 × IQR")
    st.markdown(
        f"- Limite de baixo: Q1 − 1,5 × IQR = **{pct(est['lim_inf'], 2)}**\n"
        f"- Limite de cima: Q3 + 1,5 × IQR = **{pct(est['lim_sup'], 2)}**\n"
        f"- Municípios acima do limite: **{len(acima)}** · abaixo do limite: **{len(abaixo)}**"
    )
    c1, c2, c3 = st.columns(3)
    c1.metric("Média com outliers", pct(est["media"], 2))
    c2.metric("Média sem outliers", pct(sem_outliers["valor"].mean(), 2))
    c3.metric("Mediana com outliers", pct(est["mediana"], 2))
    st.markdown(
        f"Sem os outliers, a média iria de {pct(est['media'], 2)} para {pct(sem_outliers['valor'].mean(), 2)}, "
        f"e a mediana de {pct(est['mediana'], 2)} para {pct(sem_outliers['valor'].median(), 2)}. "
        "A mediana muda menos porque depende só de quem está no meio da fila, e não do tamanho dos extremos."
    )
    mostrar = ["municipio", "uf", "regiao", "valor", "total"]
    nomes = {"municipio": "Município", "uf": "UF", "regiao": "Região", "valor": rotulo, "total": "Base do cálculo"}
    formato = {rotulo: st.column_config.NumberColumn(format="%.2f"),
               "Base do cálculo": st.column_config.NumberColumn(format="%d")}
    if not abaixo.empty:
        st.subheader("Municípios muito abaixo do padrão")
        st.dataframe(abaixo.sort_values("valor")[mostrar].rename(columns=nomes),
                     hide_index=True, width="stretch", column_config=formato)
    if not acima.empty:
        st.subheader("Municípios muito acima do padrão")
        st.dataframe(acima.sort_values("valor", ascending=False)[mostrar].rename(columns=nomes),
                     hide_index=True, width="stretch", column_config=formato)
    st.caption("A coluna \"Base do cálculo\" mostra quantas pessoas (ou domicílios) entraram na conta. "
               "Em municípios pequenos, poucas pessoas já mudam bastante o percentual.")
with abas[3]:
    if indicador == INDICADORES[2]:
        st.info("A comparação com 2010 não está disponível para cor ou raça, porque a base de 2010 não traz esse recorte por sexo.")
    elif recorte["ano"].nunique() < 2:
        st.info("A base carregada tem só um ano, então não dá para comparar.")
    else:
        comparar = []
        for cada_ano in sorted(recorte["ano"].unique()):
            tabela = calcular(recorte[recorte["ano"] == cada_ano], indicador, faixas, racas)
            comparar.append(tabela)
        comparar = pd.concat(comparar)
        evolucao = comparar.groupby(["uf", "ano"], as_index=False)[["parte", "total"]].sum()
        evolucao["valor"] = evolucao["parte"] / evolucao["total"] * 100
        evolucao["ano"] = evolucao["ano"].astype(str)
        ordem_uf = evolucao[evolucao["ano"] == evolucao["ano"].max()].sort_values("valor", ascending=False)["uf"].tolist()
        grafico = px.bar(evolucao, x="uf", y="valor", color="ano", barmode="group",
                         category_orders={"uf": ordem_uf, "ano": sorted(evolucao["ano"].unique())},
                         color_discrete_map={"2010": "#2a78d6", "2022": "#eb6834"},
                         labels={"uf": "UF", "valor": rotulo, "ano": "Ano"})
        if indicador == INDICADORES[0]:
            grafico.update_yaxes(range=[max(0, evolucao["valor"].min() - 3), evolucao["valor"].max() + 1.5])
            st.caption("O eixo vertical não começa no zero para as diferenças ficarem visíveis.")
        st.plotly_chart(grafico, width="stretch")
        resumo = comparar.groupby("ano").agg(parte=("parte", "sum"), total=("total", "sum"), mediana=("valor", "median"))
        resumo["geral"] = resumo["parte"] / resumo["total"] * 100
        primeiro, ultimo = resumo.index.min(), resumo.index.max()
        c1, c2 = st.columns(2)
        c1.metric(f"Recorte todo em {ultimo}", pct(resumo.loc[ultimo, "geral"], 2),
                  numero(resumo.loc[ultimo, "geral"] - resumo.loc[primeiro, "geral"], 2) + f" p.p. desde {primeiro}")
        c2.metric(f"Mediana dos municípios em {ultimo}", pct(resumo.loc[ultimo, "mediana"], 2),
                  numero(resumo.loc[ultimo, "mediana"] - resumo.loc[primeiro, "mediana"], 2) + f" p.p. desde {primeiro}")
with abas[4]:
    mediana_regiao = dados.groupby("regiao")["valor"].median()
    uf_alta = por_uf.iloc[0]
    uf_baixa = por_uf.iloc[-1]
    maior = dados.loc[dados["valor"].idxmax()]
    menor = dados.loc[dados["valor"].idxmin()]
    acima_50 = (dados["valor"] > 50).mean() * 100
    texto = f"""
#### 1. Qual é o retrato geral?
No recorte todo, o indicador é **{pct(geral, 2)}**. Olhando município por município, a mediana é
**{pct(est['mediana'], 2)}** e a média é {pct(est['media'], 2)}. Em {pct(acima_50)} dos municípios o valor passa de 50%.
Como o valor do recorte todo fica {"acima" if geral > est["mediana"] else "abaixo"} da mediana, as cidades mais populosas
têm valores {"mais altos" if geral > est["mediana"] else "mais baixos"} que o município típico: elas pesam mais quando cada pessoa conta uma vez.
#### 2. Onde o indicador é mais alto e mais baixo?
Entre as UFs, {uf_alta['uf']} tem o maior valor ({pct(uf_alta['uf_toda'], 2)}) e {uf_baixa['uf']} o menor
({pct(uf_baixa['uf_toda'], 2)}). Por região, a mediana dos municípios vai de {pct(mediana_regiao.min(), 2)}
no **{mediana_regiao.idxmin()}** a {pct(mediana_regiao.max(), 2)} no **{mediana_regiao.idxmax()}**.
O maior valor municipal é {maior['municipio']} ({maior['uf']}), com {pct(maior['valor'], 2)},
e o menor é {menor['municipio']} ({menor['uf']}), com {pct(menor['valor'], 2)}.
#### 3. Quão diferentes são os municípios entre si?
A metade central dos municípios fica entre {pct(est['q1'], 2)} e {pct(est['q3'], 2)} (IQR de {numero(est['iqr'], 2)} p.p.),
com desvio padrão de {numero(est['desvio'], 2)} p.p. Pela regra de 1,5 × IQR, {len(abaixo)} municípios ficam muito abaixo
e {len(acima)} muito acima do padrão.
"""
    if indicador == INDICADORES[0]:
        texto += """
#### 4. O que isso significa para os gestores?
- As mulheres são maioria principalmente nas idades mais altas (veja a aba "Perfil das mulheres"). Políticas para
  idosos são, na prática, políticas que atendem mais mulheres.
- Os municípios com poucas mulheres são casos especiais: alguns abrigam presídios, e a população presa,
  quase toda masculina, entra na contagem do Censo. Vale conferir cada outlier antes de tirar conclusões.
"""
    elif indicador == INDICADORES[1]:
        texto += """
#### 4. O que isso significa para os gestores?
- Quase metade dos lares já é chefiada por mulheres. Programas de renda, moradia e creche precisam considerar
  a mulher como a principal responsável pela casa.
- Os municípios abaixo do Q1 mostram onde a chefia feminina ainda é menor, o que ajuda a direcionar ações.
"""
    else:
        texto += """
#### 4. O que isso significa para os gestores?
- A composição racial das mulheres muda muito entre as regiões. Políticas para mulheres precisam ser pensadas
  junto com o recorte de cor ou raça de cada território.
"""
    st.markdown(texto)
    st.caption("Os números deste texto mudam sozinhos conforme os filtros da barra lateral.")
with abas[5]:
    noticias = [
        ("Mulheres chefiam metade dos lares brasileiros, segundo o IBGE",
         "Correio Braziliense · 26/10/2024",
         "O Censo 2022 mostrou que 49,1% dos domicílios tinham uma mulher como responsável, contra 38,7% em 2010.",
         "https://www.correiobraziliense.com.br/brasil/2024/10/amp/6973512-mulheres-chefiam-metade-dos-lares-brasileiros-segundo-o-ibge.html"),
        ("Cresce índice de mulheres responsáveis por domicílios; PE lidera no Brasil",
         "Movimento Econômico · 25/10/2024",
         "Pernambuco teve a maior proporção de lares chefiados por mulheres do país, com 53,9%.",
         "https://movimentoeconomico.com.br/economia/2024/10/25/cresce-indice-de-mulheres-responsaveis-por-domicilios-pe-lidera-no-brasil/"),
        ("Brasil é feminino: mulheres são maioria em todas as regiões pela primeira vez",
         "Forbes Brasil · 27/10/2023",
         "O Censo contou cerca de 6 milhões de mulheres a mais que homens. O Rio de Janeiro tem a maior "
         "proporção de mulheres e o Mato Grosso, a maior de homens.",
         "https://forbes.com.br/forbes-mulher/2023/10/brasil-e-feminino-mulheres-sao-maioria-em-todas-as-regioes-pela-primeira-vez/"),
        ("Homens são maioria apenas na população até 19 anos",
         "Jovem Pan · 27/10/2023",
         "A razão de sexo caiu para 94,2 homens a cada 100 mulheres, e a vantagem feminina cresce com a idade.",
         "https://jovempan.com.br/?p=53300"),
    ]
    col_noticias, col_imagens = st.columns([3, 2])
    with col_noticias:
        st.subheader("Na imprensa")
        for titulo, fonte, resumo, link in noticias:
            with st.container(border=True):
                st.markdown(f"**[{titulo}]({link})**")
                st.caption(fonte)
                st.write(resumo)
    with col_imagens:
        st.subheader("Para entender")
        st.image(str(PASTA / "imagens" / "chefia_feminina.png"),
                 caption="Domicílios chefiados por mulheres no Brasil, Censo 2010 e 2022.")
        st.image(str(PASTA / "imagens" / "como_ler_boxplot.png"),
                 caption="Como ler o boxplot usado neste painel.")
with abas[6]:
    st.markdown("""
**Fonte:** IBGE, Censo Demográfico 2010 e 2022, Agregados por Setores Censitários
(tabelas de sexo por idade, pessoa responsável pelo domicílio e cor ou raça por sexo).
**Como a base foi tratada (ETL):**
1. Leitura dos dados de cada setor censitário (pedaços de bairro com cerca de 200 domicílios).
2. Em 2010 a idade vem ano a ano, então as idades foram somadas nas mesmas faixas usadas em 2022.
3. Soma dos setores de cada município, separando a parte urbana da rural.
4. Os valores que o IBGE esconde por sigilo em setores muito pequenos ficam de fora da soma
   (cerca de 0,4% das mulheres de 2022).
**Indicadores:**
- **Mulheres na população:** mulheres ÷ (mulheres + homens) × 100, nas faixas etárias escolhidas.
- **Domicílios chefiados por mulheres:** responsáveis mulheres ÷ total de responsáveis × 100.
- **Mulheres por cor ou raça:** mulheres das cores escolhidas ÷ total de mulheres × 100 (só 2022).
**Cuidados:**
- A unidade analisada é o **município**: média, mediana e quartis descrevem como os municípios variam.
  O valor "Recorte todo junto" é o que vale para a população inteira do recorte.
- Municípios pequenos têm poucas pessoas na conta, então seus percentuais mudam mais facilmente.
""")
    st.download_button("Baixar os dados filtrados (CSV)",
                       dados.drop(columns=["outlier"]).to_csv(index=False).encode("utf-8-sig"),
                       file_name=f"mulheres_{ano}_filtrado.csv", mime="text/csv")
