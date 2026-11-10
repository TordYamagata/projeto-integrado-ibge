import streamlit as st

import pandas as pd

import numpy as np

import plotly.express as px

from pathlib import Path



# ==========================================
# CONFIGURACAO DA PAGINA
# ==========================================




st.title("📚 Alfabetização por Sexo e Raça")

st.caption(

    "Projeto Integrado Python/Matemática | "

    "Censo Demográfico 2022 - IBGE"

)



st.markdown(

    """

    Este dashboard analisa as taxas de alfabetização

    entre homens e mulheres, diferentes grupos de

    cor ou raça e Unidades da Federação.



    **Objetivo:** identificar desigualdades

    educacionais por sexo, raça e território.

    """

)



# ==========================================
# CARREGAMENTO AUTOMATICO
# ==========================================
CAMINHO = (

    Path(__file__).resolve().parent.parent

    / "dados"

    / "alfabetizacao_uf_sexo_raca.csv"

)



@st.cache_data

def carregar_dados():

    df = pd.read_csv(

        CAMINHO,

        encoding="utf-8-sig",

        sep=None,

        engine="python"

    )



    df.columns = df.columns.str.strip()



    obrigatorias = [

        "uf",

        "sexo",

        "cor_raca",

        "populacao_total",

        "populacao_alfabetizada"

    ]



    faltantes = [

        c for c in obrigatorias

        if c not in df.columns

    ]



    if faltantes:

        raise ValueError(

            "Colunas ausentes: "

            + ", ".join(faltantes)

        )



    for coluna in [

        "populacao_total",

        "populacao_alfabetizada"

    ]:

        df[coluna] = pd.to_numeric(

            df[coluna],

            errors="coerce"

        )



    df = df.dropna(subset=obrigatorias).copy()



    df = df[

        (df["populacao_total"] > 0)

        & (df["populacao_alfabetizada"] >= 0)

        & (

            df["populacao_alfabetizada"]

            <= df["populacao_total"]

        )

    ].copy()



    for coluna in ["uf", "sexo", "cor_raca"]:

        df[coluna] = (

            df[coluna].astype(str).str.strip()

        )



    df = df.groupby(

        ["uf", "sexo", "cor_raca"],

        as_index=False

    )[

        ["populacao_total", "populacao_alfabetizada"]

    ].sum()



    df["taxa_alfabetizacao"] = (

        df["populacao_alfabetizada"]

        / df["populacao_total"]

        * 100

    )



    return df





try:

    df = carregar_dados()



except FileNotFoundError:

    st.error(

        "CSV não encontrado! Coloque "

        "'alfabetizacao_uf_sexo_raca.csv' "

        "dentro da pasta dados."

    )

    st.stop()



except Exception as erro:

    st.error(f"Erro ao carregar dados: {erro}")

    st.stop()



if df.empty:

    st.error("O CSV não possui registros válidos.")

    st.stop()



# ==========================================
# VERIFICACAO DA COBERTURA
# ==========================================
ESTADOS = 27

SEXOS = 2

RACAS = 5

TOTAL_ESPERADO = ESTADOS * SEXOS * RACAS



combinacoes = len(df)

ufs_presentes = df["uf"].nunique()



st.sidebar.success("CSV carregado automaticamente!")



if combinacoes < TOTAL_ESPERADO:

    st.warning(

        f"⚠️ Base parcial: {combinacoes} de "

        f"{TOTAL_ESPERADO} combinações esperadas "

        f"de UF, sexo e cor ou raça. "

        "Os resultados representam apenas os "

        "grupos disponíveis no arquivo, não "

        "uma comparação nacional completa."

    )



# ==========================================
# FILTROS LATERAIS
# ==========================================
st.sidebar.header("🔎 Filtros")



ufs = sorted(df["uf"].unique())

sexos = sorted(df["sexo"].unique())

racas = sorted(df["cor_raca"].unique())



uf_escolhida = st.sidebar.multiselect(

    "Unidade da Federação",

    ufs,

    default=ufs

)



sexo_escolhido = st.sidebar.multiselect(

    "Sexo",

    sexos,

    default=sexos

)



raca_escolhida = st.sidebar.multiselect(

    "Cor ou raça",

    racas,

    default=racas

)



filtrado = df[

    df["uf"].isin(uf_escolhida)

    & df["sexo"].isin(sexo_escolhido)

    & df["cor_raca"].isin(raca_escolhida)

].copy()



if filtrado.empty:

    st.warning(

        "Nenhum registro encontrado. "

        "Altere os filtros."

    )

    st.stop()



# ==========================================
# FUNCOES ESTATISTICAS
# ==========================================
def taxa_ponderada(tabela):

    total = tabela["populacao_total"].sum()

    alfabetizada = tabela[

        "populacao_alfabetizada"

    ].sum()



    if total == 0:

        return np.nan



    return alfabetizada / total * 100





def agregar(tabela, grupos):

    resultado = tabela.groupby(

        grupos,

        as_index=False

    )[

        ["populacao_total", "populacao_alfabetizada"]

    ].sum()



    resultado["taxa_alfabetizacao"] = (

        resultado["populacao_alfabetizada"]

        / resultado["populacao_total"]

        * 100

    )



    return resultado





# ==========================================
# INDICADORES PRINCIPAIS
# ==========================================
st.header("📊 Indicadores gerais")



taxa = taxa_ponderada(filtrado)

quantidade = filtrado[

    "populacao_alfabetizada"

].sum()



taxas = filtrado["taxa_alfabetizacao"]



media = taxas.mean()

mediana = taxas.median()

desvio = taxas.std(ddof=1)



c1, c2, c3, c4 = st.columns(4)



c1.metric(

    "Taxa agregada",

    f"{taxa:.2f}%"

)



c2.metric(

    "Média das taxas",

    f"{media:.2f}%"

)



c3.metric(

    "Mediana",

    f"{mediana:.2f}%"

)



c4.metric(

    "Desvio padrão",

    f"{desvio:.2f} p.p."

    if pd.notna(desvio)

    else "N/D"

)



st.caption(

    "A taxa agregada considera as populações "

    "dos registros disponíveis. A média e "

    "a mediana consideram as taxas de cada "

    "combinação UF/sexo/raça, sem ponderação. "

    "As medidas de dispersão são expressas "

    "em pontos percentuais."

)



# ==========================================
# GRAFICO 1 - SEXO
# ==========================================
st.header("👩‍🎓 Alfabetização por sexo")



por_sexo = agregar(

    filtrado,

    ["sexo"]

)



fig_sexo = px.bar(

    por_sexo,

    x="sexo",

    y="taxa_alfabetizacao",

    color="sexo",

    text="taxa_alfabetizacao",

    title="Taxa de alfabetização por sexo",

    labels={

        "sexo": "Sexo",

        "taxa_alfabetizacao": "Taxa (%)"

    }

)



fig_sexo.update_traces(

    texttemplate="%{text:.2f}%",

    textposition="outside"

)



fig_sexo.update_layout(

    yaxis_range=[0, 110]

)



st.plotly_chart(

    fig_sexo,

    use_container_width=True

)



# ==========================================
# GRAFICO 2 - COR OU RACA
# ==========================================
st.header("🌎 Alfabetização por cor ou raça")



por_raca = agregar(

    filtrado,

    ["cor_raca"]

)



fig_raca = px.bar(

    por_raca,

    x="cor_raca",

    y="taxa_alfabetizacao",

    color="cor_raca",

    text="taxa_alfabetizacao",

    title="Comparação entre grupos raciais",

    labels={

        "cor_raca": "Cor ou raça",

        "taxa_alfabetizacao": "Taxa (%)"

    }

)



fig_raca.update_traces(

    texttemplate="%{text:.2f}%",

    textposition="outside"

)



fig_raca.update_layout(

    yaxis_range=[0, 110]

)



st.plotly_chart(

    fig_raca,

    use_container_width=True

)



# ==========================================
# GRAFICO 3 - SEXO E RACA
# ==========================================
st.header("👥 Comparação entre sexo e raça")



sexo_raca = agregar(

    filtrado,

    ["sexo", "cor_raca"]

)



fig_comparacao = px.bar(

    sexo_raca,

    x="cor_raca",

    y="taxa_alfabetizacao",

    color="sexo",

    barmode="group",

    title="Alfabetização por sexo e cor ou raça",

    labels={

        "cor_raca": "Cor ou raça",

        "taxa_alfabetizacao": "Taxa (%)",

        "sexo": "Sexo"

    }

)



st.plotly_chart(

    fig_comparacao,

    use_container_width=True

)



# ==========================================
# GRAFICO 4 - ESTADOS
# ==========================================
st.header("🗺️ Comparação entre estados")



por_uf = agregar(

    filtrado,

    ["uf"]

)



por_uf = por_uf.sort_values(

    "taxa_alfabetizacao",

    ascending=False

)



fig_uf = px.bar(

    por_uf,

    x="uf",

    y="taxa_alfabetizacao",

    color="taxa_alfabetizacao",

    title="Taxas de alfabetização por UF",

    labels={

        "uf": "Estado",

        "taxa_alfabetizacao": "Taxa (%)"

    },

    color_continuous_scale="Blues"

)



st.plotly_chart(

    fig_uf,

    use_container_width=True

)



st.caption(

    "O ranking utiliza somente os grupos "

    "disponíveis em cada UF. Estados com "

    "coberturas diferentes não devem ser "

    "comparados como totais estaduais."

)



# ==========================================
# ESTATISTICA DESCRITIVA
# ==========================================
st.header("📐 Estatística descritiva")



q1 = taxas.quantile(0.25)

q2 = taxas.quantile(0.50)

q3 = taxas.quantile(0.75)



iqr = q3 - q1

amplitude = taxas.max() - taxas.min()

variancia = taxas.var(ddof=1)



moda = taxas.round(2).mode()

moda_valor = (

    ", ".join(moda.astype(str).tolist()[:5])

    if len(moda) < len(taxas)

    else "Sem moda única"

)



estatisticas = pd.DataFrame({

    "Medida": [

        "Média",

        "Mediana",

        "Moda",

        "Primeiro quartil (Q1)",

        "Segundo quartil (Q2)",

        "Terceiro quartil (Q3)",

        "Intervalo interquartil",

        "Amplitude",

        "Variância",

        "Desvio padrão"

    ],

    "Valor": [

        f"{media:.2f}",

        f"{mediana:.2f}",

        moda_valor,

        f"{q1:.2f}",

        f"{q2:.2f}",

        f"{q3:.2f}",

        f"{iqr:.2f}",

        f"{amplitude:.2f}",

        f"{variancia:.2f}"

        if pd.notna(variancia) else "N/D",

        f"{desvio:.2f}"

        if pd.notna(desvio) else "N/D"

    ]

})



st.dataframe(

    estatisticas,

    use_container_width=True,

    hide_index=True

)



# ==========================================
# BOXPLOT E HISTOGRAMA
# ==========================================
st.header("📈 Distribuição das taxas")



col1, col2 = st.columns(2)



with col1:

    fig_box = px.box(

        filtrado,

        y="taxa_alfabetizacao",

        points="all",

        title="Boxplot das taxas",

        labels={

            "taxa_alfabetizacao": "Taxa (%)"

        }

    )



    st.plotly_chart(

        fig_box,

        use_container_width=True

    )



with col2:

    fig_hist = px.histogram(

        filtrado,

        x="taxa_alfabetizacao",

        nbins=15,

        title="Histograma das taxas",

        labels={

            "taxa_alfabetizacao": "Taxa (%)",

            "count": "Frequência"

        }

    )



    fig_hist.add_vline(

        x=media,

        line_dash="dash",

        annotation_text="Média"

    )



    fig_hist.add_vline(

        x=mediana,

        line_dash="dot",

        annotation_text="Mediana"

    )



    st.plotly_chart(

        fig_hist,

        use_container_width=True

    )



# ==========================================
# OUTLIERS
# ==========================================
st.header("🔍 Identificação de outliers")



limite_inferior = q1 - 1.5 * iqr

limite_superior = q3 + 1.5 * iqr



outliers = filtrado[

    (filtrado["taxa_alfabetizacao"] < limite_inferior)

    | (filtrado["taxa_alfabetizacao"] > limite_superior)

]



st.write(

    f"Quantidade de possíveis outliers: "

    f"**{len(outliers)}**"

)



if not outliers.empty:

    st.dataframe(

        outliers[

            ["uf", "sexo", "cor_raca", "taxa_alfabetizacao"]

        ],

        use_container_width=True,

        hide_index=True

    )

else:

    st.info(

        "Nenhum outlier identificado "

        "pela regra de 1,5 × IQR."

    )



# ==========================================
# INTERPRETACAO DOS RESULTADOS
# ==========================================
st.header("📝 Interpretação dos resultados")



if len(por_raca) >= 2:

    maior = por_raca.loc[

        por_raca["taxa_alfabetizacao"].idxmax()

    ]



    menor = por_raca.loc[

        por_raca["taxa_alfabetizacao"].idxmin()

    ]



    diferenca = (

        maior["taxa_alfabetizacao"]

        - menor["taxa_alfabetizacao"]

    )



    st.write(

        f"Entre os grupos disponíveis, "

        f"**{maior['cor_raca']}** apresenta "

        f"a maior taxa ({maior['taxa_alfabetizacao']:.2f}%), "

        f"enquanto **{menor['cor_raca']}** apresenta "

        f"a menor ({menor['taxa_alfabetizacao']:.2f}%)."

    )



    st.write(

        f"A diferença observada é de "

        f"**{diferenca:.2f} pontos percentuais**."

    )



if len(por_sexo) == 2:

    diferenca_sexo = (

        por_sexo["taxa_alfabetizacao"].max()

        - por_sexo["taxa_alfabetizacao"].min()

    )



    st.write(

        f"A diferença entre as taxas dos "

        f"dois sexos é de "

        f"**{diferenca_sexo:.2f} pontos percentuais**."

    )



st.info(

    "As interpretações são descritivas e "

    "dependem da cobertura dos dados. "

    "Diferenças observadas não demonstram "

    "por si só relações de causa e efeito."

)



# ==========================================
# TABELA FINAL
# ==========================================
st.header("📋 Base de dados utilizada")



st.dataframe(

    filtrado,

    use_container_width=True,

    hide_index=True

)



st.download_button(

    "📥 Baixar dados filtrados",

    data=filtrado.to_csv(

        index=False

    ).encode("utf-8-sig"),

    file_name="alfabetizacao_filtrada.csv",

    mime="text/csv"

)



# ==========================================
# RODAPE
# ==========================================
st.divider()



st.caption(

    "Fonte: IBGE - Censo Demográfico 2022. "

    "Projeto Integrado Python e Matemática. "

    "Análises condicionadas à cobertura "

    "da base disponibilizada."

)
