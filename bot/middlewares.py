"""Telegram bot middleware for EtherScope."""

import time
from typing import Any, Callable

from telegram import Update
from telegram.ext import ContextTypes

from core.logger import get_logger

logger = get_logger(__name__)


class RequestLoggingMiddleware:
    """Middleware for logging incoming requests."""

    @staticmethod
    async def log_update(
        update: Update, context: ContextTypes.DEFAULT_TYPE, next_handler: Callable
    ) -> Any:
        """Log incoming update.

        Args:
            update: Telegram update
            context: Telegram context
            next_handler: Next handler in middleware chain

        Returns:
            Result from next handler

        """
        user_id = update.effective_user.id if update.effective_user else "unknown"
        chat_id = update.effective_chat.id if update.effective_chat else "unknown"

        if update.message:
            text = update.message.text or ""
            logger.info(
                f"Message from user {user_id} in chat {chat_id}: {text[:50]}"
            )
        elif update.callback_query:
            data = update.callback_query.data or ""
            logger.info(
                f"Callback query from user {user_id}: {data}"
            )

        return await next_handler(update, context)


class PerformanceMiddleware:
    """Middleware for tracking request performance."""

    @staticmethod
    async def track_performance(
        update: Update, context: ContextTypes.DEFAULT_TYPE, next_handler: Callable
    ) -> Any:
        """Track request performance.

        Args:
            update: Telegram update
            context: Telegram context
            next_handler: Next handler in middleware chain

        Returns:
            Result from next handler

        """
        start_time = time.time()
        user_id = update.effective_user.id if update.effective_user else "unknown"

        try:
            result = await next_handler(update, context)
        finally:
            elapsed = time.time() - start_time
            logger.debug(
                f"Request from user {user_id} completed in {elapsed:.2f}s"
            )

        return result


class ErrorHandlingMiddleware:
    """Middleware for handling errors."""

    @staticmethod
    async def handle_errors(
        update: Update, context: ContextTypes.DEFAULT_TYPE, next_handler: Callable
    ) -> Any:
        """Handle errors in update processing.

        Args:
            update: Telegram update
            context: Telegram context
            next_handler: Next handler in middleware chain

        Returns:
            Result from next handler

        """
        try:
            return await next_handler(update, context)
        except Exception as e:
            user_id = update.effective_user.id if update.effective_user else "unknown"
            logger.error(
                f"Unhandled error processing update from user {user_id}: {str(e)}",
                exc_info=True,
            )
            # Send error message to user
            if update.message:
                try:
                    await update.message.reply_text(
                        "❌ An unexpected error occurred. "
                        "Please try again later or contact support."
                    )
                except Exception as send_error:
                    logger.error(f"Failed to send error message: {str(send_error)}")

            raise
