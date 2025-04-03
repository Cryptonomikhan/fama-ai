"""
Models module for Fama AI.

This module provides models for the Fama AI application, including Formation model integration.
"""
from models.formation import Formation
from models.model_factory import create_model

__all__ = ['Formation', 'create_model'] 