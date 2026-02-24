"""Wallet analysis service for EtherScope."""

from datetime import datetime, timedelta

from core.config import Config
from core.logger import get_logger
from models.transaction import Transaction, TransactionSummary
from models.wallet import ActivityLevel, WalletBehavior

logger = get_logger(__name__)

# Known DeFi contract interactions patterns
DEFI_KEYWORDS = [
    "uniswap",
    "aave",
    "curve",
    "lido",
    "compound",
    "maker",
    "yearn",
    "sushiswap",
    "lp_tokens",
]

# Known NFT contract addresses (simplified set)
NFT_CONTRACT_PATTERNS = ["0x" + "0" * 40]  # Placeholder


class AnalysisService:
    """Service for analyzing wallet behavior and characteristics."""

    @staticmethod
    def detect_activity_level(transactions: list[Transaction]) -> ActivityLevel:
        """Classify wallet activity level based on transaction count.

        Args:
            transactions: List of transactions

        Returns:
            ActivityLevel classification

        """
        if not transactions:
            return ActivityLevel.DORMANT

        total_txs = len(transactions)

        if total_txs >= 1000:
            return ActivityLevel.HIGHLY_ACTIVE
        elif total_txs >= 100:
            return ActivityLevel.ACTIVE
        elif total_txs >= 20:
            return ActivityLevel.MODERATE
        elif total_txs >= 5:
            return ActivityLevel.LOW
        else:
            return ActivityLevel.DORMANT

    @staticmethod
    def detect_defi_usage(transactions: list[Transaction]) -> bool:
        """Detect if wallet has interacted with DeFi protocols.

        Args:
            transactions: List of transactions

        Returns:
            True if DeFi usage detected

        """
        if not transactions:
            return False

        # Check for contract interactions (non-zero input data)
        contract_interactions = sum(
            1 for tx in transactions if tx.method_id and tx.method_id != "0x"
        )

        # Simple heuristic: if more than 20% of transactions are contract interactions,
        # likely a DeFi user
        defi_threshold = len(transactions) * 0.2
        is_defi_user = contract_interactions >= max(defi_threshold, Config.DEFI_CONTRACT_THRESHOLD)

        logger.debug(
            f"DeFi detection: {contract_interactions} contract interactions "
            f"out of {len(transactions)} transactions. DeFi user: {is_defi_user}"
        )

        return is_defi_user

    @staticmethod
    def detect_nft_trader(transactions: list[Transaction]) -> bool:
        """Detect if wallet has traded NFTs.

        Args:
            transactions: List of transactions

        Returns:
            True if NFT trading detected

        """
        if not transactions:
            return False

        # Look for common NFT contract interaction patterns
        # This is a simplified implementation
        nft_interactions = sum(1 for tx in transactions if "nft" in str(tx.method_id or "").lower())

        is_nft_trader = nft_interactions > 0

        logger.debug(f"NFT trading detection: {nft_interactions} NFT interactions detected")

        return is_nft_trader

    @staticmethod
    def detect_contract_deployer(transactions: list[Transaction]) -> bool:
        """Detect if wallet has deployed contracts.

        Args:
            transactions: List of transactions

        Returns:
            True if contract deployment detected

        """
        if not transactions:
            return False

        # Contract deployment typically has empty 'to' address
        deployments = sum(1 for tx in transactions if tx.to_address is None)

        is_deployer = deployments > 0

        logger.debug(f"Contract deployment detection: {deployments} deployments found")

        return is_deployer

    @staticmethod
    def calculate_wallet_score(
        activity_level: ActivityLevel,
        transaction_summary: TransactionSummary,
        defi_user: bool,
        nft_trader: bool,
        contract_deployer: bool,
    ) -> int:
        """Calculate overall wallet score (0-100).

        Scoring factors:
        - Transaction frequency (40%)
        - Contract interactions (30%)
        - Token diversity (15%)
        - Advanced activities - DeFi, NFT, deployment (15%)

        Args:
            activity_level: Detected activity level
            transaction_summary: Transaction summary with statistics
            defi_user: Whether wallet uses DeFi
            nft_trader: Whether wallet trades NFTs
            contract_deployer: Whether wallet deployed contracts

        Returns:
            Wallet score 0-100

        """
        score = 0

        # Transaction frequency component (40 points)
        activity_scores = {
            ActivityLevel.DORMANT: 0,
            ActivityLevel.LOW: 10,
            ActivityLevel.MODERATE: 20,
            ActivityLevel.ACTIVE: 30,
            ActivityLevel.HIGHLY_ACTIVE: 40,
        }
        score += activity_scores.get(activity_level, 0)

        # Contract interactions component (30 points)
        contract_interaction_ratio = (
            transaction_summary.contract_interactions / max(transaction_summary.total_transactions, 1)
        )
        if contract_interaction_ratio >= 0.5:
            score += 30
        elif contract_interaction_ratio >= 0.3:
            score += 20
        elif contract_interaction_ratio >= 0.1:
            score += 10
        else:
            score += 5

        # Token diversity component (15 points)
        # More tokens = higher score (cap at 15)
        token_diversity_score = min(transaction_summary.unique_interacted_addresses // 10, 15)
        score += token_diversity_score

        # Advanced activities component (15 points)
        advanced_activities = sum([defi_user, nft_trader, contract_deployer])
        advanced_score = advanced_activities * 5
        score += min(advanced_score, 15)

        # Cap at 100
        final_score = min(score, 100)

        logger.debug(f"Wallet score calculated: {final_score} (breakdowne: components above)")

        return final_score

    @staticmethod
    def analyze_wallet_behavior(
        transaction_summary: TransactionSummary, total_transactions: int
    ) -> WalletBehavior:
        """Comprehensive wallet behavior analysis.

        Args:
            transaction_summary: Transaction summary
            total_transactions: Total transaction count for the wallet

        Returns:
            WalletBehavior object with analysis results

        """
        logger.debug(f"Starting wallet behavior analysis for {total_transactions} transactions")

        # Get all transactions for analysis
        recent_transactions = transaction_summary.last_transactions

        # Detect patterns
        activity_level = AnalysisService.detect_activity_level(recent_transactions)
        defi_user = AnalysisService.detect_defi_usage(recent_transactions)
        nft_trader = AnalysisService.detect_nft_trader(recent_transactions)
        contract_deployer = AnalysisService.detect_contract_deployer(recent_transactions)

        # Calculate score
        wallet_score = AnalysisService.calculate_wallet_score(
            activity_level=activity_level,
            transaction_summary=transaction_summary,
            defi_user=defi_user,
            nft_trader=nft_trader,
            contract_deployer=contract_deployer,
        )

        behavior = WalletBehavior(
            activity_level=activity_level,
            defi_user=defi_user,
            nft_trader=nft_trader,
            contract_deployer=contract_deployer,
            wallet_score=wallet_score,
        )

        logger.debug(f"Wallet behavior analysis complete: {behavior}")

        return behavior

    @staticmethod
    def calculate_days_active(transactions: list[Transaction]) -> tuple[int, datetime]:
        """Calculate days account has been active and first transaction date.

        Args:
            transactions: List of transactions

        Returns:
            Tuple of (days_active, first_transaction_date)

        """
        if not transactions:
            return 0, datetime.utcnow()

        # Find oldest transaction
        oldest_tx = min(transactions, key=lambda t: t.timestamp)
        first_tx_date = oldest_tx.timestamp

        days_active = (datetime.utcnow() - first_tx_date).days

        logger.debug(f"Wallet active for {days_active} days since {first_tx_date}")

        return days_active, first_tx_date
