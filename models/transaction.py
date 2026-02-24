"""Pydantic models for transactions."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    """Transaction types."""

    SEND = "send"
    RECEIVE = "receive"
    CONTRACT_INTERACTION = "contract_interaction"
    TOKEN_TRANSFER = "token_transfer"
    NFT_TRANSFER = "nft_transfer"


class Transaction(BaseModel):
    """Blockchain transaction model."""

    hash: str = Field(..., description="Transaction hash")
    from_address: str = Field(..., description="From address")
    to_address: Optional[str] = Field(None, description="To address")
    value: str = Field(..., description="Transaction value in Wei")
    value_display: str = Field(..., description="Transaction value in ETH")
    gas_price: str = Field(..., description="Gas price in Wei")
    gas_used: Optional[str] = Field(None, description="Gas used in Wei")
    timestamp: datetime = Field(..., description="Transaction timestamp")
    block_number: int = Field(..., description="Block number")
    is_error: bool = Field(default=False, description="Whether transaction failed")
    type: TransactionType = Field(..., description="Transaction type")
    method_id: Optional[str] = Field(None, description="Function method ID for contract calls")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "hash": "0x1234567890abcdef",
                "from_address": "0xfrom",
                "to_address": "0xto",
                "value": "1000000000000000000",
                "value_display": "1.0",
                "gas_price": "20000000000",
                "gas_used": "21000",
                "timestamp": "2024-01-01T00:00:00",
                "block_number": 1000000,
                "is_error": False,
                "type": "send",
                "method_id": "0xa9059cbb",
            }
        }


class TransactionSummary(BaseModel):
    """Summary of transaction activity."""

    total_transactions: int = Field(..., description="Total number of transactions")
    last_transactions: list[Transaction] = Field(
        ..., description="Last N transactions (default 10)"
    )
    unique_interacted_addresses: int = Field(
        ..., description="Number of unique addresses interacted with"
    )
    contract_interactions: int = Field(..., description="Number of contract interactions")
    failed_transactions: int = Field(..., description="Number of failed transactions")

    class Config:
        """Pydantic config."""

        json_schema_extra = {
            "example": {
                "total_transactions": 150,
                "last_transactions": [],
                "unique_interacted_addresses": 45,
                "contract_interactions": 30,
                "failed_transactions": 2,
            }
        }
