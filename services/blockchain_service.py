"""Blockchain API service for EtherScope."""

import asyncio
import re
from datetime import datetime
from typing import Optional

import httpx

from core.config import Config
from core.exceptions import (
    BlockchainAPIError,
    InvalidWalletAddressError,
    RateLimitError,
)
from core.logger import get_logger
from models.token import Token, TokenSummary
from models.transaction import Transaction, TransactionSummary, TransactionType

logger = get_logger(__name__)


class BlockchainService:
    """Service for interacting with blockchain APIs."""

    def __init__(self, api_provider: Optional[str] = None, timeout: int = 30):
        """Initialize blockchain service.

        Args:
            api_provider: Blockchain API provider ('etherscan' or 'alchemy')
            timeout: HTTP request timeout in seconds

        """
        self.provider = api_provider or Config.BLOCKCHAIN_API_PROVIDER
        self.timeout = timeout
        self.api_key = Config.get_blockchain_api_key()
        self._rate_limit_remaining = Config.RATE_LIMIT_REQUESTS_PER_MINUTE
        self._last_request_time = 0.0

    @staticmethod
    def validate_address(address: str) -> str:
        """Validate and normalize Ethereum address.

        Args:
            address: Ethereum address to validate

        Returns:
            Normalized address (lowercase)

        Raises:
            InvalidWalletAddressError: If address is invalid

        """
        if not isinstance(address, str):
            raise InvalidWalletAddressError("Address must be a string")

        # Remove spaces and convert to lowercase
        address = address.strip().lower()

        # Check format
        if not re.match(r"^0x[0-9a-f]{40}$", address):
            raise InvalidWalletAddressError(
                f"Invalid wallet address format: {address}. "
                "Must be a valid 42-character Ethereum address (0x...)"
            )

        return address

    async def _make_request(
        self, url: str, params: dict, method: str = "GET"
    ) -> dict:
        """Make HTTP request with retry logic and rate limiting.

        Args:
            url: Request URL
            params: Query parameters
            method: HTTP method

        Returns:
            JSON response as dictionary

        Raises:
            BlockchainAPIError: If API request fails
            RateLimitError: If rate limit is exceeded

        """
        # Rate limiting
        await self._apply_rate_limit()

        retries = Config.API_MAX_RETRIES
        last_error = None

        for attempt in range(retries):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.request(method, url, params=params)
                    response.raise_for_status()

                    logger.info(
                        f"API request successful: {url}",
                        extra={"attempt": attempt + 1},
                    )

                    return response.json()

            except httpx.HTTPStatusError as e:
                last_error = e
                if e.response.status_code == 429:
                    logger.warning("Rate limit exceeded, applying backoff")
                    raise RateLimitError("API rate limit exceeded")

                if attempt < retries - 1:
                    wait_time = Config.API_RETRY_DELAY * (2 ** attempt)
                    logger.warning(
                        f"Request failed with status {e.response.status_code}, "
                        f"retrying in {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                    continue

            except httpx.RequestError as e:
                last_error = e
                if attempt < retries - 1:
                    wait_time = Config.API_RETRY_DELAY * (2 ** attempt)
                    logger.warning(f"Request error, retrying in {wait_time}s: {str(e)}")
                    await asyncio.sleep(wait_time)
                    continue

        logger.error(f"API request failed after {retries} attempts: {str(last_error)}")
        raise BlockchainAPIError(
            f"Failed to fetch blockchain data after {retries} attempts"
        )

    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting to API requests."""
        import time

        current_time = time.time()
        time_since_last = current_time - self._last_request_time

        # Reset counter every minute
        if time_since_last > 60:
            self._rate_limit_remaining = Config.RATE_LIMIT_REQUESTS_PER_MINUTE
            self._last_request_time = current_time

        if self._rate_limit_remaining <= 0:
            wait_time = 60 - time_since_last
            logger.warning(f"Rate limit reached, waiting {wait_time:.2f}s")
            await asyncio.sleep(max(wait_time, 0))
            self._rate_limit_remaining = Config.RATE_LIMIT_REQUESTS_PER_MINUTE
            self._last_request_time = time.time()

        self._rate_limit_remaining -= 1

    async def get_eth_balance(self, address: str) -> str:
        """Fetch ETH balance for wallet.

        Args:
            address: Wallet address

        Returns:
            Balance in Wei

        Raises:
            InvalidWalletAddressError: If address is invalid
            BlockchainAPIError: If API call fails

        """
        address = self.validate_address(address)
        logger.info(f"Fetching ETH balance for {address}")

        if self.provider == "alchemy":
            return await self._get_balance_alchemy(address)
        else:
            return await self._get_balance_etherscan(address)

    async def _get_balance_etherscan(self, address: str) -> str:
        """Fetch balance from Etherscan."""
        url = Config.ETHERSCAN_BASE_URL
        params = {
            "module": "account",
            "action": "balance",
            "address": address,
            "apikey": self.api_key,
        }

        data = await self._make_request(url, params)

        if data.get("status") != "1":
            raise BlockchainAPIError(f"Etherscan error: {data.get('message', 'Unknown error')}")

        return data.get("result", "0")

    async def _get_balance_alchemy(self, address: str) -> str:
        """Fetch balance from Alchemy."""
        url = f"{Config.ALCHEMY_BASE_URL}/{self.api_key}"
        headers = {"accept": "application/json", "content-type": "application/json"}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                url,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "eth_getBalance",
                    "params": [address, "latest"],
                },
                headers=headers,
            )
            response.raise_for_status()
            data = response.json()

        if "error" in data:
            raise BlockchainAPIError(f"Alchemy error: {data['error']['message']}")

        # Alchemy returns hex value, convert to decimal
        return str(int(data.get("result", "0x0"), 16))

    async def get_erc20_tokens(self, address: str) -> TokenSummary:
        """Fetch ERC20 token holdings for wallet.

        Args:
            address: Wallet address

        Returns:
            TokenSummary with token holdings

        Raises:
            InvalidWalletAddressError: If address is invalid
            BlockchainAPIError: If API call fails

        """
        address = self.validate_address(address)
        logger.info(f"Fetching ERC20 tokens for {address}")

        if self.provider == "alchemy":
            return await self._get_tokens_alchemy(address)
        else:
            return await self._get_tokens_etherscan(address)

    async def _get_tokens_etherscan(self, address: str) -> TokenSummary:
        """Fetch tokens from Etherscan."""
        url = Config.ETHERSCAN_BASE_URL
        params = {
            "module": "account",
            "action": "tokentx",
            "address": address,
            "page": 1,
            "offset": 10000,
            "sort": "desc",
            "apikey": self.api_key,
        }

        data = await self._make_request(url, params)

        if data.get("status") != "1" or not data.get("result"):
            return TokenSummary(top_tokens=[], total_tokens_held=0, total_usd_value=None)

        # Parse tokens - simplified implementation
        tokens_dict = {}
        for tx in data.get("result", []):
            contract = tx.get("contractAddress", "").lower()
            if contract and contract not in tokens_dict:
                tokens_dict[contract] = Token(
                    contract_address=contract,
                    name=tx.get("tokenName", "Unknown"),
                    symbol=tx.get("tokenSymbol", "???"),
                    decimals=int(tx.get("tokenDecimal", 18)),
                    balance=tx.get("value", "0"),
                    balance_display=self._format_token_balance(
                        tx.get("value", "0"), int(tx.get("tokenDecimal", 18))
                    ),
                    usd_value=None,
                )

        top_tokens = sorted(
            tokens_dict.values(),
            key=lambda t: int(t.balance) if t.balance.isdigit() else 0,
            reverse=True,
        )[:10]

        return TokenSummary(
            top_tokens=top_tokens,
            total_tokens_held=len(tokens_dict),
            total_usd_value=None,
        )

    async def _get_tokens_alchemy(self, address: str) -> TokenSummary:
        """Fetch tokens from Alchemy."""
        # This is a simplified implementation
        # Real implementation would use Alchemy's token API
        logger.info("Alchemy token fetching not yet implemented, returning empty summary")
        return TokenSummary(top_tokens=[], total_tokens_held=0, total_usd_value=None)

    async def get_transactions(self, address: str, limit: int = 10) -> TransactionSummary:
        """Fetch recent transactions for wallet.

        Args:
            address: Wallet address
            limit: Number of transactions to fetch

        Returns:
            TransactionSummary with transaction details

        Raises:
            InvalidWalletAddressError: If address is invalid
            BlockchainAPIError: If API call fails

        """
        address = self.validate_address(address)
        logger.info(f"Fetching transactions for {address}, limit={limit}")

        if self.provider == "alchemy":
            return await self._get_transactions_alchemy(address, limit)
        else:
            return await self._get_transactions_etherscan(address, limit)

    async def _get_transactions_etherscan(self, address: str, limit: int) -> TransactionSummary:
        """Fetch transactions from Etherscan."""
        url = Config.ETHERSCAN_BASE_URL
        params = {
            "module": "account",
            "action": "txlist",
            "address": address,
            "page": 1,
            "offset": limit,
            "sort": "desc",
            "apikey": self.api_key,
        }

        data = await self._make_request(url, params)

        if data.get("status") != "1" or not data.get("result"):
            return TransactionSummary(
                total_transactions=0,
                last_transactions=[],
                unique_interacted_addresses=0,
                contract_interactions=0,
                failed_transactions=0,
            )

        transactions = []
        unique_addresses = set()
        contract_interactions = 0
        failed_transactions = 0
        total_transactions = len(data.get("result", []))

        for tx in data.get("result", [])[:limit]:
            to_addr = tx.get("to", "")
            from_addr = tx.get("from", "").lower()

            if to_addr:
                unique_addresses.add(to_addr.lower())
            if from_addr:
                unique_addresses.add(from_addr)

            if tx.get("input", "0x") != "0x":
                contract_interactions += 1

            if tx.get("isError", "0") == "1":
                failed_transactions += 1

            # Determine transaction type
            tx_type = TransactionType.CONTRACT_INTERACTION
            if to_addr.lower() == address:
                tx_type = TransactionType.RECEIVE
            elif tx.get("input", "0x") == "0x":
                tx_type = TransactionType.SEND

            transaction = Transaction(
                hash=tx.get("hash", ""),
                from_address=from_addr,
                to_address=to_addr.lower() if to_addr else None,
                value=tx.get("value", "0"),
                value_display=self._format_ether(tx.get("value", "0")),
                gas_price=tx.get("gasPrice", "0"),
                gas_used=tx.get("gas", "0"),
                timestamp=datetime.fromtimestamp(int(tx.get("timeStamp", 0))),
                block_number=int(tx.get("blockNumber", 0)),
                is_error=tx.get("isError", "0") == "1",
                type=tx_type,
                method_id=tx.get("input", "0x")[:10] if tx.get("input", "0x") != "0x" else None,
            )
            transactions.append(transaction)

        # Remove the address itself from unique addresses
        unique_addresses.discard(address)

        return TransactionSummary(
            total_transactions=total_transactions,
            last_transactions=transactions,
            unique_interacted_addresses=len(unique_addresses),
            contract_interactions=contract_interactions,
            failed_transactions=failed_transactions,
        )

    async def _get_transactions_alchemy(self, address: str, limit: int) -> TransactionSummary:
        """Fetch transactions from Alchemy."""
        logger.info("Alchemy transaction fetching not yet implemented, returning empty summary")
        return TransactionSummary(
            total_transactions=0,
            last_transactions=[],
            unique_interacted_addresses=0,
            contract_interactions=0,
            failed_transactions=0,
        )

    @staticmethod
    def _format_ether(wei: str) -> str:
        """Convert Wei to Ether string representation.

        Args:
            wei: Value in Wei

        Returns:
            Formatted ETH value

        """
        try:
            wei_int = int(wei)
            eth = wei_int / 1e18
            return f"{eth:.6f}".rstrip("0").rstrip(".")
        except (ValueError, TypeError):
            return "0"

    @staticmethod
    def _format_token_balance(balance: str, decimals: int) -> str:
        """Convert token balance with decimals.

        Args:
            balance: Balance in base units
            decimals: Token decimals

        Returns:
            Formatted balance

        """
        try:
            balance_int = int(balance)
            divisor = 10 ** decimals
            formatted = balance_int / divisor
            return f"{formatted:.6f}".rstrip("0").rstrip(".")
        except (ValueError, TypeError):
            return "0"
