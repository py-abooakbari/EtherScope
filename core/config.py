"""Configuration management for EtherScope."""

import os
from typing import Optional

from dotenv import load_dotenv

from .exceptions import ConfigurationError

load_dotenv()


class Config:
    """Application configuration."""

    # Telegram
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_MAX_MESSAGE_LENGTH: int = 4096

    # Blockchain API
    BLOCKCHAIN_API_PROVIDER: str = os.getenv("BLOCKCHAIN_API_PROVIDER", "etherscan")
    # Etherscan
    ETHERSCAN_API_KEY: str = os.getenv("ETHERSCAN_API_KEY", "")
    ETHERSCAN_BASE_URL: str = "https://api.etherscan.io/api"
    # Alchemy
    ALCHEMY_API_KEY: Optional[str] = os.getenv("ALCHEMY_API_KEY")
    ALCHEMY_BASE_URL: str = "https://eth-mainnet.g.alchemy.com/v2"

    # API Settings
    API_TIMEOUT: int = 30
    API_MAX_RETRIES: int = 3
    API_RETRY_DELAY: float = 1.0
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60

    # Cache
    CACHE_ENABLED: bool = os.getenv("CACHE_ENABLED", "true").lower() == "true"
    CACHE_TTL_SECONDS: int = 300  # 5 minutes
    CACHE_MAX_SIZE: int = 1000

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT: str = "structured"

    # Analysis
    MIN_TRANSACTIONS_THRESHOLD: int = 10
    DEFI_CONTRACT_THRESHOLD: int = 5
    WALLET_SCORE_MAX: int = 100

    # Environment
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "production")

    @classmethod
    def validate(cls) -> None:
        """Validate required configuration values."""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ConfigurationError("TELEGRAM_BOT_TOKEN environment variable is required")

        if cls.BLOCKCHAIN_API_PROVIDER == "etherscan" and not cls.ETHERSCAN_API_KEY:
            raise ConfigurationError("ETHERSCAN_API_KEY environment variable is required for Etherscan provider")

        if cls.BLOCKCHAIN_API_PROVIDER == "alchemy" and not cls.ALCHEMY_API_KEY:
            raise ConfigurationError("ALCHEMY_API_KEY environment variable is required for Alchemy provider")

    @classmethod
    def get_blockchain_api_key(cls) -> str:
        """Get the appropriate blockchain API key based on provider."""
        if cls.BLOCKCHAIN_API_PROVIDER == "alchemy":
            if not cls.ALCHEMY_API_KEY:
                raise ConfigurationError("ALCHEMY_API_KEY not configured")
            return cls.ALCHEMY_API_KEY
        return cls.ETHERSCAN_API_KEY
