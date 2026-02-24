"""Custom exceptions for EtherScope."""


class EtherScopeException(Exception):
    """Base exception for EtherScope application."""

    pass


class InvalidWalletAddressError(EtherScopeException):
    """Raised when wallet address validation fails."""

    pass


class BlockchainServiceError(EtherScopeException):
    """Raised when blockchain service operations fail."""

    pass


class BlockchainAPIError(BlockchainServiceError):
    """Raised when external blockchain API call fails."""

    pass


class RateLimitError(BlockchainServiceError):
    """Raised when rate limit is exceeded."""

    pass


class CacheServiceError(EtherScopeException):
    """Raised when cache service operations fail."""

    pass


class AnalysisServiceError(EtherScopeException):
    """Raised when analysis service operations fail."""

    pass


class ConfigurationError(EtherScopeException):
    """Raised when configuration is invalid."""

    pass
