"""Indicador Pessoas Indígenas — Censo 2022, módulo do dashboard integrado."""
from pathlib import Path
import unicodedata
import pandas as pd
import streamlit as st
import plotly.express as px

ROOT = Path(__file__).resolve().parent.parent
DADOS = ROOT / 'dados'

st.title('Pessoas Indígenas no Brasil — Censo 2022')
st.caption('Projeto Integrado Python/Matemática | Fonte: IBGE — Censo Demográfico 2022')

@st.cache_data
def carregar(nome):
    caminhos = [DADOS / nome, Path(__file__).resolve().parent / nome]
    for caminho in caminhos:
        if caminho.is_file():
            try:
                return pd.read_csv(caminho, sep=None, engine='python', encoding='utf-8-sig')
            except Exception as exc:
                st.error(f'Não foi possível ler {nome}: {exc}')
                return None
    return None

def normalizar(texto):
    texto = unicodedata.normalize('NFKD', str(texto))
    texto = ''.join(c for c in texto if not unicodedata.combining(c))
    return texto.casefold().strip().replace('_', ' ')

def identificar_coluna(df, termos):
    for termo in termos:
        for coluna in df.columns:
            if normalizar(termo) == normalizar(coluna):
                return coluna
    for termo in termos:
        for coluna in df.columns:
            if normalizar(termo) in normalizar(coluna):
                return coluna
    return None

def numeros(serie):
    if pd.api.types.is_numeric_dtype(serie):
        return pd.to_numeric(serie, errors='coerce')
    s = serie.astype('string').str.strip().str.replace(' ', '', regex=False)
    # Inteiros com separador de milhar ou valores com vírgula decimal.
    s = s.str.replace(r'(?<=\d)\.(?=\d{3}(?:\D|$))', '', regex=True)
    s = s.str.replace(',', '.', regex=False)
    return pd.to_numeric(s, errors='coerce')

st.sidebar.header('Filtros — Pessoas indígenas')
abas = st.tabs(['Visão geral e UFs', 'Urbano × rural', 'Etnias', 'Metodologia'])

with abas[0]:
    df = carregar('populacao_uf_2022.csv')
    if df is None or df.empty:
        st.warning('Base populacao_uf_2022.csv ausente ou vazia. Verifique a pasta dados/.')
    else:
        uf = identificar_coluna(df, ['sigla_uf', 'uf', 'unidade da federação', 'estado'])
        valor = identificar_coluna(df, ['populacao_indigena', 'população indígena', 'pessoas indígenas', 'quantidade'])
        if uf is None or valor is None or uf == valor:
            st.warning('Colunas de UF e população não identificadas: ' + ', '.join(map(str, df.columns)))
        else:
            base = df.copy()
            base[valor] = numeros(base[valor])
            base = base.dropna(subset=[uf, valor])
            base = base.groupby(uf, as_index=False)[valor].sum()
            if base[uf].nunique() != 27:
                st.warning(f'Esta base possui {base[uf].nunique()} UFs distintas; confira a cobertura antes de apresentar resultados nacionais.')
            escolhas = sorted(base[uf].astype(str).unique())
            selecionadas = st.sidebar.multiselect('UF', escolhas, default=escolhas, key='indigenas_uf')
            base = base[base[uf].astype(str).isin(selecionadas)]
            if base.empty:
                st.info('Selecione pelo menos uma UF.')
            else:
                serie = base.set_index(uf)[valor]
                st.metric('População indígena nas UFs selecionadas', f'{serie.sum():,.0f}'.replace(',', '.'))
                fig = px.bar(base.sort_values(valor, ascending=False), x=uf, y=valor, title='População indígena por UF (2022)')
                st.plotly_chart(fig, width='stretch')
                st.subheader('Estatística descritiva — população indígena por UF')
                q1, mediana, q3 = serie.quantile([0.25, 0.5, 0.75])
                moda = serie.mode()
                estat = {
                    'Média': serie.mean(), 'Mediana': mediana,
                    'Moda': ', '.join(f'{v:,.0f}'.replace(',', '.') for v in moda) if len(moda) < len(serie) else 'Sem moda única',
                    'Q1': q1, 'Q3': q3, 'IQR': q3-q1,
                    'Amplitude': serie.max()-serie.min(),
                    'Variância (populacional)': serie.var(ddof=0),
                    'Desvio padrão (populacional)': serie.std(ddof=0)
                }
                st.dataframe(pd.DataFrame(estat.items(), columns=['Medida', 'Valor']), hide_index=True)
                st.plotly_chart(px.box(x=serie, labels={'x': 'Pessoas indígenas por UF'}, title='Boxplot da população por UF'), width='stretch')
                st.caption('As estatísticas descrevem UFs, não indivíduos. Outliers podem ser analisados pela regra de 1,5 × IQR.')

with abas[1]:
    df = carregar('urbano_rural_brasil_2022.csv')
    if df is None or df.empty:
        st.warning('Arquivo urbano_rural_brasil_2022.csv ausente ou vazio.')
    else:
        obrigatorias = {'localizacao', 'situacao_domicilio', 'populacao_indigena'}
        if not obrigatorias.issubset(df.columns):
            st.warning('O CSV deve ter as colunas: localizacao, situacao_domicilio, populacao_indigena.')
            st.dataframe(df.head(), hide_index=True)
        else:
            base = df[df['localizacao'].astype(str).str.strip().str.casefold() == 'total'].copy()
            base['situacao_domicilio'] = base['situacao_domicilio'].astype(str).str.strip().str.title()
            base['populacao_indigena'] = numeros(base['populacao_indigena'])
            base = base[base['situacao_domicilio'].isin(['Urbana', 'Rural'])].dropna(subset=['populacao_indigena'])
            agregado = base.groupby('situacao_domicilio', as_index=False)['populacao_indigena'].sum()
            if set(agregado['situacao_domicilio']) != {'Urbana', 'Rural'}:
                st.warning('Não foi possível localizar as duas categorias Urbana e Rural.')
            else:
                total = int(agregado['populacao_indigena'].sum())
                st.metric('População indígena no Brasil', f'{total:,}'.replace(',', '.'))
                st.plotly_chart(px.bar(agregado, x='situacao_domicilio', y='populacao_indigena', color='situacao_domicilio', text_auto=True, title='População indígena urbana × rural — Brasil, 2022'), width='stretch')
                st.plotly_chart(px.pie(agregado, names='situacao_domicilio', values='populacao_indigena', title='Participação por situação do domicílio'), width='stretch')
                st.dataframe(agregado, hide_index=True)
                st.caption('Comparação nacional; localização em Terra Indígena e situação urbana/rural são dimensões diferentes.')

with abas[2]:
    df = carregar('etnias_2022.csv')
    if df is None or df.empty:
        st.warning('Base etnias_2022.csv ausente ou vazia.')
    else:
        etnia = identificar_coluna(df, ['etnia', 'povo', 'grupo indígena'])
        valor = identificar_coluna(df, ['populacao_indigena', 'população', 'pessoas', 'quantidade', 'total'])
        if etnia is None or valor is None or etnia == valor:
            st.warning('O arquivo precisa conter colunas de etnia e quantidade. Colunas: ' + ', '.join(map(str, df.columns)))
        else:
            base = df.copy()
            base[valor] = numeros(base[valor])
            base = base.dropna(subset=[etnia, valor])
            ranking = base.groupby(etnia, as_index=False)[valor].sum().nlargest(15, valor)
            st.info('Confira a cobertura da base de etnias: o arquivo do projeto pode ser parcial.')
            st.plotly_chart(px.bar(ranking.sort_values(valor), x=valor, y=etnia, orientation='h', title='Etnias registradas na base — Brasil, 2022'), width='stretch')
            st.dataframe(ranking, hide_index=True)
            st.caption('Fonte: IBGE, Censo 2022 — https://www.ibge.gov.br/brasil-indigena/. Declarações múltiplas de etnia exigem cuidado na soma.')

with abas[3]:
    st.markdown('''### Fonte e cuidados de interpretação
- Fonte: **IBGE, Censo Demográfico 2022**. Confira os arquivos originais antes da apresentação.
- População por UF, etnias e situação do domicílio precisam usar recortes compatíveis.
- **Urbano/rural** não significa **dentro/fora de Terra Indígena**.
- A base nacional urbano/rural não permite inferir valores por UF.
- As medidas estatísticas descrevem as unidades analisadas.
- Arquivos incompletos não são preenchidos com números inventados.

**Fonte:** https://www.ibge.gov.br/estatisticas/sociais/populacao/22827-censo-demografico-2022.html
''')
