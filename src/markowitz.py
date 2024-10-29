# -*- coding: UTF-8 -*-
"""Import modules"""
import yfinance as yf
import numpy as np 
import matplotlib.pyplot as plt 
import datetime as dt 
import pandas as pd
from scipy.optimize import minimize 
import matplotlib.ticker as mtick


class Mark:
    """Markowitz model
    class"""

    def __init__(self):
        """Initialize instance"""

        # import local modules

        from src.static import StaticVariables

        self.static = StaticVariables()
        self.begin = dt.date(2017, 1, 1)
        self.end = dt.date(2023, 12, 31)

    def __repr__(self):
        """ Class representation """

        return """ Markowitz Model Optimizer """

    def __str__(self): 
        """ String representation """

        return """ Markowitz Model Optimizer """
    
    def __call__(self):
        """execute class
        routine"""

        self.__transform_data()
        self._get_results()


        """O uso do retorno logarítmico lineariza a nossa relação de retorno e,
            dessa forma, podemos acumular retorno apenas somando-os

            obs: depois voltaremos para o retorno aritmético para que possamos
            ter noção da sensibilidade do retorno de fato"""

        """Uma ideia para projetar retornos futuros sem ser pela média passada seria justamente utilizar
            a TIR, a taxa interna de rentabilidade lá do Valuation da companhia
        """


    def __optimize(self):
        """Download data"""


        # important initial configurations
        dy_data = pd.read_excel(self.static.data_dy_mean)
        dy_mad_data = pd.read_excel(self.static.data_dy_mad)
        price_mad_data = pd.read_excel(self.static.data_price_mad)

        weight_vector = self.__get_weighs()
        dy_mad_vector = np.array(dy_mad_data["dy_mad"])
        price_mad_vector = np.array(price_mad_data["pr_mad"])

        dy_mad_indice = float(sum(weight_vector * dy_mad_vector))
        pr_mad_indice = float(sum(weight_vector * price_mad_vector))

        financials = self.static.financials
        electricals = self.static.electricals
        others = self.static.others

        all_assets = financials + electricals + others

        num_carteiras = 100_000

        tabela_ret_esp = np.zeros(num_carteiras)
        tabela_vols_esp = np.zeros(num_carteiras)

        tabela_sharpe = np.zeros(num_carteiras)
        tabela_pesos = np.zeros((num_carteiras, len(lista_acoes)))

        for sample_wallet in range(num_carteiras):

            pesos = np.random.random(len(lista_acoes))
            pesos = pesos/np.sum(pesos) # normalizing
            tabela_pesos[sample_wallet, :] = pesos

            tabela_ret_esp[sample_wallet] = np.sum(media_retornos * pesos * 252) # anualize by capital market year (cause returns are log)
            tabela_vols_esp[sample_wallet] = np.sqrt(np.dot(pesos.T, np.dot(matriz_cov*252, pesos))) #dot é produto de matrizes
            # produto duplo, calculo de volatilidade anualizada ponderada pelos pesos dos ativos, raíz disso é std

            tabela_sharpe[sample_wallet] = tabela_ret_esp[sample_wallet]/tabela_vols_esp[sample_wallet]


        sharpe_max = tabela_sharpe.argmax()

        tabela_pesos[sharpe_max]


        tabela_ret_esp_arit = np.exp(tabela_ret_esp) - 1

        tabela_vols_esp[sharpe_max]