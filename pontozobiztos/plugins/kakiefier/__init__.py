# from .kakiefierapp import on_message, on_reaction_added, on_reaction_removed
from . import kakiefierapp

ENABLED = False

on_message = kakiefierapp.prediction_test_mode


