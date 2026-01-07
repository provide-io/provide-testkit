"""In-memory chat storage implementation.

Provides chat storage for testing and development without Redis.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from responsum.chat.models import ChatMessage


class MemoryChatStore:
    """In-memory chat message storage for testing.

    Provides the same interface as RedisChatStore but stores
    everything in memory.
    """

    def __init__(
        self,
        max_messages: int = 100,
        ttl_seconds: int = 3600,
    ) -> None:
        """Initialize in-memory chat store.

        Args:
            max_messages: Maximum messages to retain per session
            ttl_seconds: TTL (ignored in memory implementation)
        """
        self.max_messages = max_messages
        self.ttl_seconds = ttl_seconds

        self._messages: dict[str, list[ChatMessage]] = defaultdict(list)
        self._typing: dict[str, set[str]] = defaultdict(set)
        self._reactions: dict[str, dict[str, list[str]]] = defaultdict(dict)

    async def add_message(self, session_id: str, message: ChatMessage) -> None:
        """Store a chat message."""
        self._messages[session_id].insert(0, message)  # Newest first
        # Trim to max size
        if len(self._messages[session_id]) > self.max_messages:
            self._messages[session_id] = self._messages[session_id][: self.max_messages]

    async def get_history(self, session_id: str, limit: int = 50) -> list[ChatMessage]:
        """Retrieve chat message history in chronological order."""
        messages = self._messages.get(session_id, [])[:limit]
        # Reverse to get chronological order (oldest first)
        return list(reversed(messages))

    async def update_typing(self, session_id: str, player_id: str, is_typing: bool) -> set[str]:
        """Update typing indicator for a player."""
        if is_typing:
            self._typing[session_id].add(player_id)
        else:
            self._typing[session_id].discard(player_id)

        return self._typing[session_id].copy()

    async def add_reaction(
        self, session_id: str, message_id: str, player_id: str, emoji: str
    ) -> dict[str, list[str]]:
        """Add a reaction to a message."""
        key = f"{session_id}:{message_id}"
        if key not in self._reactions:
            self._reactions[key] = {}

        reactions = self._reactions[key]
        if emoji not in reactions:
            reactions[emoji] = []
        if player_id not in reactions[emoji]:
            reactions[emoji].append(player_id)

        return reactions

    async def remove_reaction(
        self, session_id: str, message_id: str, player_id: str, emoji: str
    ) -> dict[str, list[str]]:
        """Remove a reaction from a message."""
        key = f"{session_id}:{message_id}"
        if key not in self._reactions:
            return {}

        reactions = self._reactions[key]
        if emoji in reactions and player_id in reactions[emoji]:
            reactions[emoji].remove(player_id)
            if not reactions[emoji]:
                del reactions[emoji]

        return reactions

    async def clear_session_chat(self, session_id: str) -> None:
        """Clear all chat data for a session."""
        self._messages.pop(session_id, None)
        self._typing.pop(session_id, None)

        # Clear reactions for this session
        keys_to_remove = [k for k in self._reactions if k.startswith(f"{session_id}:")]
        for key in keys_to_remove:
            del self._reactions[key]


class MemoryChatRateLimiter:
    """In-memory rate limiting for chat messages.

    Provides the same interface as ChatRateLimiter but stores
    counters in memory.
    """

    def __init__(
        self,
        max_messages: int = 10,
        window_seconds: int = 60,
    ) -> None:
        """Initialize rate limiter.

        Args:
            max_messages: Maximum messages per window
            window_seconds: Window duration in seconds (ignored in memory)
        """
        self.max_messages = max_messages
        self.window_seconds = window_seconds
        self._counts: dict[str, int] = defaultdict(int)

    def _key(self, session_id: str, player_id: str) -> str:
        return f"{session_id}:{player_id}"

    async def check_rate_limit(self, session_id: str, player_id: str) -> bool:
        """Check if player can send a message and increment counter."""
        key = self._key(session_id, player_id)

        if self._counts[key] >= self.max_messages:
            return False

        self._counts[key] += 1
        return True

    async def get_remaining(self, session_id: str, player_id: str) -> int:
        """Get remaining messages in current window."""
        key = self._key(session_id, player_id)
        return max(0, self.max_messages - self._counts[key])

    def reset(self, session_id: str | None = None, player_id: str | None = None) -> None:
        """Reset rate limits (for testing)."""
        if session_id is None and player_id is None:
            self._counts.clear()
        elif session_id and player_id:
            key = self._key(session_id, player_id)
            self._counts.pop(key, None)


__all__ = ["MemoryChatStore", "MemoryChatRateLimiter"]
