"""Unit tests for wallet analysis service."""

from datetime import datetime, timedelta

import pytest

from models.transaction import Transaction, TransactionSummary, TransactionType
from models.wallet import ActivityLevel, WalletBehavior
from services.analysis_service import AnalysisService


@pytest.fixture
def sample_transactions():
    """Create sample transactions for testing."""
    base_date = datetime.utcnow()
    return [
        Transaction(
            hash="0x" + "a" * 64,
            from_address="0x1234567890123456789012345678901234567890",
            to_address="0x0000000000000000000000000000000000000000",
            value="1000000000000000000",
            value_display="1.0",
            gas_price="20000000000",
            gas_used="21000",
            timestamp=base_date - timedelta(days=i),
            block_number=1000000 - i,
            is_error=False,
            type=TransactionType.SEND if i % 2 == 0 else TransactionType.RECEIVE,
            method_id=None,
        )
        for i in range(5)
    ]


class TestActivityDetection:
    """Tests for activity level detection."""

    def test_dormant_no_transactions(self):
        """Test dormant classification with no transactions."""
        result = AnalysisService.detect_activity_level([])
        assert result == ActivityLevel.DORMANT

    def test_dormant_few_transactions(self):
        """Test dormant classification with few transactions."""
        transactions = [
            Transaction(
                hash="0x" + "a" * 64,
                from_address="0x1234567890123456789012345678901234567890",
                to_address=None,
                value="0",
                value_display="0",
                gas_price="20000000000",
                gas_used="21000",
                timestamp=datetime.utcnow(),
                block_number=1000000,
                is_error=False,
                type=TransactionType.SEND,
                method_id=None,
            )
        ]
        result = AnalysisService.detect_activity_level(transactions)
        assert result == ActivityLevel.DORMANT

    def test_low_activity(self):
        """Test low activity classification."""
        transactions = [
            Transaction(
                hash="0x" + str(i) * 64,
                from_address="0x1234567890123456789012345678901234567890",
                to_address=None,
                value="0",
                value_display="0",
                gas_price="20000000000",
                gas_used="21000",
                timestamp=datetime.utcnow(),
                block_number=1000000 - i,
                is_error=False,
                type=TransactionType.SEND,
                method_id=None,
            )
            for i in range(8)
        ]
        result = AnalysisService.detect_activity_level(transactions)
        assert result == ActivityLevel.LOW

    def test_moderate_activity(self):
        """Test moderate activity classification."""
        transactions = [
            Transaction(
                hash="0x" + str(i % 10) * 64,
                from_address="0x1234567890123456789012345678901234567890",
                to_address=None,
                value="0",
                value_display="0",
                gas_price="20000000000",
                gas_used="21000",
                timestamp=datetime.utcnow(),
                block_number=1000000 - i,
                is_error=False,
                type=TransactionType.SEND,
                method_id=None,
            )
            for i in range(50)
        ]
        result = AnalysisService.detect_activity_level(transactions)
        assert result == ActivityLevel.MODERATE

    def test_active(self):
        """Test active classification."""
        transactions = [
            Transaction(
                hash="0x" + str(i % 10) * 64,
                from_address="0x1234567890123456789012345678901234567890",
                to_address=None,
                value="0",
                value_display="0",
                gas_price="20000000000",
                gas_used="21000",
                timestamp=datetime.utcnow(),
                block_number=1000000 - i,
                is_error=False,
                type=TransactionType.SEND,
                method_id=None,
            )
            for i in range(150)
        ]
        result = AnalysisService.detect_activity_level(transactions)
        assert result == ActivityLevel.ACTIVE

    def test_highly_active(self):
        """Test highly active classification."""
        transactions = [
            Transaction(
                hash="0x" + str(i % 10) * 64,
                from_address="0x1234567890123456789012345678901234567890",
                to_address=None,
                value="0",
                value_display="0",
                gas_price="20000000000",
                gas_used="21000",
                timestamp=datetime.utcnow(),
                block_number=1000000 - i,
                is_error=False,
                type=TransactionType.SEND,
                method_id=None,
            )
            for i in range(1500)
        ]
        result = AnalysisService.detect_activity_level(transactions)
        assert result == ActivityLevel.HIGHLY_ACTIVE


class TestDeFiDetection:
    """Tests for DeFi usage detection."""

    def test_no_defi_no_transactions(self):
        """Test no DeFi usage with no transactions."""
        result = AnalysisService.detect_defi_usage([])
        assert result is False

    def test_no_defi_contract_interactions(self):
        """Test no DeFi when no contract interactions."""
        transactions = [
            Transaction(
                hash="0x" + str(i) * 64,
                from_address="0x1234567890123456789012345678901234567890",
                to_address="0x1111111111111111111111111111111111111111",
                value="1000000000000000000",
                value_display="1.0",
                gas_price="20000000000",
                gas_used="21000",
                timestamp=datetime.utcnow(),
                block_number=1000000 - i,
                is_error=False,
                type=TransactionType.SEND,
                method_id=None,
            )
            for i in range(10)
        ]
        result = AnalysisService.detect_defi_usage(transactions)
        assert result is False

    def test_defi_user_contract_interactions(self):
        """Test DeFi detection with contract interactions."""
        transactions = [
            Transaction(
                hash="0x" + str(i) * 64,
                from_address="0x1234567890123456789012345678901234567890",
                to_address="0x1111111111111111111111111111111111111111",
                value="0",
                value_display="0",
                gas_price="20000000000",
                gas_used="200000",
                timestamp=datetime.utcnow(),
                block_number=1000000 - i,
                is_error=False,
                type=TransactionType.CONTRACT_INTERACTION,
                method_id="0xa9059cbb",  # transfer method
            )
            for i in range(20)
        ]
        result = AnalysisService.detect_defi_usage(transactions)
        assert result is True


class TestWalletScoring:
    """Tests for wallet score calculation."""

    def test_dormant_wallet_score(self):
        """Test scoring for dormant wallet."""
        transaction_summary = TransactionSummary(
            total_transactions=0,
            last_transactions=[],
            unique_interacted_addresses=0,
            contract_interactions=0,
            failed_transactions=0,
        )

        score = AnalysisService.calculate_wallet_score(
            activity_level=ActivityLevel.DORMANT,
            transaction_summary=transaction_summary,
            defi_user=False,
            nft_trader=False,
            contract_deployer=False,
        )

        assert 0 <= score <= 100
        assert score < 20  # Should be low for dormant wallet

    def test_highly_active_defi_score(self):
        """Test scoring for highly active DeFi user."""
        transaction_summary = TransactionSummary(
            total_transactions=1000,
            last_transactions=[],
            unique_interacted_addresses=100,
            contract_interactions=500,
            failed_transactions=5,
        )

        score = AnalysisService.calculate_wallet_score(
            activity_level=ActivityLevel.HIGHLY_ACTIVE,
            transaction_summary=transaction_summary,
            defi_user=True,
            nft_trader=True,
            contract_deployer=True,
        )

        assert 0 <= score <= 100
        assert score > 70  # Should be high for active DeFi user

    def test_score_capped_at_100(self):
        """Test that score is capped at 100."""
        transaction_summary = TransactionSummary(
            total_transactions=10000,
            last_transactions=[],
            unique_interacted_addresses=1000,
            contract_interactions=9000,
            failed_transactions=10,
        )

        score = AnalysisService.calculate_wallet_score(
            activity_level=ActivityLevel.HIGHLY_ACTIVE,
            transaction_summary=transaction_summary,
            defi_user=True,
            nft_trader=True,
            contract_deployer=True,
        )

        assert score <= 100


class TestDaysActive:
    """Tests for days active calculation."""

    def test_days_active_no_transactions(self):
        """Test days active with no transactions."""
        days_active, first_tx_date = AnalysisService.calculate_days_active([])
        assert days_active == 0

    def test_days_active_recent_transactions(self):
        """Test days active with recent transactions."""
        now = datetime.utcnow()
        transactions = [
            Transaction(
                hash="0x" + str(i) * 64,
                from_address="0x1234567890123456789012345678901234567890",
                to_address=None,
                value="0",
                value_display="0",
                gas_price="20000000000",
                gas_used="21000",
                timestamp=now - timedelta(days=i),
                block_number=1000000 - i,
                is_error=False,
                type=TransactionType.SEND,
                method_id=None,
            )
            for i in range(30)
        ]

        days_active, first_tx_date = AnalysisService.calculate_days_active(transactions)

        assert days_active >= 29  # At least 29 days
        assert first_tx_date <= now
