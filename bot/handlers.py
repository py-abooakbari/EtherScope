"""Telegram bot handlers for EtherScope."""

from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ChatAction
from telegram.error import BadRequest
from telegram.ext import ContextTypes, CallbackQueryHandler, MessageHandler, filters

# simple in-memory user state tracker
user_states: dict[int, str] = {}

from core.config import Config
from core.exceptions import (
    BlockchainServiceError,
    EtherScopeException,
    InvalidWalletAddressError,
)
from core.logger import get_logger
from models.wallet import ActivityLevel, WalletAnalysis
from services.analysis_service import AnalysisService
from services.blockchain_service import BlockchainService
from services.cache_service import get_cache_service

logger = get_logger(__name__)

# Initialize services
blockchain_service = BlockchainService()
cache_service = get_cache_service()


async def perform_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE, wallet_address: str) -> None:
    """Common analysis logic extracted from analyze command.

    Args:
        update: Telegram update that triggered the analysis
        context: Telegram context
        wallet_address: Address to analyze
    """
    user_id = update.effective_user.id if update.effective_user else "unknown"

    try:
        # validate
        wallet_address = BlockchainService.validate_address(wallet_address)

        # show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING,
        )

        # check cache
        cache_key = f"analysis:{wallet_address}"
        cached_analysis = cache_service.get(cache_key)
        if cached_analysis:
            logger.info(f"Returning cached analysis for {wallet_address}")
            msg = BotFormatter.format_wallet_analysis(cached_analysis)
            for chunk in _split_message(msg):
                await update.message.reply_html(chunk)
            return

        eth_balance = await blockchain_service.get_eth_balance(wallet_address)
        token_summary = await blockchain_service.get_erc20_tokens(wallet_address)
        transaction_summary = await blockchain_service.get_transactions(wallet_address, limit=10)

        behavior = AnalysisService.analyze_wallet_behavior(
            transaction_summary=transaction_summary,
            total_transactions=transaction_summary.total_transactions,
        )
        days_active, first_tx_date = AnalysisService.calculate_days_active(
            transaction_summary.last_transactions
        )

        eth_balance_display = BlockchainService._format_ether(eth_balance)
        analysis = WalletAnalysis(
            wallet_address=wallet_address,
            eth_balance=eth_balance,
            eth_balance_display=eth_balance_display,
            usd_value=None,
            token_summary=token_summary,
            transaction_summary=transaction_summary,
            behavior=behavior,
            first_transaction_date=first_tx_date,
            days_active=days_active,
        )

        cache_service.set(cache_key, analysis)

        msg = BotFormatter.format_wallet_analysis(analysis)
        for chunk in _split_message(msg):
            await update.message.reply_html(chunk)

        logger.info(f"Analysis sent for wallet {wallet_address}")

    except InvalidWalletAddressError as e:
        logger.warning(f"Invalid wallet address from user {user_id}: {str(e)}")
        await update.message.reply_html(BotFormatter.format_error_message(e))
    except BlockchainServiceError as e:
        logger.error(f"Blockchain service error for user {user_id}: {str(e)}")
        await update.message.reply_html(BotFormatter.format_error_message(e))
    except Exception as e:
        logger.error(f"Unexpected error during analysis for user {user_id}: {str(e)}")
        await update.message.reply_html(BotFormatter.format_error_message(e))


class BotFormatter:
    """Formatter for Telegram bot responses."""

    @staticmethod
    def format_wallet_analysis(analysis: WalletAnalysis) -> str:
        """Format wallet analysis for Telegram message.

        Args:
            analysis: WalletAnalysis object

        Returns:
            Formatted message string

        """
        message = (
            f"💼 <b>Wallet Analysis Report</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            f"<b>Address:</b>\n"
            f"<code>{analysis.wallet_address}</code>\n\n"
            f"<b>💰 ETH Balance</b>\n"
            f"Balance: <code>{analysis.eth_balance_display} ETH</code>\n"
        )

        if analysis.usd_value:
            message += f"Value: <code>${analysis.usd_value:,.2f}</code>\n"

        # Token summary
        message += (
            f"\n<b>🪙 Token Holdings</b>\n"
            f"Total Tokens: <code>{analysis.token_summary.total_tokens_held}</code>\n"
        )

        if analysis.token_summary.top_tokens:
            message += f"Top Tokens:\n"
            for token in analysis.token_summary.top_tokens[:5]:
                message += (
                    f"  • {token.symbol}: <code>{token.balance_display}</code>\n"
                )

        # Transaction summary
        message += (
            f"\n<b>📊 Transaction History</b>\n"
            f"Total Transactions: <code>{analysis.transaction_summary.total_transactions}</code>\n"
            f"Unique Addresses: <code>{analysis.transaction_summary.unique_interacted_addresses}</code>\n"
            f"Contract Interactions: <code>{analysis.transaction_summary.contract_interactions}</code>\n"
            f"Failed Transactions: <code>{analysis.transaction_summary.failed_transactions}</code>\n"
        )

        # Recent transactions
        if analysis.transaction_summary.last_transactions:
            message += f"\n<b>📝 Latest Transactions</b>\n"
            for tx in analysis.transaction_summary.last_transactions[:3]:
                direction = (
                    "↓" if tx.to_address and tx.to_address == analysis.wallet_address else "↑"
                )
                message += (
                    f"{direction} {tx.value_display} ETH - "
                    f"<code>{tx.hash[:10]}...</code>"
                    f" ({tx.timestamp.strftime('%Y-%m-%d')})\n"
                )

        # Behavioral analysis
        message += (
            f"\n<b>🎯 Behavioral Analysis</b>\n"
            f"Activity Level: <code>{analysis.behavior.activity_level.value.upper()}</code>\n"
            f"DeFi User: <code>{'Yes' if analysis.behavior.defi_user else 'No'}</code>\n"
            f"NFT Trader: <code>{'Yes' if analysis.behavior.nft_trader else 'No'}</code>\n"
            f"Contract Deployer: <code>{'Yes' if analysis.behavior.contract_deployer else 'No'}</code>\n"
            f"Wallet Score: <code>{analysis.behavior.wallet_score}/100</code>\n"
        )

        # Account age
        if analysis.days_active is not None and analysis.first_transaction_date:
            message += (
                f"\n<b>📅 Account History</b>\n"
                f"Active Days: <code>{analysis.days_active}</code>\n"
                f"First Transaction: <code>"
                f"{analysis.first_transaction_date.strftime('%Y-%m-%d')}</code>\n"
            )

        message += f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        message += f"Generated: {analysis.analyzed_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"

        return message

    @staticmethod
    def format_welcome_message() -> str:
        """Format welcome message.

        Returns:
            Welcome message

        """
        return (
            "👋 <b>Welcome to EtherScope</b>\n\n"
            "Your Web3 Wallet Intelligence Bot\n\n"
            "<b>📖 Available Commands:</b>\n\n"
            "/analyze [wallet_address]\n"
            "  Analyze an Ethereum wallet address\n\n"
            "/health\n"
            "  Check bot health status\n\n"
            "<b>💡 Example:</b>\n"
            "/analyze 0x1234567890123456789012345678901234567890\n\n"
            "Bot will provide detailed analysis including:\n"
            "  • ETH balance and token holdings\n"
            "  • Transaction statistics\n"
            "  • DeFi and NFT activity detection\n"
            "  • Behavioral classification\n"
            "  • Overall wallet score\n"
        )

    @staticmethod
    def format_error_message(error: Exception) -> str:
        """Format error message for user.

        Args:
            error: Exception object

        Returns:
            Formatted error message

        """
        if isinstance(error, InvalidWalletAddressError):
            return (
                f"❌ <b>Invalid Wallet Address</b>\n\n"
                f"Error: {str(error)}\n\n"
                f"Please provide a valid Ethereum address (42 characters starting with 0x)"
            )
        elif isinstance(error, BlockchainServiceError):
            return (
                f"❌ <b>Blockchain API Error</b>\n\n"
                f"Failed to fetch blockchain data. Please try again later.\n\n"
                f"Error: {str(error)}"
            )
        else:
            return (
                f"❌ <b>Analysis Error</b>\n\n"
                f"An unexpected error occurred. Please try again later."
            )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command and show buttons.

    Args:
        update: Telegram update
        context: Telegram context

    """
    try:
        user_id = update.effective_user.id if update.effective_user else "unknown"
        logger.info(f"User {user_id} started bot")
        print(f"✅ /start command received from user {user_id}")

        message = BotFormatter.format_welcome_message()
        # create inline buttons for analyze and health
        keyboard = [
            [InlineKeyboardButton("🔍 Analyze Wallet", callback_data="analyze")],
            [InlineKeyboardButton("📈 Health Check", callback_data="health")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_html(message, reply_markup=reply_markup)
        print(f"✅ Welcome message with buttons sent successfully")
    except Exception as e:
        logger.error(f"Error in /start handler: {str(e)}", exc_info=True)
        print(f"❌ Error in /start handler: {str(e)}")
        raise


async def analyze(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /analyze command from text or command.

    This method delegates to :func:`perform_analysis` with the extracted
    wallet address.
    """
    """Handle /analyze command.

    Args:
        update: Telegram update
        context: Telegram context

    """
    user_id = update.effective_user.id if update.effective_user else "unknown"

    try:
        # Determine wallet address either from command args or plain text
        wallet_address: str | None = None
        if context.args and len(context.args) > 0:
            wallet_address = context.args[0].strip()
        elif update.message and update.message.text:
            # when called after pressing analyze button, user may send address
            wallet_address = update.message.text.strip()

        if not wallet_address:
            await update.message.reply_html(
                "❌ <b>Missing wallet address</b>\n\n"
                "Usage: /analyze <wallet_address> or press the button below"
            )
            return

        # perform actual analysis
        await perform_analysis(update, context, wallet_address)
        return

        logger.info(
            f"Analysis requested by user {user_id} for wallet {wallet_address}"
        )

        # Show typing indicator
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id,
            action=ChatAction.TYPING,
        )

        # Validate address
        wallet_address = BlockchainService.validate_address(wallet_address)

        # Check cache
        cache_key = f"analysis:{wallet_address}"
        cached_analysis = cache_service.get(cache_key)

        if cached_analysis:
            logger.info(f"Returning cached analysis for {wallet_address}")
            message = BotFormatter.format_wallet_analysis(cached_analysis)
            # Split message if too long
            for chunk in _split_message(message):
                await update.message.reply_html(chunk)
            return

        # Fetch blockchain data
        logger.debug(f"Fetching blockchain data for {wallet_address}")

        eth_balance = await blockchain_service.get_eth_balance(wallet_address)
        token_summary = await blockchain_service.get_erc20_tokens(wallet_address)
        transaction_summary = await blockchain_service.get_transactions(wallet_address, limit=10)

        # Analyze behavior
        logger.debug(f"Analyzing wallet behavior for {wallet_address}")

        behavior = AnalysisService.analyze_wallet_behavior(
            transaction_summary=transaction_summary,
            total_transactions=transaction_summary.total_transactions,
        )

        # Calculate days active
        days_active, first_tx_date = AnalysisService.calculate_days_active(
            transaction_summary.last_transactions
        )

        # Create analysis result
        eth_balance_display = BlockchainService._format_ether(eth_balance)

        analysis = WalletAnalysis(
            wallet_address=wallet_address,
            eth_balance=eth_balance,
            eth_balance_display=eth_balance_display,
            usd_value=None,  # USD conversion would require price API
            token_summary=token_summary,
            transaction_summary=transaction_summary,
            behavior=behavior,
            first_transaction_date=first_tx_date,
            days_active=days_active,
        )

        # Cache result
        cache_service.set(cache_key, analysis)

        # Format and send response
        message = BotFormatter.format_wallet_analysis(analysis)

        # Split message if too long
        for chunk in _split_message(message):
            await update.message.reply_html(chunk)

        logger.info(f"Analysis sent for wallet {wallet_address}")

    except InvalidWalletAddressError as e:
        logger.warning(f"Invalid wallet address from user {user_id}: {str(e)}")
        message = BotFormatter.format_error_message(e)
        await update.message.reply_html(message)

    except BlockchainServiceError as e:
        logger.error(f"Blockchain service error for user {user_id}: {str(e)}")
        message = BotFormatter.format_error_message(e)
        await update.message.reply_html(message)

    except Exception as e:
        logger.error(f"Unexpected error during analysis for user {user_id}: {str(e)}")
        message = BotFormatter.format_error_message(e)
        await update.message.reply_html(message)


async def health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /health command or health button callback.

    Args:
        update: Telegram update
        context: Telegram context

    """
    # determine user and target message object regardless of update type
    user_id = None
    target = None

    if update.effective_user:
        user_id = update.effective_user.id

    # normal command comes with message
    if update.message:
        target = update.message
    # callback query will have the message inside it
    elif update.callback_query and update.callback_query.message:
        target = update.callback_query.message

    logger.info(f"Health check from user {user_id}")

    cache_stats = cache_service.get_stats()

    status_message = (
        f"✅ <b>EtherScope Bot Status</b>\n\n"
        f"<b>System Information</b>\n"
        f"Environment: <code>{Config.ENVIRONMENT}</code>\n"
        f"Blockchain Provider: <code>{Config.BLOCKCHAIN_API_PROVIDER}</code>\n"
        f"API Timeout: <code>{Config.API_TIMEOUT}s</code>\n\n"
        f"<b>Cache Status</b>\n"
        f"Enabled: <code>{'Yes' if cache_stats['enabled'] else 'No'}</code>\n"
        f"Size: <code>{cache_stats['size']}/{cache_stats['max_size']}</code>\n"
        f"Utilization: <code>{cache_stats['utilization']:.1%}</code>\n\n"
        f"<b>Bot Status</b>\n"
        f"Status: <code>🟢 Operational</code>\n"
        f"Timestamp: <code>{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</code>\n"
    )

    if target:
        await target.reply_html(status_message)
    else:
        # fallback: reply via context.bot if nothing else available
        chat_id = update.effective_chat.id if update.effective_chat else None
        if chat_id:
            await context.bot.send_message(chat_id=chat_id, text=status_message, parse_mode="HTML")




async def callback_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline button callbacks."""
    query = update.callback_query
    # answer the query early to remove the loading spinner; ignore if it's expired
    try:
        await query.answer()
    except BadRequest as exc:  # telegram.error.BadRequest
        logger.warning(f"Could not answer callback query, it may be too old: {exc}")

    user_id = query.from_user.id if query.from_user else None

    if query.data == "analyze":
        if user_id:
            user_states[user_id] = "awaiting_wallet"
        await query.message.reply_html("Please send the <b>wallet address</b> you want to analyze.")
    elif query.data == "health":
        # reuse health handler by crafting fake update
        await health(update, context)


async def text_router(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Catch-all for text messages to support wallet input after button."""
    user_id = update.effective_user.id if update.effective_user else None
    if user_id and user_states.get(user_id) == "awaiting_wallet":
        address = update.message.text.strip()
        user_states.pop(user_id, None)
        await perform_analysis(update, context, address)
    else:
        # ignore or provide help
        await update.message.reply_text("Please use the buttons above or commands like /analyze <address>.")


def _split_message(message: str, max_length: int = Config.TELEGRAM_MAX_MESSAGE_LENGTH) -> list[str]:
    """Split long message into chunks.

    Args:
        message: Message to split
        max_length: Maximum length per chunk

    Returns:
        List of message chunks

    """
    if len(message) <= max_length:
        return [message]

    chunks = []
    current_chunk = ""

    for line in message.split("\n"):
        if len(current_chunk) + len(line) + 1 > max_length:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = line + "\n"
        else:
            current_chunk += line + "\n"

    if current_chunk:
        chunks.append(current_chunk)

    return chunks
