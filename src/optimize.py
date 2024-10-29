# -*- coding: UTF-8 -*-
"""Import modules"""
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from requests import get
from io import StringIO
import pyomo.environ as pyo
from os import path


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

        self.__transform_data()
        self._get_results()

    def __transform_data(self) -> None:
        """ Process excel files
        return None """

        for filepath in [self.static.data_dy_mean,
                         self.static.data_dy_mad,
                         self.static.data_price_mad]:
            try:
                data = (
                    pd.read_excel(filepath)
                    .rename(columns={"Unnamed: 0": "ticker"})
                )

                data.to_excel(filepath, index=False)

            except Exception as error:
                raise OSError(error) from error

        return "Transform data"
       

    def __get_weighs(self) -> list:
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

        returns_dict = {ticker:dy for ticker, dy in zip(dy_data["ticker"], dy_data["dy_medio"])}
        dy_mad_dict = {ticker:dy for ticker, dy in zip(dy_mad_data["ticker"], dy_mad_data["dy_mad"])}
        pr_mad_dict = {ticker:dy for ticker, dy in zip(price_mad_data["ticker"], price_mad_data["pr_mad"])}

        # building model
        model = pyo.ConcreteModel()

        model.weight = pyo.Var(all_assets, domain=pyo.NonNegativeReals)

        model.returns = pyo.Objective(expr=sum([model.weight[asset] * returns_dict[asset] 
                                                for asset in all_assets]),
                                    sense=pyo.maximize)

        # setting constraints
        model.cons = pyo.ConstraintList()

        model.cons.add(expr=sum([model.weight[weight] for weight in model.weight]) == 1)

        for weight in model.weight:
            model.cons.add(expr= model.weight[weight] <= 0.20)

        model.cons.add(sum([model.weight[asset] 
                            for asset in model.weight if asset in financials]) <= 0.50)
        
        model.cons.add(sum([model.weight[asset] 
                            for asset in model.weight if asset in electricals]) <= 0.50)
        
        model.cons.add(sum([model.weight[asset] 
                            for asset in model.weight if asset in others]) <= 0.50)

        model.cons.add(expr=sum([model.weight[asset] * dy_mad_dict[asset] 
                                 for asset in all_assets]) <= dy_mad_indice)
        
        model.cons.add(expr=sum([model.weight[asset] * pr_mad_dict[asset] 
                                 for asset in all_assets]) <= pr_mad_indice)

        return model
    

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
            sharpe_ratio = [sharpe_ratio],
        )

        dataframe.to_excel(path.join(self.static.data_dir, "resultados_otimizacao.xlsx"), float_format="%.8f")

        return "Results spreadsheet done"
