# Análise descritiva: Mulheres no Brasil

**Indicador 4** · Fonte: IBGE, Censo Demográfico 2010 e 2022 (Agregados por Setores Censitários)

O dashboard trabalha com três medidas, calculadas para cada um dos 5.570 municípios:
1. **Mulheres na população (%)**: mulheres ÷ moradores × 100, com filtro por faixa etária.
2. **Domicílios chefiados por mulheres (%)**: lares em que a pessoa responsável é mulher.
3. **Mulheres por cor ou raça (%)**: parte das mulheres de cada cor ou raça (só 2022).

## 1. Mulheres na população (2022)

| Medida | Valor |
|---|---|
| Brasil todo (cada pessoa conta uma vez) | 51,58% |
| Média dos municípios | 50,06% |
| Mediana dos municípios | 50,13% |
| Moda | 50% |
| Q1 e Q3 | 49,23% e 50,97% |
| IQR | 1,74 p.p. |
| Amplitude | 22,02 p.p. (de 32,68% em Iaras-SP a 54,71% em Santos-SP) |
| Desvio padrão | 1,36 p.p. |
| Outliers (1,5 × IQR) | 42 abaixo de 46,63% e 15 acima de 53,58% |

**Leitura**
- No Brasil todo as mulheres são 51,6%, mas no município típico ficam perto de 50%. Isso acontece porque as
  **cidades grandes têm mais mulheres** (Santos, Salvador, Recife, Niterói, Rio, Porto Alegre estão entre os outliers de cima),
  e elas pesam mais quando cada pessoa conta uma vez.
- Os **outliers de baixo** são quase todos do interior de São Paulo (Iaras, Álvaro de Carvalho, Itirapina, Riolândia).
  Vários abrigam presídios, e a população presa, quase toda masculina, entra na contagem do Censo.
- **Idade:** os homens são maioria até os 19 anos. As mulheres passam a ser maioria a partir dos 25 a 29 anos e chegam
  a 57,9% entre quem tem 70 anos ou mais, porque vivem mais.
- **2010 → 2022:** a participação feminina subiu de 51,05% para 51,58%, e subiu em todas as UFs.
  Rio de Janeiro tem a maior proporção e Mato Grosso a menor, as duas acima de 49,7%.
- A distribuição tem **assimetria negativa** (−1,03): a cauda comprida fica à esquerda, puxada pelos municípios
  com poucas mulheres. Por isso a média (50,06%) fica um pouco abaixo da mediana (50,13%).

## 2. Domicílios chefiados por mulheres (2022)

| Medida | Valor |
|---|---|
| Brasil todo | 49,13% (era 38,73% em 2010) |
| Mediana dos municípios | 45,68% (era 33,19% em 2010) |
| Média dos municípios | 44,92% |
| Q1 e Q3 | 40,18% e 50,40% |
| Desvio padrão | 7,70 p.p. |
| Outliers | 47 abaixo e 4 acima |
| Mínimo e máximo | 15,44% em União da Serra-RS e 70,14% em Cacimbas-PB |

**Leitura**
- Em 12 anos, a chefia feminina subiu mais de 10 pontos e hoje quase metade dos lares tem uma mulher como responsável.
- É maior no **Nordeste** (mediana de 50,4%) e menor no **Sul** (41,2%). Pernambuco lidera entre as UFs, com 53,9%.
- Dos 47 outliers de baixo, 38 ficam no Rio Grande do Sul e em Santa Catarina: municípios pequenos e rurais, onde a
  chefia masculina ainda é a regra.

## 3. Mulheres por cor ou raça (2022)

| Região | Brancas | Pretas | Pardas | Pretas + pardas |
|---|---|---|---|---|
| Norte | 21,5% | 7,9% | 67,6% | 75,5% |
| Nordeste | 27,3% | 12,4% | 59,7% | 72,1% |
| Centro-Oeste | 38,1% | 8,4% | 52,3% | 60,7% |
| Sudeste | 51,2% | 10,2% | 38,0% | 48,2% |
| Sul | 73,8% | 4,7% | 21,0% | 25,7% |
| **Brasil** | **44,5%** | **9,7%** | **45,0%** | **54,6%** |

**Leitura:** mais da metade das brasileiras é preta ou parda (54,6%), mas a composição muda muito entre as regiões:
três em cada quatro mulheres do Norte são negras, contra uma em cada quatro no Sul.
No Norte, 2,9% das mulheres são indígenas, a maior proporção do país.

## Recomendações para os gestores
- Políticas para idosos atendem principalmente mulheres, porque elas são a maioria a partir dos 60 anos.
- Programas de renda, moradia e creche devem considerar a mulher como a responsável pela casa em quase metade dos lares,
  e em mais da metade no Nordeste.
- Políticas para mulheres precisam do recorte de cor ou raça de cada território, que muda muito entre as regiões.
- Os outliers devem ser conferidos caso a caso: presídios e municípios muito pequenos distorcem os percentuais.

## Limitações
- A unidade é o município: média, mediana e quartis mostram como os municípios variam entre si.
- Em setores muito pequenos o IBGE esconde valores por sigilo. Eles ficam de fora (cerca de 0,4% das mulheres de 2022).
- Cor ou raça por sexo só foi usada em 2022.
