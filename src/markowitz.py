# -*- coding: UTF-8 -*-
"""Import modules"""
import datetime as dt
from os import path
import time

import numpy as np
import pandas as pd


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

        self.__optimize()
        self._get__results(self.__check_contraints())


    def __optimize(self) -> str:
        """Use grid search model
        optimize sharpe ratio"""

        # important initial configurations
        from src.optimize import OptimizeDY

        data_index = OptimizeDY()._transform_data()

        begin_time = time.time()

        weight_vector = OptimizeDY()._get_weighs()
        dy_return_verctor = np.array(data_index["dy_medio"])
        dy_mad_vector = np.array(data_index["dy_mad"])
        price_mad_vector = np.array(data_index["pr_mad"])

        # number of random weights combinations
        num_carteiras = 100_000

        # creating vectors
        exp_return_vector = np.zeros(num_carteiras)
        exp_dy_mad_vector = np.zeros(num_carteiras)
        exp_pr_mad_vector = np.zeros(num_carteiras)
        sharpe_vector = np.zeros(num_carteiras)
        weight_matrix = np.zeros((num_carteiras, len(weight_vector)))

        for k in range(num_carteiras):
            
            # kind of a grid search
            pesos = np.random.random(len(weight_vector)) 
            pesos = pesos/np.sum(pesos) # normalizing weights
            weight_matrix[k, :] = pesos

            exp_return_vector[k] = np.sum(dy_return_verctor * pesos) 
            exp_dy_mad_vector[k] = np.sum(dy_mad_vector * pesos)
            exp_pr_mad_vector[k] = np.sum(price_mad_vector * pesos)

            sharpe_vector[k] = (exp_return_vector[k] - 0.06)/(exp_dy_mad_vector[k])

        self.exp_return_vector = exp_return_vector
        self.exp_dy_mad_vector = exp_dy_mad_vector
        self.exp_pr_mad_vector = exp_pr_mad_vector
        self.sharpe_vector = sharpe_vector
        self.weight_matrix = weight_matrix

        self.elapsed_time = time.time() - begin_time

        return "Markowitz optimization done"


    def __check_contraints(self):
        """check constraints
        in vector's values"""

        # important initial configurations
        from src.optimize import OptimizeDY

        data_index = OptimizeDY()._transform_data()

        weight_vector = OptimizeDY()._get_weighs()
        dy_mad_vector = np.array(data_index["dy_mad"])
        price_mad_vector = np.array(data_index["pr_mad"])

        dy_mad_indice = float(sum(weight_vector * dy_mad_vector))
        pr_mad_indice = float(sum(weight_vector * price_mad_vector))

        financials = [2, 3, 5, 6, 7, 8]
        electricals = [0, 4, 8, 9, 10]
        others = [1, 11, 12, 13, 14, 15, 16, 18, 19]

        arrays = [
            "exp_return_vector",
            "exp_dy_mad_vector",
            "exp_pr_mad_vector",
            "sharpe_vector",
        ]

        setores = [financials, electricals, others]

        while True:
            best_sharpe = self.sharpe_vector.argmax()
            best_weight = self.weight_matrix[best_sharpe]

            if (
                any(x > 0.2 for x in best_weight)
                or np.sum(best_weight * dy_mad_vector) >= dy_mad_indice
                or np.sum(best_weight * price_mad_vector) >= pr_mad_indice
                ):
                for attr in arrays:
                    setattr(self, attr, np.delete(getattr(self, attr), best_sharpe))
                self.weight_matrix = np.delete(self.weight_matrix, best_sharpe, axis=0)
            

            elif any(any(best_weight[i] > 0.5 for i in setor) for setor in setores):
                for attr in arrays:
                    setattr(self, attr, np.delete(getattr(self, attr), best_sharpe))
                self.weight_matrix = np.delete(self.weight_matrix, best_sharpe, axis=0)
            
            else:
                print("Found a viable solution for the portfolio weights")
                print(best_weight)
                break

        return best_sharpe
    
    def _get__results(self, best_sharpe) -> str:
        
        results_df = pd.DataFrame()
        results_df = results_df.assign(
            retorno_carteira = [self.exp_return_vector[best_sharpe]],
            mad_dy_carteira = [self.exp_dy_mad_vector[best_sharpe]],
            mad_preco_carteira = [self.exp_pr_mad_vector[best_sharpe]],
            mad_total_carteira = [self.exp_dy_mad_vector[best_sharpe] + self.exp_pr_mad_vector[best_sharpe]],
            sharpe_ratio = [self.sharpe_vector[best_sharpe]],
            tempo_execucao = [self.elapsed_time]
        )
    
        results_df.to_excel(path.join(self.static.data_results_dir, "resultados_markowitz.xlsx"), float_format="%.8f")

        return "Results spreadsheet done"
