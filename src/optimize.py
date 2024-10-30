# -*- coding: UTF-8 -*-
"""Import modules"""
from io import StringIO
from os import path
import time

import numpy as np
import pandas as pd
import pyomo.environ as pyo
from bs4 import BeautifulSoup
from requests import get


class OptimizeDY:
    """Dividend Yield
    Optimizer Model"""

    def __init__(self):
        """Initialize instance"""

        # import local modules

        from src.static import StaticVariables

        self.static = StaticVariables()


    def __repr__(self):
        """ Class representation """

        return """ Dividend Yield Optimizer """

    def __str__(self): 
        """ String representation """

        return """Dividend Yield Optimizer"""
    
    def __call__(self):
        """execute class
        routine"""

        data_index = self._transform_data()
        self._get_results(data_index, "resultados_otimizacao_pyomo", 0.2, 0.5)

        data_index_optimistic = self._transform_data()
        data_index_optimistic = data_index_optimistic.assign(
                dy_medio = lambda x: x["dy_medio"] * 1.10,
                dy_mad = lambda x: x["dy_mad"] * 0.9,
                pr_mad = lambda x: x["pr_mad"] * 0.8
        )
        self._get_results(data_index_optimistic, "resultados_otimista_pyomo", 0.25, 0.5)

        data_index_pessimistic = self._transform_data()
        data_index_pessimistic = data_index_pessimistic.assign(
                dy_medio = lambda x: x["dy_medio"] * 0.9,
                dy_mad = lambda x: x["dy_mad"] * 1.10,
                pr_mad = lambda x: x["pr_mad"] * 1.20
        )
        self._get_results(data_index_pessimistic, "resultados_pessimista_pyomo", 0.15, 0.4)


    def _transform_data(self) -> pd.DataFrame:
        """ Process excel files
        return DataFrame """
        
        df_list = []

        for filepath in [self.static.data_dy_mean,
                         self.static.data_dy_mad,
                         self.static.data_price_mad]:
            try:
                data = (
                    pd.read_excel(filepath)
                    .rename(columns={"Unnamed: 0": "ticker"})
                )

                df_list.append(data)

            except Exception as error:
                raise OSError(error) from error
            
        df_final = (
            df_list[0]
            .merge(df_list[1], on="ticker", how="inner")
            .merge(df_list[2], on="ticker", how="inner")
        )

        return df_final
       

    def _get_weighs(self) -> list:
        """ Scrap b3 page
        return weight vector """

        try:

            response = get(self.static.b3_url)
            if not response.ok:
                response.raise_for_status()
            
            soup = BeautifulSoup(response.content, "html.parser")

            table_content = soup.find_all("table")[0]

            index_assets = pd.read_html(StringIO(str(table_content)))[0]
            index_assets.columns = ["ticker", "empresa", "posicao"]

            index_assets = index_assets.assign(
                    posicao = lambda x: (x["posicao"].str.slice(0,3).astype(float))/ 100
                )

            index_assets = index_assets.drop(19)

            weight_vector = index_assets["posicao"].to_numpy()

            return weight_vector

        except Exception as error:
            raise OSError(error) from error


    def _pyo_optimize(self, weight_vector: np.array, 
                       returns_vector: np.array,
                       data_index: pd.DataFrame,
                       individua_max_concentration: float,
                       sector_max_concentration: float) -> pyo.ConcreteModel:
        """optimize dys
        return model's results"""

        # important initial configurations

        try:
            dy_mad_vector = np.array(data_index["dy_mad"])
            price_mad_vector = np.array(data_index["pr_mad"])
            
            dy_mad_indice = float(sum(weight_vector * dy_mad_vector))
            pr_mad_indice = float(sum(weight_vector * price_mad_vector))

            financials = self.static.financials
            electricals = self.static.electricals
            others = self.static.others

            all_assets = financials + electricals + others

            returns_dict = {ticker:dy for ticker, dy in zip(data_index["ticker"], returns_vector)}
            dy_mad_dict = {ticker:mad for ticker, mad in zip(data_index["ticker"], data_index["dy_mad"])}
            pr_mad_dict = {ticker:mad for ticker, mad in zip(data_index["ticker"], data_index["pr_mad"])}
        
        except Exception as error:
            raise OSError(error) from error
        
        # building model
        model = pyo.ConcreteModel()
        model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)

        try:
            model.weight = pyo.Var(all_assets, domain=pyo.NonNegativeReals)

            model.returns = pyo.Objective(expr=sum([model.weight[asset] * returns_dict[asset] 
                                                    for asset in all_assets]),
                                        sense=pyo.maximize)

            # setting constraints
            model.cons = pyo.ConstraintList()

            model.cons.add(expr=sum([model.weight[weight] for weight in model.weight]) == 1)

            for weight in model.weight:
                model.cons.add(expr= model.weight[weight] <= individua_max_concentration)

            model.cons.add(sum([model.weight[asset] for asset in financials]) <= sector_max_concentration)
            
            model.cons.add(sum([model.weight[asset] for asset in electricals]) <= sector_max_concentration)
            
            model.cons.add(sum([model.weight[asset] for asset in others]) <= sector_max_concentration)

            model.cons.add(expr=sum([model.weight[asset] * dy_mad_dict[asset] 
                                    for asset in all_assets]) <= dy_mad_indice)
            
            model.cons.add(expr=sum([model.weight[asset] * pr_mad_dict[asset] 
                                    for asset in all_assets]) <= pr_mad_indice)

            return model
        
        except Exception as error:
            raise OSError(error) from error


    def _get_results(self, data_index: pd.DataFrame, filename: str, 
                     individua_max_concentration: float,
                     sector_max_concentration: float) -> None:
        """Generate results
        spreadsheet
        return None"""

        weight_vector = self._get_weighs()
        returns_vector = data_index["dy_medio"]

        rfr = 0.06 # risk-free rate
        
        begin_time = time.time()
        model = self._pyo_optimize(weight_vector, returns_vector, data_index, 
                                   individua_max_concentration,
                                   sector_max_concentration)
        elapsed_time = time.time() - begin_time

        solver = pyo.SolverFactory("glpk")
        solver.solve(model)

        optm_wallet = {str(key):model.weight[key]() 
                         for key in model.weight.keys() if model.weight[key]() > 0}
        
        print(optm_wallet)

        shadow_prices = {str(key):model.dual[key] 
                         for key in model.dual.keys() if model.dual[key] > 0}

        sharpe_ratio = (model.returns() - rfr) / model.cons[25]()

        df_results = pd.DataFrame(data=shadow_prices, index = [0])
        df_results = df_results.assign(
            retorno_carteira = [model.returns()],
            mad_dy_carteira = [model.cons[25]()],
            mad_preco_carteira = [model.cons[26]()],
            mad_total_carteira = lambda x: x["mad_dy_carteira"] + x["mad_preco_carteira"],
            sharpe_ratio = [sharpe_ratio],
            tempo_execucao = [elapsed_time]
        )

        df_results.to_excel(path.join(self.static.data_results_dir, f"{filename}.xlsx"), float_format="%.8f")

        print("Results spreadsheet done")
