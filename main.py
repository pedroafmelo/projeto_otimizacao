# -*- coding: UTF-8 -*-
"""Import local modules"""
from src.markowitz import Mark
from src.optimize import OptimizeDY
from src.monte_carlom import MonteCarlo

if __name__ == "__main__":
    pyo_optimizer = OptimizeDY()
    mark_optimizer = Mark()
    simulator = MonteCarlo()

    pyo_optimizer()
    mark_optimizer()
    simulator()