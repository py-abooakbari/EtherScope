"""Pydantic models for tokens."""

from typing import Optional

from pydantic import BaseModel, Field


class Token(BaseModel):
    """ERC20 token model."""

    contract_address: str = Field(..., description="Token contract address")
    name: str = Field(..., description="Token name")
    symbol: str = Field(..., description="Token symbol")
    decimals: int = Field(..., description="Token decimals")
    balance: str = Field(..., description="Token balance in base units")
    balance_display: str = Field(..., description="Token balance in human-readable format")
    usd_value: Optional[float] = Field(None, description="USD value of token holdings")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "contract_address": "0xdac17f958d2ee523a2206206994597c13d831ec7",
                "name": "Tether USD",
                "symbol": "USDT",
                "decimals": 6,
                "balance": "1000000000",
                "balance_display": "1000.0",
                "usd_value": 1000.0,
            }
        }


class TokenSummary(BaseModel):
    """Summary of token holdings."""

    top_tokens: list[Token] = Field(..., description="Top tokens by balance")
    total_tokens_held: int = Field(..., description="Total number of unique tokens held")
    total_usd_value: Optional[float] = Field(None, description="Total USD value of all tokens")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "top_tokens": [],
                "total_tokens_held": 5,
                "total_usd_value": 50000.0,
            }
        }
