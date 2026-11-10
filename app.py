
import streamlit as st
from pathlib import Path

st.set_page_config(
    page_title="Números que Falam | IBGE",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

BASE_DIR = Path(__file__).resolve().parent

PAGINAS = [
    ("Pessoas indígenas", "indigenas.py", "🌎"),
    ("Rendimento", "rendimento.py", "💰"),
    ("Indicador da Sara", "indicador_sara.py", "📈"),
    ("Mulheres", "mulheres.py", "👩"),
    ("Alfabetização", "alfabetizacao.py", "📚"),
]

def criar_pagina(nome, arquivo, icone):
    caminho = BASE_DIR / "paginas" / arquivo

    if caminho.is_file():
        return st.Page(
            str(caminho),
            title=nome,
            icon=icone
        )

    return None

paginas_disponiveis = []
paginas_ausentes = []

for nome, arquivo, icone in PAGINAS:
    pagina = criar_pagina(nome, arquivo, icone)

    if pagina is not None:
        paginas_disponiveis.append(pagina)
    else:
        paginas_ausentes.append(arquivo)


def inicio():
    st.title("📊 Números que Falam")
    st.subheader("Descobrindo o Brasil")
    st.write("Projeto Integrado Python e Matemática | IBGE")

    st.info(
        "Selecione um indicador abaixo ou utilize "
        "o menu lateral para navegar."
    )

    st.markdown("### Indicadores demográficos")

    for i in range(0, len(paginas_disponiveis), 2):
        colunas = st.columns(2)

        for j, coluna in enumerate(colunas):
            indice = i + j

            if indice < len(paginas_disponiveis):
                pagina = paginas_disponiveis[indice]

                with coluna:
                    st.page_link(
                        pagina,
                        label=pagina.title,
                        icon=pagina.icon,
                        use_container_width=True
                    )

    st.divider()
    st.caption(
        "Fonte: IBGE | Projeto Integrado Python e Matemática"
    )


pagina_inicial = st.Page(
    inicio,
    title="Página inicial",
    icon="🏠",
    default=True
)

navegacao = st.navigation(
    {
        "Início": [pagina_inicial],
        "Indicadores": paginas_disponiveis
    },
    position="sidebar"
)

if paginas_ausentes:
    st.sidebar.warning(
        "Arquivos não encontrados: "
        + ", ".join(paginas_ausentes)
    )

navegacao.run()
