# -*- coding: UTF-8 -*-
"""Import modules"""
from io import StringIO
from os import path

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

        self._transform_data()
        self._get_results()

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


    def __pyo_optimize(self) -> pyo.ConcreteModel:
        """optimize dys
        return model's results"""

        # important initial configurations

        data_index = self._transform_data()

        weight_vector = self._get_weighs()

        try:
            dy_mad_vector = np.array(data_index["dy_mad"])
            price_mad_vector = np.array(data_index["pr_mad"])
            
            dy_mad_indice = float(sum(weight_vector * dy_mad_vector))
            pr_mad_indice = float(sum(weight_vector * price_mad_vector))

            financials = self.static.financials
            electricals = self.static.electricals
            others = self.static.others

            all_assets = financials + electricals + others

            returns_dict = {ticker:dy for ticker, dy in zip(data_index["ticker"], data_index["dy_medio"])}
            dy_mad_dict = {ticker:dy for ticker, dy in zip(data_index["ticker"], data_index["dy_mad"])}
            pr_mad_dict = {ticker:dy for ticker, dy in zip(data_index["ticker"], data_index["pr_mad"])}
        
        except Exception as error:
            raise OSError(error) from error
        
        # building model
        model = pyo.ConcreteModel()

        try:
            model.weight = pyo.Var(all_assets, domain=pyo.NonNegativeReals)

            model.returns = pyo.Objective(expr=sum([model.weight[asset] * returns_dict[asset] 
                                                    for asset in all_assets]),
                                        sense=pyo.maximize)

            # setting constraints
            model.cons = pyo.ConstraintList()

            model.cons.add(expr=sum([model.weight[weight] for weight in model.weight]) == 1)

            for weight in model.weight:
                model.cons.add(expr= model.weight[weight] <= 0.20)

            model.cons.add(sum([model.weight[asset] for asset in financials]) <= 0.50)
            
            model.cons.add(sum([model.weight[asset] for asset in electricals]) <= 0.50)
            
            model.cons.add(sum([model.weight[asset] for asset in others]) <= 0.50)

            model.cons.add(expr=sum([model.weight[asset] * dy_mad_dict[asset] 
                                    for asset in all_assets]) <= dy_mad_indice)
            
            model.cons.add(expr=sum([model.weight[asset] * pr_mad_dict[asset] 
                                    for asset in all_assets]) <= pr_mad_indice)

            return model
        
        except Exception as error:
            raise OSError(error) from error

    def _get_results(self) -> None:
        """Generate results
        spreadsheet
        return None"""


        rfr = 0.06 # risk-free rate

        model = self.__pyo_optimize()

        solver = pyo.SolverFactory("glpk")
        solver.solve(model)

        sharpe_ratio = (model.returns() - rfr) / model.cons[25]()

        dataframe = pd.DataFrame()
        dataframe = dataframe.assign(
            retorno_carteira = [model.returns()],
            mad_dy_carteira = [model.cons[25]()],
            mad_preco_carteira = [model.cons[26]()],
            mad_total_carteira = lambda x: x["mad_dy_carteira"] + x["mad_preco_carteira"],
            sharpe_ratio = [sharpe_ratio]
        )

        dataframe.to_excel(path.join(self.static.data_dir, "resultados_otimizacao.xlsx"), float_format="%.8f")

        print("Results spreadsheet done")
