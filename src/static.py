# -*- coding: UTF-8 -*- 
"""Import modules"""

from os import path
from dataclasses import dataclass, field


@dataclass
class StaticVariables:
    """Static variables
    dataclass"""

    data_dir = path.join(
        path.dirname(path.dirname(__file__)), "data"
        )
    
    data_results_dir = path.join(
        path.dirname(path.dirname(__file__)), "data_results"
        )

    data_dy_mean: str = path.join(data_dir, "dy_mean.xlsx"
    )

    data_dy_5years: str = path.join(data_dir, "dy_5years.xlsx")

    data_dy_mad: str = path.join(data_dir, "dy_mad.xlsx")

    data_price_mad: str = path.join(data_dir, "price_mad.xlsx")

    b3_url: str = "https://www.b3.com.br/pt_br/noticias/b3-lanca-primeiro-indice-derivado-do-ibovespa-b3-para-acompanhar-empresas-que-mais-pagam-dividendos.htm"

    model_solver: str = "glpk"

    financials: list = field(default_factory=list)

    electricals: list = field(default_factory=list)

    others: list = field(default_factory=list)

    def __post_init__(self):
        """Initialize sectors
        lists"""

        self.financials = ["BBSE3", "SANB11", "ITSA4", "BBAS3", "BRAP4", "CIEL3"]

        self.electricals = ["TAEE11", "EGIE3", "CMIG4", "CPLE6", "CPFE3"]

        self.others = ["VIVT3", "CSNA3", "VALE3", "GGBR4", "VBBR3", "CYRE3", "GOAU4", "PETR4", "MRFG3"]