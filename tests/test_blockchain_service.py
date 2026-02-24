"""Unit tests for wallet address validation and blockchain service."""

import pytest

from core.exceptions import InvalidWalletAddressError
from services.blockchain_service import BlockchainService


class TestAddressValidation:
    """Tests for Ethereum address validation."""

    def test_valid_address_lowercase(self):
        """Test validation of valid lowercase address."""
        address = "0x1234567890123456789012345678901234567890"
        result = BlockchainService.validate_address(address)
        assert result == address.lower()

    def test_valid_address_uppercase(self):
        """Test validation of valid uppercase address."""
        address = "0x1234567890ABCDEF1234567890ABCDEF12345678"
        result = BlockchainService.validate_address(address)
        assert result == address.lower()

    def test_valid_address_mixed_case(self):
        """Test validation of mixed case address."""
        address = "0x1234567890AbCdEf1234567890AbCdEf12345678"
        result = BlockchainService.validate_address(address)
        assert result == address.lower()

    def test_valid_address_with_spaces(self):
        """Test validation of address with spaces is trimmed."""
        address = "  0x1234567890123456789012345678901234567890  "
        result = BlockchainService.validate_address(address)
        assert result == "0x1234567890123456789012345678901234567890"

    def test_invalid_address_no_prefix(self):
        """Test validation fails for address without 0x prefix."""
        address = "1234567890123456789012345678901234567890"
        with pytest.raises(InvalidWalletAddressError):
            BlockchainService.validate_address(address)

    def test_invalid_address_too_short(self):
        """Test validation fails for address too short."""
        address = "0x123456789012345678901234567890123456"
        with pytest.raises(InvalidWalletAddressError):
            BlockchainService.validate_address(address)

    def test_invalid_address_too_long(self):
        """Test validation fails for address too long."""
        address = "0x12345678901234567890123456789012345678901"
        with pytest.raises(InvalidWalletAddressError):
            BlockchainService.validate_address(address)

    def test_invalid_address_invalid_hex(self):
        """Test validation fails for non-hex characters."""
        address = "0xGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGGG"
        with pytest.raises(InvalidWalletAddressError):
            BlockchainService.validate_address(address)

    def test_invalid_address_not_string(self):
        """Test validation fails for non-string input."""
        address = 12345
        with pytest.raises(InvalidWalletAddressError):
            BlockchainService.validate_address(address)


class TestFormatting:
    """Tests for number formatting utilities."""

    def test_format_ether_full_eth(self):
        """Test formatting full ETH amounts."""
        wei = "1000000000000000000"  # 1 ETH
        result = BlockchainService._format_ether(wei)
        assert result == "1"

    def test_format_ether_wei(self):
        """Test formatting small amounts."""
        wei = "1000000000000000"  # 0.001 ETH
        result = BlockchainService._format_ether(wei)
        assert result == "0.001"

    def test_format_ether_zero(self):
        """Test formatting zero ETH."""
        wei = "0"
        result = BlockchainService._format_ether(wei)
        assert result == "0"

    def test_format_ether_large_amount(self):
        """Test formatting large amounts."""
        wei = "1000000000000000000000"  # 1000 ETH
        result = BlockchainService._format_ether(wei)
        assert result == "1000"

    def test_format_token_balance(self):
        """Test formatting token balance with decimals."""
        balance = "1000000000000000000"  # 1 token with 18 decimals
        decimals = 18
        result = BlockchainService._format_token_balance(balance, decimals)
        assert result == "1"

    def test_format_token_balance_usdc(self):
        """Test formatting USDC balance (6 decimals)."""
        balance = "1000000"  # 1 USDC
        decimals = 6
        result = BlockchainService._format_token_balance(balance, decimals)
        assert result == "1"

    def test_format_token_balance_zero(self):
        """Test formatting zero token balance."""
        balance = "0"
        decimals = 18
        result = BlockchainService._format_token_balance(balance, decimals)
        assert result == "0"

    def test_format_ether_invalid(self):
        """Test formatting with invalid value."""
        wei = "not_a_number"
        result = BlockchainService._format_ether(wei)
        assert result == "0"
