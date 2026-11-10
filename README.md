# Números que Falam — Dashboard Integrado IBGE

Estrutura inicial de integração dos cinco projetos individuais de Python e Matemática.

## Preparação

1. Instale Python e Git no computador.
2. Coloque `app.py`, `baixar_projetos.py` e `requirements.txt` na mesma pasta.
3. No terminal dessa pasta, execute:

```bash
python baixar_projetos.py
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Estrutura esperada

```text
app.py
baixar_projetos.py
requirements.txt
projetos/
  projeto-indigenas-ibge/
  analise_rendimento/
  Projeto-Integrado-Sara/
  MULHERES/
  alfabetizacao-ibge/
```

## Importante

Este é um **esqueleto de integração**, não uma integração testada dos cinco trabalhos. O aplicativo identifica automaticamente os módulos com `app.py` na raiz. Projetos cujo `app.py` esteja em subpasta ou apenas em ZIP precisarão ser reorganizados. Os scripts originais também podem precisar de ajustes nos caminhos dos arquivos CSV, na configuração de página do Streamlit (`st.set_page_config`) e em dependências adicionais. Mantenha as fontes e a autoria de cada módulo.

Se os repositórios tiverem dependências próprias, consolide-as em `requirements.txt` após verificar cada projeto. Para publicar no Streamlit Cloud, envie a pasta completa ao GitHub (incluindo os CSVs permitidos) e configure `app.py` como arquivo principal.
