# -*- coding: UTF-8 -*- 
"""Import modules"""
import datetime as dt

import matplotlib.pyplot as plt
import numpy as np
import yfinance as yf
from numpy import linalg as LA


class MonteCarlo:
    """Monte Carlo
    Simulation class"""

    # import local modules
    from src.static import StaticVariables
    static = StaticVariables()

lista_acoes = static.financials + static.electricals + static.others

#
retornos = "ADICIONAR VETOR DE RETORNOS"
matriz_cov = retornos.cov()
#

pesos_carteira = np.full(len(lista_acoes), 1/len(lista_acoes))
numero_acoes = len(lista_acoes)

num_sim = 10_000
dias_projetados = 252
capital_inicial = 1000

retorno_medio = retornos.mean(axis=0).to_numpy() # transforma em vetor -> aqui entra o vetor de retornos do dy
matriz_retorno_medio = retorno_medio * np.ones(shape=(dias_projetados, numero_acoes)) # gera matriz cheia dos retornos médios

L = LA.cholesky(matriz_cov) # triangulariz cov_matrix para correlacionar retornos sintéticos


retornos_carteira = np.zeros([dias_projetados, num_sim])
montante_final = np.zeros(num_sim)

for s in range(num_sim):
    Rpdf = np.random.normal(size=(dias_projetados, numero_acoes))

    retornos_sinteticos = matriz_retorno_medio + np.inner(Rpdf, L)

    retornos_carteira[:, s] = np.cumprod(np.inner(pesos_carteira,
                                                  retornos_sinteticos) + 1) * capital_inicial
    
    montante_final[s] = retornos_carteira[-1, s]


retornos_carteira

montante_99 = str(np.percentile(montante_final, 1))
montante_95 = str(np.percentile(montante_final, 5))
montante_mediano = str(np.percentile(montante_final, 50))
cenarios_lucro = str((len(montante_final[montante_final > 1000]) / len(montante_final)) * 100) + "%"


print(f"""
        Ao investir R$ 1000,00 na carteira {lista_acoes},
        podemos esperar esses resultados para os próximos 3 anos, utilizando o método de Monte Carlo com 10 mil simulações:

        Com 50% de probabilidade, o montante será maior que {montante_mediano};
        
        Com 95% de probabilidade, o montante será maior que {montante_95};
        
        Com 99% de probabilidade, o montante será maior que {montante_99}.

        Em {cenarios_lucro} dos cenários, foi possível obter lucro no próximo ano.
      
      """)

config = dict(histtype="stepfilled", alpha=0.8, density=False, bins=150)
fig, ax = plt.subplots()
ax.hist(montante_final, ** config)
ax.xaxis.set_major_formatter("R${x:.0f}")
plt.title("Distribuição de montantes finanis com simulação de MC")
plt.xlabel("Montante final (R$)")
plt.ylabel("Frequência")