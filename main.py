# -*- coding: UTF-8 -*-
"""Import local modules"""
from src.markowitz import Mark
from src.optimize import OptimizeDY


if __name__ == "__main__":
    pyo_optimizer = OptimizeDY()
    mark_optimizer = Mark()

    pyo_optimizer()
    mark_optimizer()