"""Unit tests for Telegram bot handlers."""

import pytest
from types import SimpleNamespace

from bot import handlers


class DummyMessage:
    def __init__(self):
        self.replies = []

    async def reply_html(self, msg, **kwargs):
        self.replies.append(msg)

    async def reply_text(self, msg, **kwargs):
        self.replies.append(msg)


class DummyCallbackQuery:
    def __init__(self, data):
        self.data = data
        self.message = DummyMessage()
        self.from_user = SimpleNamespace(id=1)
        self.answered = False

    async def answer(self):
        self.answered = True


class DummyUpdate:
    def __init__(self, callback_query=None, message=None):
        self.callback_query = callback_query
        self.message = message
        self.effective_user = (
            callback_query.from_user if callback_query else (message.from_user if message else None)
        )
        self.effective_chat = SimpleNamespace(id=123)


class DummyContext:
    def __init__(self):
        self.args = []

        async def send_chat_action(*args, **kwargs):
            # mimic bot typing indicator; do nothing
            return None

        self.bot = SimpleNamespace(send_chat_action=send_chat_action)


@pytest.mark.asyncio
async def test_health_button_callback(monkeypatch):
    update = DummyUpdate(callback_query=DummyCallbackQuery("health"))
    context = DummyContext()
    await handlers.callback_router(update, context)

    # callback should be answered
    assert update.callback_query.answered is True

    # health message should be sent
    assert update.callback_query.message.replies
    assert "EtherScope Bot Status" in update.callback_query.message.replies[0]


@pytest.mark.asyncio
async def test_callback_query_too_old(monkeypatch):
    """Simulate BadRequest when answering a callback query."""
    class ExpiredQuery(DummyCallbackQuery):
        async def answer(self):
            raise handlers.BadRequest("Query is too old")

    update = DummyUpdate(callback_query=ExpiredQuery("health"))
    context = DummyContext()
    # should not raise even though answer throws
    await handlers.callback_router(update, context)

    # health message still delivered
    assert update.callback_query.message.replies
    assert "EtherScope Bot Status" in update.callback_query.message.replies[0]


@pytest.mark.asyncio
async def test_analyze_button_sets_state(monkeypatch):
    update = DummyUpdate(callback_query=DummyCallbackQuery("analyze"))
    context = DummyContext()
    await handlers.callback_router(update, context)

    # state should be set for the user
    assert handlers.user_states.get(1) == "awaiting_wallet"
    assert update.callback_query.message.replies
    assert "wallet address" in update.callback_query.message.replies[0]


@pytest.mark.asyncio
async def test_text_router_triggers_analysis(monkeypatch):
    called = []

    async def fake_analysis(u, c, addr):
        called.append(addr)

    monkeypatch.setattr(handlers, "perform_analysis", fake_analysis)

    # set up state for user 1
    handlers.user_states[1] = "awaiting_wallet"

    msg = DummyMessage()
    msg.text = "0xABCDEF"
    msg.from_user = SimpleNamespace(id=1)
    update = DummyUpdate(message=msg)
    context = DummyContext()

    await handlers.text_router(update, context)

    assert called == ["0xABCDEF"]
    # state should have been cleared
    assert 1 not in handlers.user_states


@pytest.mark.asyncio
async def test_text_router_ignores_without_state(monkeypatch):
    msg = DummyMessage()
    msg.text = "just some text"
    msg.from_user = SimpleNamespace(id=2)
    update = DummyUpdate(message=msg)
    context = DummyContext()

    await handlers.text_router(update, context)
    assert "Please use the buttons" in msg.replies[0]


@pytest.mark.asyncio
async def test_perform_analysis_handles_blockchain_error(monkeypatch):
    # bypass address validation so blockchain call is attempted
    monkeypatch.setattr(handlers.BlockchainService, "validate_address", lambda a: a)

    # make blockchain_service raise error during balance fetch
    async def fake_get_eth_balance(addr):
        raise handlers.BlockchainServiceError("Etherscan error: NOTOK")

    monkeypatch.setattr(handlers.blockchain_service, "get_eth_balance", fake_get_eth_balance)

    msg = DummyMessage()
    msg.text = "0x0000000000000000000000000000000000000000"
    msg.from_user = SimpleNamespace(id=3)
    update = DummyUpdate(message=msg)
    context = DummyContext()

    await handlers.perform_analysis(update, context, "0x0000000000000000000000000000000000000000")
    # should reply with error message containing "Blockchain API Error"
    assert any("Blockchain API Error" in r for r in msg.replies)
