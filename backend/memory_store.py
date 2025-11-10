import asyncio
from collections import deque
from copy import deepcopy
from typing import Any, Deque, Dict, List, Optional

from chatkit.store import NotFoundError, Store
from chatkit.types import Attachment, Page, ThreadItem, ThreadMetadata


def _clone(model):
    if hasattr(model, "model_copy"):
        return model.model_copy(deep=True)
    return deepcopy(model)


class MemoryStore(Store[Dict[str, Any]]):
    def __init__(self) -> None:
        self._threads: Dict[str, ThreadMetadata] = {}
        self._items: Dict[str, Deque[ThreadItem]] = {}
        self._attachments: Dict[str, Attachment] = {}
        self._lock = asyncio.Lock()

    async def load_thread(
        self, thread_id: str, context: Dict[str, Any]
    ) -> ThreadMetadata:
        async with self._lock:
            thread = self._threads.get(thread_id)
            if not thread:
                raise NotFoundError(f"Thread {thread_id} not found")
            return _clone(thread)

    async def save_thread(
        self, thread: ThreadMetadata, context: Dict[str, Any]
    ) -> None:
        async with self._lock:
            self._threads[thread.id] = _clone(thread)
            self._items.setdefault(thread.id, deque())

    async def load_thread_items(
        self,
        thread_id: str,
        after: Optional[str],
        limit: int,
        order: str,
        context: Dict[str, Any],
    ) -> Page[ThreadItem]:
        async with self._lock:
            items = self._items.get(thread_id)
            if items is None:
                raise NotFoundError(f"Thread {thread_id} not found")

            ordered: List[ThreadItem]
            if order == "asc":
                ordered = list(items)
            else:
                ordered = list(reversed(items))

            start = 0
            if after:
                for idx, item in enumerate(ordered):
                    if item.id == after:
                        start = idx + 1
                        break
                else:
                    raise NotFoundError(f"Item {after} not found in thread {thread_id}")

            subset = ordered[start : start + limit] if limit else ordered[start:]
            has_more = start + len(subset) < len(ordered)
            next_after = subset[-1].id if has_more and subset else None

            return Page[ThreadItem](
                data=[_clone(item) for item in subset],
                has_more=has_more,
                after=next_after,
            )

    async def save_attachment(
        self, attachment: Attachment, context: Dict[str, Any]
    ) -> None:
        async with self._lock:
            self._attachments[attachment.id] = _clone(attachment)

    async def load_attachment(
        self, attachment_id: str, context: Dict[str, Any]
    ) -> Attachment:
        async with self._lock:
            attachment = self._attachments.get(attachment_id)
            if not attachment:
                raise NotFoundError(f"Attachment {attachment_id} not found")
            return _clone(attachment)

    async def delete_attachment(
        self, attachment_id: str, context: Dict[str, Any]
    ) -> None:
        async with self._lock:
            if attachment_id in self._attachments:
                del self._attachments[attachment_id]
                return
            raise NotFoundError(f"Attachment {attachment_id} not found")

    async def load_threads(
        self,
        limit: int,
        after: Optional[str],
        order: str,
        context: Dict[str, Any],
    ) -> Page[ThreadMetadata]:
        async with self._lock:
            threads = list(self._threads.values())
            threads.sort(key=lambda t: t.created_at, reverse=(order != "asc"))

            start = 0
            if after:
                for idx, thread in enumerate(threads):
                    if thread.id == after:
                        start = idx + 1
                        break
                else:
                    raise NotFoundError(f"Thread {after} not found")

            subset = threads[start : start + limit] if limit else threads[start:]
            has_more = start + len(subset) < len(threads)
            next_after = subset[-1].id if has_more and subset else None

            return Page[ThreadMetadata](
                data=[_clone(thread) for thread in subset],
                has_more=has_more,
                after=next_after,
            )

    async def add_thread_item(
        self, thread_id: str, item: ThreadItem, context: Dict[str, Any]
    ) -> None:
        async with self._lock:
            if thread_id not in self._threads:
                raise NotFoundError(f"Thread {thread_id} not found")

            collection = self._items.setdefault(thread_id, deque())
            collection.append(_clone(item))

    async def save_item(
        self, thread_id: str, item: ThreadItem, context: Dict[str, Any]
    ) -> None:
        async with self._lock:
            collection = self._items.get(thread_id)
            if collection is None:
                raise NotFoundError(f"Thread {thread_id} not found")

            for idx, existing in enumerate(collection):
                if existing.id == item.id:
                    collection[idx] = _clone(item)
                    return

            raise NotFoundError(f"Item {item.id} not found in thread {thread_id}")

    async def load_item(
        self, thread_id: str, item_id: str, context: Dict[str, Any]
    ) -> ThreadItem:
        async with self._lock:
            collection = self._items.get(thread_id)
            if collection is None:
                raise NotFoundError(f"Thread {thread_id} not found")

            for item in collection:
                if item.id == item_id:
                    return _clone(item)

            raise NotFoundError(f"Item {item_id} not found in thread {thread_id}")

    async def delete_thread(
        self, thread_id: str, context: Dict[str, Any]
    ) -> None:
        async with self._lock:
            thread_removed = self._threads.pop(thread_id, None)
            items_removed = self._items.pop(thread_id, None)

            if thread_removed is None or items_removed is None:
                raise NotFoundError(f"Thread {thread_id} not found")

    async def delete_thread_item(
        self, thread_id: str, item_id: str, context: Dict[str, Any]
    ) -> None:
        async with self._lock:
            collection = self._items.get(thread_id)
            if collection is None:
                raise NotFoundError(f"Thread {thread_id} not found")

            for idx, item in enumerate(collection):
                if item.id == item_id:
                    del collection[idx]
                    return

            raise NotFoundError(f"Item {item_id} not found in thread {thread_id}")


