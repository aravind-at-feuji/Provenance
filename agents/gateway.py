"""
agents/gateway.py — Re-export of LLMGateway choke point.

Architecture reference: §C.5, §J.3, §Part V.
All AI agents route through LLMGateway.
"""

from app.modules.ai.gateway import BudgetExceededError, LLMGateway

__all__ = ["BudgetExceededError", "LLMGateway"]
