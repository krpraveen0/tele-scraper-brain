from __future__ import annotations

from datetime import datetime, timezone
from typing import AsyncIterator, Awaitable, Callable

from telethon import TelegramClient, events
from telethon.tl.custom.message import Message

from app.config import Settings
from app.models import SignalAnalysis, TelegramSignal

SignalHandler = Callable[[TelegramSignal], Awaitable[SignalAnalysis | None]]


class TelegramSignalClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.client = TelegramClient(
            settings.telegram_session_name,
            settings.tg_api_id,
            settings.tg_api_hash,
        )

    async def start(self) -> None:
        await self.client.start(phone=self.settings.tg_phone)

    async def run_monitor(self, handler: SignalHandler) -> None:
        @self.client.on(events.NewMessage(chats=self.settings.source_chats))
        async def on_message(event: events.NewMessage.Event) -> None:
            signal = await self._message_to_signal(event.message)
            await handler(signal)

        await self.start()
        print("Telegram monitor started. Press Ctrl+C to stop.")
        await self.client.run_until_disconnected()

    async def iter_recent_signals(self, limit_per_source: int) -> AsyncIterator[TelegramSignal]:
        """Yield recent historical messages from each configured source.

        Messages are yielded oldest-to-newest within each source so backfill processing
        behaves closer to live monitoring and preserves chronological context in logs.
        """
        await self.start()

        for source in self.settings.source_chats:
            messages: list[Message] = []
            async for message in self.client.iter_messages(source, limit=limit_per_source):
                if not message.raw_text:
                    continue
                messages.append(message)

            for message in reversed(messages):
                yield await self._message_to_signal(message)

    async def send_saved_signal(self, signal: TelegramSignal, analysis: SignalAnalysis) -> None:
        destination_chat = self.settings.destination_for(signal, analysis)
        await self.client.send_message(
            destination_chat,
            self.format_saved_signal(signal, analysis),
            link_preview=False,
        )

    async def send_briefing(self, text: str) -> None:
        await self.client.send_message(
            self.settings.briefing_chat,
            text,
            link_preview=False,
        )

    async def disconnect(self) -> None:
        await self.client.disconnect()

    async def _message_to_signal(self, message: Message) -> TelegramSignal:
        chat = await message.get_chat()
        username = getattr(chat, "username", None)
        source_ref = f"@{username}" if username else None
        source_title = getattr(chat, "title", None) or username or str(message.chat_id)
        source_id = str(message.chat_id)
        message_date = message.date or datetime.now(timezone.utc)
        permalink = self._build_permalink(chat, message.id)
        return TelegramSignal(
            source_id=source_id,
            source_title=source_title,
            message_id=message.id,
            message_text=message.raw_text or "",
            message_date=message_date,
            permalink=permalink,
            source_ref=source_ref,
        )

    @staticmethod
    def _build_permalink(chat: object, message_id: int) -> str | None:
        username = getattr(chat, "username", None)
        if username:
            return f"https://t.me/{username}/{message_id}"
        return None

    @staticmethod
    def format_saved_signal(signal: TelegramSignal, analysis: SignalAnalysis) -> str:
        tags = " ".join(analysis.tags)
        link_line = f"\nOriginal link: {signal.permalink}" if signal.permalink else ""
        original = signal.message_text[:1200]
        if len(signal.message_text) > 1200:
            original += " ..."

        return f"""📌 Saved by Praveen Signal OS

Category: {analysis.category}
Score: {analysis.score}/10
Action: {analysis.suggested_action}

Why valuable:
{analysis.reason}

Summary:
{analysis.summary}

Source: {signal.source_title}{link_line}

Tags: {tags}

Original:
{original}""".strip()
