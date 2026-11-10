"""
Números que Falam — Descobrindo o Brasil
Indicador 1: AFAZERES DOMÉSTICOS (horas de cuidado não remunerado por sexo e raça)
Persona / demandantes: Secretárias de Estado (BA, PE, AM, CE)

Como rodar:
    pip install -r requirements.txt
    streamlit run afazeres_domesticos.py

Para integrar ao painel do grupo:
    from afazeres_domesticos import render
    render()          # chame dentro da página/menu lateral do app unificado
"""

import re
import unicodedata

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# ----------------------------------------------------------------------------
# 1. Constantes
# ----------------------------------------------------------------------------
UF_REGIAO = {
    "RO": "Norte", "AC": "Norte", "AM": "Norte", "RR": "Norte", "PA": "Norte", "AP": "Norte", "TO": "Norte",
    "MA": "Nordeste", "PI": "Nordeste", "CE": "Nordeste", "RN": "Nordeste", "PB": "Nordeste",
    "PE": "Nordeste", "AL": "Nordeste", "SE": "Nordeste", "BA": "Nordeste",
    "MG": "Sudeste", "ES": "Sudeste", "RJ": "Sudeste", "SP": "Sudeste",
    "PR": "Sul", "SC": "Sul", "RS": "Sul",
    "MS": "Centro-Oeste", "MT": "Centro-Oeste", "GO": "Centro-Oeste", "DF": "Centro-Oeste",
}

NOME_UF = {
    "rondonia": "RO", "acre": "AC", "amazonas": "AM", "roraima": "RR", "para": "PA", "amapa": "AP",
    "tocantins": "TO", "maranhao": "MA", "piaui": "PI", "ceara": "CE", "rio grande do norte": "RN",
    "paraiba": "PB", "pernambuco": "PE", "alagoas": "AL", "sergipe": "SE", "bahia": "BA",
    "minas gerais": "MG", "espirito santo": "ES", "rio de janeiro": "RJ", "sao paulo": "SP",
    "parana": "PR", "santa catarina": "SC", "rio grande do sul": "RS",
    "mato grosso do sul": "MS", "mato grosso": "MT", "goias": "GO", "distrito federal": "DF",
}

UFS_PERSONAS = ["BA", "PE", "AM", "CE"]  # Secretárias de Estado do cenário

# Colunas padronizadas usadas internamente
COLUNAS = ["UF", "Região", "Sexo", "Raça", "Faixa etária", "Ocupação", "Ano", "Horas"]

# Palavras-chave para sugerir o mapeamento de colunas de arquivos do SIDRA
PISTAS = {
    "UF": ["unidade da federacao", "uf", "estado"],
    "Sexo": ["sexo"],
    "Raça": ["cor ou raca", "raca", "cor"],
    "Faixa etária": ["grupo de idade", "faixa", "idade"],
    "Ano": ["ano", "trimestre"],
    "Horas": ["horas", "valor", "media"],
    "Região": ["regiao", "grande regiao"],
    "Ocupação": ["situacao na ocupacao", "condicao na ocupacao", "ocupacao", "situacao"],
}
OPCIONAIS = ["Região", "Sexo", "Raça", "Faixa etária", "Ocupação", "Ano"]
NENHUMA = "(não tem)"


# ----------------------------------------------------------------------------
# 2. ETL
# ----------------------------------------------------------------------------
def normaliza(txt) -> str:
    """minúsculas, sem acento e sem espaços duplicados."""
    txt = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", txt).strip().lower()


def gerar_demo(seed: int = 42) -> pd.DataFrame:
    """Base SINTÉTICA só para testar o painel. NÃO são dados do IBGE."""
    rng = np.random.default_rng(seed)
    efeito_uf = {uf: rng.normal(0, 1.3) for uf in UF_REGIAO}
    base = {"Mulheres": 21.4, "Homens": 11.0}
    raca_mult = {"Branca": 0.97, "Preta": 1.03, "Parda": 1.04}
    faixa_mult = {"14 a 24 anos": 0.80, "25 a 39 anos": 1.12, "40 a 59 anos": 1.10, "60 anos ou mais": 0.95}
    ocup_mult = {"Ocupadas": 0.86, "Não ocupadas": 1.18}
    linhas = []
    for ano in (2016, 2019, 2022):
        tendencia = {2016: 1.0, 2019: 1.01, 2022: 1.03}[ano]
        for uf, regiao in UF_REGIAO.items():
            for sexo, h in base.items():
                for raca, rm in raca_mult.items():
                    for faixa, fm in faixa_mult.items():
                        for ocup, om in ocup_mult.items():
                            v = (h * rm * fm * om + efeito_uf[uf] + rng.normal(0, 0.9)) * tendencia
                            linhas.append([uf, regiao, sexo, raca, faixa, ocup, ano, round(max(v, 2.0), 1)])
    return pd.DataFrame(linhas, columns=COLUNAS)


def ler_arquivo(arquivo) -> pd.DataFrame:
    """Lê CSV (separador ; ou ,) ou XLSX exportado do SIDRA/IBGE."""
    nome = arquivo.name.lower()
    if nome.endswith((".xlsx", ".xls")):
        return pd.read_excel(arquivo)
    return pd.read_csv(arquivo, sep=None, engine="python", encoding_errors="replace")


def sugerir_coluna(colunas, chave):
    for pista in PISTAS[chave]:
        for c in colunas:
            if pista == normaliza(c) or re.search(rf"\b{re.escape(pista)}\b", normaliza(c)):
                return c
    return None


def para_numero(serie: pd.Series) -> pd.Series:
    """Converte textos do SIDRA ('1.234,5', '-', '...', 'X') em número."""
    s = serie.astype(str).str.strip()
    s = s.replace({"-": np.nan, "..": np.nan, "...": np.nan, "X": np.nan, "nan": np.nan, "": np.nan})
    tem_virgula = s.dropna().str.contains(",").any()
    if tem_virgula:
        s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce")


def tratar(bruto: pd.DataFrame, mapa: dict) -> pd.DataFrame:
    """ETL: renomeia, limpa e padroniza (UF em sigla, região derivada, horas numéricas)."""
    df = pd.DataFrame()
    for destino, origem in mapa.items():
        if origem and origem != NENHUMA:
            df[destino] = bruto[origem]
    df["Horas"] = para_numero(df["Horas"])
    df = df.dropna(subset=["UF", "Horas"])

    # UF: aceita sigla ou nome por extenso
    def uf_sigla(x):
        x = str(x).strip()
        if x.upper() in UF_REGIAO:
            return x.upper()
        return NOME_UF.get(normaliza(x))

    df["UF"] = df["UF"].map(uf_sigla)
    df = df.dropna(subset=["UF"])
    if "Região" not in df.columns:
        df["Região"] = df["UF"].map(UF_REGIAO)
    for c in ("Sexo", "Raça", "Faixa etária", "Ocupação"):
        if c in df.columns:
            df[c] = df[c].astype(str).str.strip()
    if "Ano" in df.columns:
        df["Ano"] = df["Ano"].astype(str).str.extract(r"(\d{4})")[0]
    return df.drop_duplicates().reset_index(drop=True)


# ----------------------------------------------------------------------------
# 3. Estatística descritiva
# ----------------------------------------------------------------------------
def estatisticas(s: pd.Series) -> dict:
    s = s.dropna()
    q1, q2, q3 = s.quantile([0.25, 0.5, 0.75])
    iqr = q3 - q1
    lim_inf, lim_sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    moda = s.round(1).mode()
    return {
        "n": int(len(s)),
        "Média": s.mean(),
        "Mediana (Q2)": q2,
        "Moda": moda.iloc[0] if len(moda) else np.nan,
        "Q1": q1,
        "Q3": q3,
        "IQR": iqr,
        "Amplitude": s.max() - s.min(),
        "Variância": s.var(ddof=1),
        "Desvio padrão": s.std(ddof=1),
        "Coef. de variação (%)": s.std(ddof=1) / s.mean() * 100 if s.mean() else np.nan,
        "Limite inferior (1,5·IQR)": lim_inf,
        "Limite superior (1,5·IQR)": lim_sup,
        "Outliers": int(((s < lim_inf) | (s > lim_sup)).sum()),
    }


def fmt(x, casas=1) -> str:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "—"
    return f"{x:,.{casas}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def outliers(df: pd.DataFrame) -> pd.DataFrame:
    e = estatisticas(df["Horas"])
    return df[(df["Horas"] < e["Limite inferior (1,5·IQR)"]) | (df["Horas"] > e["Limite superior (1,5·IQR)"])]


# ----------------------------------------------------------------------------
# 4. Interface
# ----------------------------------------------------------------------------
def achar_sexos(df: pd.DataFrame):
    """Devolve (rótulo feminino, rótulo masculino) presentes na coluna Sexo."""
    if "Sexo" not in df.columns:
        return None, None
    vals = list(df["Sexo"].dropna().unique())
    fem = next((v for v in vals if normaliza(v).startswith(("mulher", "fem"))), None)
    mas = next((v for v in vals if normaliza(v).startswith(("homen", "homem", "masc"))), None)
    return fem, mas


def grupo_raca(valor: str):
    n = normaliza(valor)
    if n.startswith(("pret", "pard", "negr")):
        return "pretas/pardas"
    if n.startswith("branc"):
        return "brancas"
    return None


def filtros(df: pd.DataFrame):
    """Aplica os filtros da barra lateral. Devolve (df filtrado, df de referência nacional).
    A referência nacional usa os mesmos filtros, exceto Região e UF."""
    st.sidebar.subheader("Filtros")
    ref = df.copy()

    def multi(coluna, rotulo):
        nonlocal df, ref
        if coluna in df.columns:
            opcoes = sorted(df[coluna].dropna().unique())
            sel = st.sidebar.multiselect(rotulo, opcoes, default=opcoes)
            df = df[df[coluna].isin(sel)]
            ref = ref[ref[coluna].isin(sel)]

    multi("Ano", "Ano")
    multi("Faixa etária", "Faixa etária")
    multi("Sexo", "Sexo")
    multi("Raça", "Cor ou raça")
    multi("Ocupação", "Situação na ocupação")

    regs = sorted(df["Região"].dropna().unique())
    sel = st.sidebar.multiselect("Região", regs, default=regs)
    df = df[df["Região"].isin(sel)]
    foco = st.sidebar.checkbox("Foco nos estados do cenário (BA, PE, AM, CE)")
    if foco:
        df = df[df["UF"].isin(UFS_PERSONAS)]
    else:
        ufs = sorted(df["UF"].unique())
        sel = st.sidebar.multiselect("Estados (UF)", ufs, default=ufs)
        df = df[df["UF"].isin(sel)]
    return df, ref


def texto_interpretativo(df: pd.DataFrame) -> list:
    out = []
    e = estatisticas(df["Horas"])
    dif = e["Média"] - e["Mediana (Q2)"]
    if abs(dif) < 0.05 * e["Média"]:
        out.append(f"Média ({fmt(e['Média'])} h) e mediana ({fmt(e['Mediana (Q2)'])} h) são próximas: "
                   "distribuição aproximadamente simétrica; a média é uma boa referência.")
    else:
        lado = "puxada para cima" if dif > 0 else "puxada para baixo"
        out.append(f"A média ({fmt(e['Média'])} h) está {lado} em relação à mediana ({fmt(e['Mediana (Q2)'])} h): "
                   "há assimetria, então a mediana representa melhor o valor típico.")
    out.append(f"A metade central dos dados fica entre {fmt(e['Q1'])} h e {fmt(e['Q3'])} h (IQR = {fmt(e['IQR'])} h); "
               f"o desvio padrão é {fmt(e['Desvio padrão'])} h (CV = {fmt(e['Coef. de variação (%)'])}%).")
    out.append(f"Pela regra 1,5·IQR, há {e['Outliers']} observação(ões) atípica(s) nos filtros atuais.")

    fem, mas = achar_sexos(df)
    if fem and mas:
        m = df.groupby("Sexo")["Horas"].mean()
        out.append(f"As mulheres dedicam em média {fmt(m[fem])} h por semana e os homens {fmt(m[mas])} h: "
                   f"diferença de {fmt(m[fem] - m[mas])} h ({fmt(m[fem] / m[mas], 2)}x).")
    por_uf = df.groupby("UF")["Horas"].mean().sort_values()
    if len(por_uf) >= 2:
        out.append(f"Entre as UFs filtradas, a menor média é {por_uf.index[0]} ({fmt(por_uf.iloc[0])} h) "
                   f"e a maior é {por_uf.index[-1]} ({fmt(por_uf.iloc[-1])} h).")
    return out


NOTICIAS = {
    "Carga mental feminina": [
        ("ONU News — ONU Mulheres ressalta peso invisível da carga mental feminina",
         "https://news.un.org/pt/story/2026/06/1853597",
         "A ONU Mulheres alerta que o planejamento e a gestão da casa continuam recaindo sobre as mulheres, "
         "mesmo quando elas são as principais provedoras."),
        ("A Crítica — Quando ser forte demais adoece: sobrecarga feminina e materna",
         "https://www.acritica.com/geral/quando-ser-forte-demais-adoece-sobrecarga-feminina-e-materna-pode-esconder-sofrimento-psicologico-1.416105",
         "Relaciona a sobrecarga de mulheres e mães a ansiedade, depressão e esgotamento, usando os dados do IBGE "
         "de 2022 sobre horas de cuidado."),
    ],
    "Economia do cuidado": [
        ("O POVO+ (CE) — Economia do cuidado: um trabalho invisível e não remunerado das mulheres",
         "https://mais.opovo.com.br/reportagens-especiais/mulheres-e-cuidado-economia-sociedade/2024/06/25/economia-do-cuidado-um-trabalho-invisivel-e-nao-remunerado-das-mulheres.html",
         "Reportagem cearense que cita estudo do Ibre/FGV: se fosse valorado, o cuidado das mulheres elevaria o PIB "
         "em pelo menos 13%."),
        ("CartaCapital — Trabalho doméstico não remunerado vale 11% do PIB no Brasil",
         "https://cartacapital.com.br/economia/trabalho-domestico-nao-remunerado-vale-11-do-pib-no-brasil",
         "Apresenta a estimativa de 11% do PIB e a proposta de uma conta satélite para medir esse trabalho."),
        ("Agência Câmara — Proposta inclui trabalho doméstico não remunerado no PIB",
         "https://www.camara.leg.br/noticias/556609-PROPOSTA-INCLUI-TRABALHO-DOMESTICO-NAO-REMUNERADO-NO-PIB",
         "Explica o PL 638/2019, que pede ao IBGE uma pesquisa de uso do tempo para medir a economia do cuidado."),
    ],
}


def render():
    st.title("🏠 Afazeres Domésticos — Tabela 1.1")
    st.caption("Horas semanais dedicadas a cuidados de pessoas e/ou afazeres domésticos · "
               "Cenário: Maria (Assistência Social, BA), Fátima (Políticas para Mulheres, PE), "
               "Antônio (AM) e Luíza (CE) elaboram políticas para dividir melhor o trabalho de cuidado não remunerado.")

    # ---- Upload / ETL ----
    st.sidebar.subheader("Dados")
    arquivo = st.sidebar.file_uploader("Base do IBGE (CSV/XLSX)", type=["csv", "xlsx", "xls"])
    if arquivo is None:
        st.warning("**Modo demonstração:** os dados abaixo são SINTÉTICOS, só para testar o painel. "
                   "Envie na barra lateral o CSV/XLSX do IBGE para analisar dados reais.")
        df_total = gerar_demo()
    else:
        try:
            bruto = ler_arquivo(arquivo)
        except Exception as erro:  # noqa: BLE001
            st.error(f"Não consegui ler o arquivo: {erro}")
            st.stop()
        cols = list(bruto.columns)
        with st.sidebar.expander("Mapeamento de colunas", expanded=True):
            mapa = {}
            for chave in ["UF", "Horas"] + OPCIONAIS:
                sug = sugerir_coluna(cols, chave)
                opcoes = cols if chave in ("UF", "Horas") else [NENHUMA] + cols
                idx = opcoes.index(sug) if sug in opcoes else 0
                mapa[chave] = st.selectbox(chave, opcoes, index=idx, key=f"map_{chave}")
        try:
            df_total = tratar(bruto, mapa)
        except Exception as erro:  # noqa: BLE001
            st.error(f"Falha no tratamento: {erro}. Revise o mapeamento de colunas.")
            st.stop()
        if df_total.empty:
            st.error("Nenhuma linha válida após o tratamento. Confira as colunas de UF e de valor.")
            st.stop()
        st.success(f"Base carregada: {len(df_total):,} linhas válidas.".replace(",", "."))

    df, ref = filtros(df_total)
    if df.empty:
        st.info("Nenhum dado para os filtros selecionados.")
        return

    st.sidebar.download_button("⬇️ Baixar base tratada (CSV)", df.to_csv(index=False).encode("utf-8-sig"),
                               "afazeres_domesticos_tratado.csv", "text/csv")

    # ---- KPIs ----
    e = estatisticas(df["Horas"])
    fem, mas = achar_sexos(df)
    kpis = [("Média (h/sem)", fmt(e["Média"])), ("Mediana (h/sem)", fmt(e["Mediana (Q2)"])),
            ("IQR", fmt(e["IQR"])), ("Desvio padrão", fmt(e["Desvio padrão"])), ("Outliers", e["Outliers"])]
    if fem and mas:
        mf = df.loc[df["Sexo"] == fem, "Horas"].mean()
        mm = df.loc[df["Sexo"] == mas, "Horas"].mean()
        kpis.append(("Mulheres ÷ Homens", f"{fmt(mf / mm, 2)}x"))
    for col, (rotulo, valor) in zip(st.columns(len(kpis)), kpis):
        col.metric(rotulo, valor)

    abas = st.tabs(["📊 Distribuição", "⚖️ Sexo, raça e UF", "📈 Evolução vs Brasil", "💼 Ocupação",
                    "🧮 Estatísticas", "📰 Notícias", "📝 Interpretação"])

    # ---- 1. Distribuição ----
    with abas[0]:
        esq, dir_ = st.columns(2)
        eixo_x = "Sexo" if "Sexo" in df.columns else None
        fig = px.box(df, x=eixo_x, y="Horas", color=eixo_x, points="all", hover_data=["UF"],
                     title="Boxplot das horas semanais", labels={"Horas": "Horas por semana"})
        esq.plotly_chart(fig, width="stretch")
        fig = px.histogram(df, x="Horas", nbins=20, marginal="box", color=eixo_x,
                           title="Histograma das horas semanais", labels={"Horas": "Horas por semana"})
        dir_.plotly_chart(fig, width="stretch")

    # ---- 2. Sexo, raça e UF ----
    with abas[1]:
        st.markdown("**Pergunta 1:** qual a discrepância média de horas entre homens e mulheres por estado? E por sexo e raça?")
        if "Sexo" in df.columns:
            g = df.groupby(["UF", "Sexo"], as_index=False)["Horas"].mean()
            fig = px.bar(g, x="UF", y="Horas", color="Sexo", barmode="group",
                         title="Horas semanais por sexo e estado", labels={"Horas": "Média de horas por semana"})
            st.plotly_chart(fig, width="stretch")
        if fem and mas:
            p = df.pivot_table(index="UF", columns="Sexo", values="Horas", aggfunc="mean").dropna(subset=[fem, mas])
            p["Diferença M−H (h)"] = p[fem] - p[mas]
            p["Razão M/H"] = p[fem] / p[mas]
            gap = p.reset_index().sort_values("Diferença M−H (h)")
            gap["Grupo"] = np.where(gap["UF"].isin(UFS_PERSONAS), "Estados do cenário", "Outros estados")
            fig = px.bar(gap, x="Diferença M−H (h)", y="UF", orientation="h", color="Grupo",
                         color_discrete_map={"Estados do cenário": "#d62728", "Outros estados": "#9aa5b1"},
                         title="Discrepância média (mulheres − homens) por estado")
            fig.update_layout(height=max(380, 22 * len(gap)))
            st.plotly_chart(fig, width="stretch")
            st.dataframe(gap.drop(columns="Grupo").round(2), width="stretch", hide_index=True)
        else:
            st.info("Para a discrepância por estado, a base precisa ter a coluna de sexo (mulheres e homens).")

        if "Sexo" in df.columns and "Raça" in df.columns:
            d = df.copy()
            d["Raça (grupo)"] = d["Raça"].map(grupo_raca)
            d = d.dropna(subset=["Raça (grupo)"])
            if not d.empty:
                d["Grupo"] = d["Sexo"] + " " + d["Raça (grupo)"]
                g = d.groupby("Grupo", as_index=False)["Horas"].mean().sort_values("Horas")
                fig = px.bar(g, x="Grupo", y="Horas", color="Grupo",
                             title="Horas por sexo e raça (pretas/pardas × brancas)",
                             labels={"Horas": "Média de horas por semana"})
                st.plotly_chart(fig, width="stretch")
        else:
            st.info("Para o recorte por raça, use a tabela do IBGE com sexo e cor ou raça (ex.: Tabela 1.1.1).")

    # ---- 3. Evolução vs Brasil ----
    with abas[2]:
        st.markdown("**Pergunta 2:** como essa divisão evoluiu nos últimos anos nos estados analisados versus a média nacional?")
        if "Ano" in df.columns and df["Ano"].nunique() > 1:
            chaves = ["Ano"] + (["Sexo"] if "Sexo" in df.columns else [])
            uf_ano = df.groupby(chaves + ["UF"], as_index=False)["Horas"].mean().rename(columns={"UF": "Série"})
            nacional = ref.groupby(chaves, as_index=False)["Horas"].mean()
            nacional["Série"] = "Brasil (média de todas as UFs)"
            serie = pd.concat([uf_ano, nacional], ignore_index=True).sort_values("Ano")
            fig = px.line(serie, x="Ano", y="Horas", color="Série", markers=True,
                          facet_col="Sexo" if "Sexo" in serie.columns else None,
                          title="Evolução das horas semanais: estados × Brasil",
                          labels={"Horas": "Média de horas por semana"})
            st.plotly_chart(fig, width="stretch")
            st.caption("A linha do Brasil é a média simples das UFs da base com os mesmos filtros de ano, sexo, raça, "
                       "faixa etária e ocupação. O IBGE também publica o valor nacional oficial, ponderado.")
        else:
            st.info("Selecione mais de um ano (ou use uma base com vários anos) para ver a evolução.")

    # ---- 4. Ocupação ----
    with abas[3]:
        st.markdown("**Pergunta 3:** há diferença significativa entre quem trabalha fora e quem não está ocupado?")
        if "Ocupação" in df.columns and df["Ocupação"].nunique() >= 2:
            cor = "Sexo" if "Sexo" in df.columns else None
            fig = px.box(df, x="Ocupação", y="Horas", color=cor, points="all", hover_data=["UF"],
                         title="Horas semanais por situação na ocupação", labels={"Horas": "Horas por semana"})
            st.plotly_chart(fig, width="stretch")
            tab = df.groupby("Ocupação")["Horas"].agg(["count", "mean", "median", "std"]).round(2)
            tab.columns = ["n", "Média", "Mediana", "Desvio padrão"]
            st.dataframe(tab, width="stretch")
            grupos = [g["Horas"].to_numpy() for _, g in df.groupby("Ocupação")]
            if len(grupos) == 2:
                try:
                    from scipy import stats
                    t, pvalor = stats.ttest_ind(grupos[0], grupos[1], equal_var=False)
                    st.markdown(f"Teste t de Welch: t = {fmt(t, 2)}, p = {pvalor:.4f}. "
                                + ("Diferença estatisticamente significativa (p < 0,05)." if pvalor < 0.05
                                   else "Sem evidência de diferença significativa (p ≥ 0,05)."))
                    st.caption("Cada observação da base é uma média por UF/grupo, não uma pessoa. "
                               "Use o p-valor como apoio, junto com a leitura de média, mediana e boxplot.")
                except ImportError:
                    st.caption("Instale o scipy (pip install scipy) para ver o teste de significância.")
        else:
            st.info("Para esta análise a base precisa ter a situação na ocupação (ocupadas × não ocupadas). "
                    "No IBGE, ela aparece nas tabelas 1.1.2 a 1.1.4 (pessoas ocupadas e não ocupadas).")

    # ---- 5. Estatísticas ----
    with abas[4]:
        if "Sexo" in df.columns:
            tabela = {"Todos": estatisticas(df["Horas"])}
            for s, parte in df.groupby("Sexo"):
                tabela[s] = estatisticas(parte["Horas"])
        else:
            tabela = {"Todos": e}
        st.dataframe(pd.DataFrame(tabela).round(2), width="stretch")
        st.markdown("**Outliers (regra 1,5·IQR)**")
        out = outliers(df)
        if out.empty:
            st.success("Nenhum outlier nos filtros atuais.")
        else:
            st.dataframe(out.sort_values("Horas", ascending=False), width="stretch")
        st.caption("Se a média muda muito ao retirar os outliers, prefira a mediana como medida de referência.")

    # ---- 6. Notícias ----
    with abas[5]:
        st.caption("Reportagens para contextualizar o tema. Resumos feitos pelo grupo a partir das matérias; leia o texto completo no link.")
        for tema, itens in NOTICIAS.items():
            st.subheader(tema)
            for titulo, url, resumo in itens:
                st.markdown(f"**[{titulo}]({url})**  \n{resumo}")
        st.subheader("Imagens ilustrativas")
        st.caption("Envie imagens livres de uso (ex.: Unsplash, Pexels, Agência Brasil) ou cole o endereço de uma imagem.")
        url_img = st.text_input("Endereço (URL) de uma imagem")
        if url_img.strip():
            st.image(url_img.strip(), width="stretch")
        for img in st.file_uploader("Imagens ou infográficos", type=["png", "jpg", "jpeg"],
                                    accept_multiple_files=True) or []:
            st.image(img, width="stretch")

    # ---- 7. Interpretação ----
    with abas[6]:
        st.subheader("Leitura automática dos números")
        for linha in texto_interpretativo(df):
            st.markdown(f"- {linha}")
        st.subheader("Resposta aos gestores (Maria, Fátima, Antônio e Luíza)")
        st.text_area("Como esses números podem orientar políticas para dividir o trabalho de cuidado "
                     "(ex.: creches, cuidado de idosos, campanhas, apoio à renda das mulheres)?",
                     height=140, key="resposta_persona")
        st.info("Referência para conferir sua base (IBGE, PNAD Contínua 2022, Brasil): mulheres 21,3 h e homens 11,7 h por semana.")


if __name__ == "__main__":
    st.set_page_config(page_title="Afazeres Domésticos · IBGE", page_icon="🏠", layout="wide")
    render()
