from typing import Protocol

import httpx


class Notifier(Protocol):
    async def notify(self, message: str) -> None: ...


class NullNotifier:
    async def notify(self, message: str) -> None:
        return None


class SlackWebhookNotifier:
    def __init__(self, webhook_url: str) -> None:
        self.webhook_url = webhook_url

    async def notify(self, message: str) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(self.webhook_url, json={"text": message})
            response.raise_for_status()
