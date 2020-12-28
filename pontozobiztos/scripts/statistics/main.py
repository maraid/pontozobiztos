from pontozobiztos.scripts.statistics import queries
import importlib


for module in queries.__all__:
    imported_module = importlib.import_module('queries.' + module)
    imported_module.plot()