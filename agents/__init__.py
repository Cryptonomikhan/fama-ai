"""
Agents module for Fama AI.

This module provides specialized AI agents for financial modeling
and analysis of yield-generating investment vehicles.
"""
from agents.research import ResearchAgent
from agents.modeling import ModelingAgent
from agents.scenario_planner import ScenarioPlannerAgent
from agents.assumption_generator import AssumptionGeneratorAgent
from agents.validator import ValidatorAgent
from agents.agent_coordinator import AgentCoordinator
from agents.dashboard_builder import DashboardBuilderAgent

__all__ = [
    'ResearchAgent',
    'ModelingAgent',
    'ScenarioPlannerAgent',
    'AssumptionGeneratorAgent',
    'ValidatorAgent',
    'AgentCoordinator',
    'DashboardBuilderAgent'
] 