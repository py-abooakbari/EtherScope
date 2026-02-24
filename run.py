"""Entry point for EtherScope Telegram bot."""

from bot.main import EtherScopeBot
from core.config import Config
from core.logger import get_logger, setup_logging

# Setup logging
setup_logging()
logger = get_logger(__name__)


def main() -> None:
    """Main entry point for the bot."""
    logger.info("=" * 60)
    logger.info("Starting EtherScope - Web3 Wallet Intelligence Bot")
    logger.info("=" * 60)
    
    print("\n" + "=" * 60)
    print("🤖 EtherScope - Web3 Wallet Intelligence Bot")
    print("=" * 60)

    # Validate configuration
    try:
        Config.validate()
        logger.info(f"Configuration validated successfully")
        logger.info(f"  - Environment: {Config.ENVIRONMENT}")
        logger.info(f"  - Blockchain Provider: {Config.BLOCKCHAIN_API_PROVIDER}")
        logger.info(f"  - Cache Enabled: {Config.CACHE_ENABLED}")
        
        print(f"\n✅ Configuration validated!")
        print(f"   Environment: {Config.ENVIRONMENT}")
        print(f"   Blockchain Provider: {Config.BLOCKCHAIN_API_PROVIDER}")
        print(f"   Cache Enabled: {Config.CACHE_ENABLED}")
    except Exception as e:
        logger.error(f"Configuration validation failed: {str(e)}")
        raise

    # Create bot
    bot = EtherScopeBot()
    app = bot.create_app()
    
    print(f"\n✅ Bot application created successfully")
    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🚀 Bot is now RUNNING and listening for messages...")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"\n📱 Open Telegram and send these commands to your bot:")
    print(f"   /start - Show welcome message")
    print(f"   /analyze <wallet_address> - Analyze a wallet")
    print(f"   /health - Check bot status")
    print(f"\n💡 Example:")
    print(f"   /analyze 0xd8da6bf26964af9d7eed9e03e53415d37aa96045")
    print(f"\n⏹️  Press Ctrl+C to stop the bot")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    
    # Run the bot (this will manage the event loop internally)
    app.run_polling(allowed_updates=["message", "callback_query"], drop_pending_updates=False)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot interrupted by user")
        print("\n\n⏹️  Bot stopped.")
    except Exception as e:
        logger.error(f"Bot crashed: {str(e)}", exc_info=True)
        print(f"\n\n❌ Bot crashed: {str(e)}")
        exit(1)
