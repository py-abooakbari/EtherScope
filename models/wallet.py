"""Pydantic models for wallets."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, validator

from .token import TokenSummary
from .transaction import TransactionSummary


class ActivityLevel(str, Enum):
    """Wallet activity levels."""

    DORMANT = "dormant"
    LOW = "low"
    MODERATE = "moderate"
    ACTIVE = "active"
    HIGHLY_ACTIVE = "highly_active"


class WalletBehavior(BaseModel):
    """Behavioral analysis of wallet."""

    activity_level: ActivityLevel = Field(..., description="Overall activity level")
    defi_user: bool = Field(..., description="Whether wallet interacts with DeFi protocols")
    nft_trader: bool = Field(..., description="Whether wallet trades NFTs")
    contract_deployer: bool = Field(..., description="Whether wallet deployed contracts")
    wallet_score: int = Field(..., ge=0, le=100, description="Overall wallet score (0-100)")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "activity_level": "active",
                "defi_user": True,
                "nft_trader": False,
                "contract_deployer": False,
                "wallet_score": 75,
            }
        }


class WalletAnalysis(BaseModel):
    """Complete wallet analysis."""

    wallet_address: str = Field(..., description="Ethereum wallet address")
    eth_balance: str = Field(..., description="ETH balance in Wei")
    eth_balance_display: str = Field(..., description="ETH balance in ETH")
    usd_value: Optional[float] = Field(None, description="Total wallet USD value")
    token_summary: TokenSummary = Field(..., description="Token holdings summary")
    transaction_summary: TransactionSummary = Field(..., description="Transaction summary")
    behavior: WalletBehavior = Field(..., description="Behavioral analysis")
    analyzed_at: datetime = Field(default_factory=datetime.utcnow, description="Analysis timestamp")
    first_transaction_date: Optional[datetime] = Field(
        None, description="Date of first transaction"
    )
    days_active: Optional[int] = Field(None, description="Number of days account has been active")

    @validator("wallet_address")
    def validate_address(cls, v: str) -> str:
        """Validate Ethereum address format."""
        if not v.startswith("0x") or len(v) != 42:
            raise ValueError("Invalid Ethereum address format")
        try:
            int(v, 16)
        except ValueError:
            raise ValueError("Invalid Ethereum address format")
        return v.lower()

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "wallet_address": "0x1234567890123456789012345678901234567890",
                "eth_balance": "1000000000000000000",
                "eth_balance_display": "1.0",
                "usd_value": 1500.0,
                "token_summary": {
                    "top_tokens": [],
                    "total_tokens_held": 5,
                    "total_usd_value": 50000.0,
                },
                "transaction_summary": {
                    "total_transactions": 150,
                    "last_transactions": [],
                    "unique_interacted_addresses": 45,
                    "contract_interactions": 30,
                    "failed_transactions": 2,
                },
                "behavior": {
                    "activity_level": "active",
                    "defi_user": True,
                    "nft_trader": False,
                    "contract_deployer": False,
                    "wallet_score": 75,
                },
                "analyzed_at": "2024-01-01T00:00:00",
                "first_transaction_date": "2022-01-01T00:00:00",
                "days_active": 730,
            }
        }
