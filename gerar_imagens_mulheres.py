import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

os.makedirs("imagens", exist_ok=True)
ROXO = "#6250d6"
VERDE = "#1baf7a"
AZUL = "#2a78d6"
LARANJA = "#eb6834"
ESCURO = "#0d366b"
TEXTO = "#52514e"

base = pd.read_csv("dados/mulheres_municipios.csv")
resumo = base.groupby("ano")[["resp_mulheres", "resp_homens"]].sum()
resumo["mulheres"] = resumo["resp_mulheres"] / (resumo["resp_mulheres"] + resumo["resp_homens"]) * 100
resumo["homens"] = 100 - resumo["mulheres"]

fig, ax = plt.subplots(figsize=(7, 3.6), dpi=150)
anos = [str(a) for a in resumo.index]
ax.barh(anos, resumo["mulheres"], color=ROXO, height=0.55)
ax.barh(anos, resumo["homens"], left=resumo["mulheres"], color=VERDE, height=0.55)
for i, (m, h) in enumerate(zip(resumo["mulheres"], resumo["homens"])):
    ax.text(m / 2, i, f"Mulheres\n{m:.1f}%".replace(".", ","), ha="center", va="center", color="white", fontsize=10, fontweight="bold")
    ax.text(m + h / 2, i, f"Homens\n{h:.1f}%".replace(".", ","), ha="center", va="center", color="white", fontsize=10, fontweight="bold")
ax.axvline(50, color="white", linewidth=1.5, linestyle="--")
ax.set_xlim(0, 100)
ax.set_xticks([])
ax.set_title("Quem é a pessoa responsável pelo domicílio?", fontsize=12, loc="left")
ax.spines[["top", "right", "bottom", "left"]].set_visible(False)
ax.tick_params(axis="y", length=0, labelsize=11)
fig.tight_layout()
fig.savefig("imagens/chefia_feminina.png")
plt.close(fig)

dados = np.concatenate([np.random.default_rng(7).lognormal(7.6, 0.35, 300), [5200, 5900, 7000]])
q1, mediana, q3 = np.percentile(dados, [25, 50, 75])

fig, ax = plt.subplots(figsize=(7, 3.6), dpi=150)
ax.boxplot(dados, vert=False, widths=0.45, patch_artist=True,
           boxprops={"facecolor": "#cde2fb", "color": AZUL},
           medianprops={"color": ESCURO, "linewidth": 2},
           whiskerprops={"color": AZUL}, capprops={"color": AZUL},
           flierprops={"marker": "o", "markerfacecolor": LARANJA, "markeredgecolor": LARANJA, "markersize": 6})
ax.annotate("Q1 (25%)", xy=(q1, 1.23), xytext=(q1 - 600, 1.45), arrowprops={"arrowstyle": "->"}, fontsize=9)
ax.annotate("Mediana (50%)", xy=(mediana, 1.23), xytext=(mediana - 200, 1.55), arrowprops={"arrowstyle": "->"}, fontsize=9)
ax.annotate("Q3 (75%)", xy=(q3, 1.23), xytext=(q3 + 300, 1.45), arrowprops={"arrowstyle": "->"}, fontsize=9)
ax.annotate("", xy=(q1, 0.7), xytext=(q3, 0.7), arrowprops={"arrowstyle": "<->", "color": ESCURO})
ax.text((q1 + q3) / 2, 0.58, "IQR = Q3 − Q1", ha="center", fontsize=9, color=ESCURO)
ax.text(dados.max(), 0.78, "Outliers:\nacima de Q3 + 1,5 × IQR", ha="right", fontsize=9, color=LARANJA)
ax.set_yticks([])
ax.set_ylim(0.4, 1.75)
ax.set_xlabel("Valor", color=TEXTO)
ax.set_title("Como ler um boxplot", fontsize=12, loc="left")
ax.spines[["top", "right", "left"]].set_visible(False)
fig.tight_layout()
fig.savefig("imagens/como_ler_boxplot.png")
plt.close(fig)

print("imagens prontas na pasta imagens/")
