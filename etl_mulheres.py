import os
import urllib.request
import pandas as pd

PASTA_BRUTOS = "dados/brutos"
ARQUIVO_FINAL = "dados/mulheres_municipios.csv"
LINK = "https://github.com/ipea/censobr_prep_data/releases/download/v1.0.0/"
ARQUIVO_2022 = "2022_tracts_Pessoas_v1.0.0.parquet"
ARQUIVO_2010 = "2010_tracts_Pessoa_v1.0.0.parquet"

SIGLAS = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL", 28: "SE", 29: "BA",
    31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS",
    50: "MS", 51: "MT", 52: "GO", 53: "DF",
}

FAIXAS = ["0_4", "5_9", "10_14", "15_19", "20_24", "25_29", "30_39", "40_49", "50_59", "60_69", "70_mais"]
LIMITES = [(0, 4), (5, 9), (10, 14), (15, 19), (20, 24), (25, 29), (30, 39), (40, 49), (50, 59), (60, 69), (70, 100)]
RACAS = ["branca", "preta", "amarela", "parda", "indigena"]


def baixar_brutos():
    os.makedirs(PASTA_BRUTOS, exist_ok=True)
    for nome in [ARQUIVO_2022, ARQUIVO_2010]:
        caminho = os.path.join(PASTA_BRUTOS, nome)
        if not os.path.exists(caminho):
            print("baixando", nome)
            urllib.request.urlretrieve(LINK + nome, caminho)


def situacao(codigo):
    if codigo <= 3:
        return "Urbana"
    return "Rural"


def montar_2022():
    colunas_m = [f"demografia_V{1020 + i:05d}" for i in range(11)]
    colunas_h = [f"demografia_V{1009 + i:05d}" for i in range(11)]
    colunas_raca = [f"raca_V{1327 + i:05d}" for i in range(5)]
    usar = ["name_region", "code_state", "code_muni", "name_muni", "code_situacao",
            "parentesco_V01062", "parentesco_V01063"] + colunas_m + colunas_h + colunas_raca
    bruto = pd.read_parquet(os.path.join(PASTA_BRUTOS, ARQUIVO_2022), columns=usar)

    tabela = pd.DataFrame({
        "ano": 2022,
        "regiao": bruto["name_region"].astype(str),
        "uf": bruto["code_state"].astype(int).map(SIGLAS),
        "cod_municipio": bruto["code_muni"].astype(int),
        "municipio": bruto["name_muni"].astype(str),
        "situacao": bruto["code_situacao"].astype(int).apply(situacao),
    })
    for i, faixa in enumerate(FAIXAS):
        tabela["mulheres_" + faixa] = pd.to_numeric(bruto[colunas_m[i]], errors="coerce")
        tabela["homens_" + faixa] = pd.to_numeric(bruto[colunas_h[i]], errors="coerce")
    tabela["resp_mulheres"] = pd.to_numeric(bruto["parentesco_V01063"], errors="coerce")
    tabela["resp_homens"] = pd.to_numeric(bruto["parentesco_V01062"], errors="coerce")
    for i, raca in enumerate(RACAS):
        tabela["mulheres_" + raca] = pd.to_numeric(bruto[colunas_raca[i]], errors="coerce")
    return tabela


def montar_2010(nomes):
    def coluna_idade(prefixo, idade):
        if idade == 0:
            return f"{prefixo}_V022"
        return f"{prefixo}_V{34 + idade:03d}"

    usar = ["name_region", "abbrev_state", "code_muni", "code_situacao", "pessoa11_V003", "pessoa12_V003"]
    for idade in range(101):
        usar.append(coluna_idade("pessoa11", idade))
        usar.append(coluna_idade("pessoa12", idade))
    bruto = pd.read_parquet(os.path.join(PASTA_BRUTOS, ARQUIVO_2010), columns=usar)
    bruto = bruto.dropna(subset=["code_muni"])

    tabela = pd.DataFrame({
        "ano": 2010,
        "regiao": bruto["name_region"].astype(str),
        "uf": bruto["abbrev_state"].astype(str),
        "cod_municipio": bruto["code_muni"].astype(int),
        "situacao": bruto["code_situacao"].astype(int).apply(situacao),
    })
    tabela["municipio"] = tabela["cod_municipio"].map(nomes)
    for faixa, (inicio, fim) in zip(FAIXAS, LIMITES):
        cols_m = [coluna_idade("pessoa12", i) for i in range(inicio, fim + 1)]
        cols_h = [coluna_idade("pessoa11", i) for i in range(inicio, fim + 1)]
        tabela["mulheres_" + faixa] = bruto[cols_m].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=1)
        tabela["homens_" + faixa] = bruto[cols_h].apply(pd.to_numeric, errors="coerce").sum(axis=1, min_count=1)
    tabela["resp_mulheres"] = pd.to_numeric(bruto["pessoa12_V003"], errors="coerce")
    tabela["resp_homens"] = pd.to_numeric(bruto["pessoa11_V003"], errors="coerce")
    for raca in RACAS:
        tabela["mulheres_" + raca] = float("nan")
    return tabela


baixar_brutos()

setores22 = montar_2022()
nomes = setores22.drop_duplicates("cod_municipio").set_index("cod_municipio")["municipio"]
setores10 = montar_2010(nomes)

setores = pd.concat([setores10, setores22])
contagens = [c for c in setores.columns if c.startswith(("mulheres_", "homens_", "resp_"))]

chaves = ["ano", "regiao", "uf", "cod_municipio", "municipio", "situacao"]
final = setores.groupby(chaves, as_index=False)[contagens].sum(min_count=1)
for col in contagens:
    final[col] = final[col].round().astype("Int64")

os.makedirs("dados", exist_ok=True)
final.to_csv(ARQUIVO_FINAL, index=False, encoding="utf-8-sig")
print("pronto:", ARQUIVO_FINAL, final.shape)
