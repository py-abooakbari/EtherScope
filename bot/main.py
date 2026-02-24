"""Main Telegram bot application for EtherScope."""

from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from core.config import Config
from core.logger import get_logger

from .handlers import analyze, health, start, callback_router, text_router

logger = get_logger(__name__)


class EtherScopeBot:
    """Main bot application class."""

    def __init__(self) -> None:
        """Initialize bot application."""
        self.app: Application | None = None

    def create_app(self) -> Application:
        """Create and configure Telegram bot application.

        Returns:
            Configured Application instance

        """
        logger.info("Creating EtherScope bot application")
        print("   Creating bot application...")

        # Create application with bot token
        self.app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

        # Register command handlers
        self._register_handlers()

        logger.info("Bot application created successfully")
        return self.app

    def _register_handlers(self) -> None:
        """Register command handlers with bot."""
        if not self.app:
            raise RuntimeError("Application not initialized")

        logger.debug("Registering command handlers")
        print(f"   Registering command handlers...")

        # Add handlers
        self.app.add_handler(CommandHandler("start", start))
        self.app.add_handler(CommandHandler("analyze", analyze))
        self.app.add_handler(CommandHandler("health", health))
        # handle inline callbacks
        self.app.add_handler(CallbackQueryHandler(callback_router))
        # handle plain text for address input
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    

        logger.debug("Command handlers registered: /start, /analyze, /health")
        print(f"   ✅ Handlers registered: /start, /analyze, /health")
