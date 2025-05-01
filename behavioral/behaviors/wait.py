import asyncio
from typing import Optional

import py_trees

from behavioral.base import AsyncBehavior
from behavioral.guards import BehaviorGuard


class Wait(AsyncBehavior):
    def __init__(
        self,
        delay: float,
        guard: Optional[BehaviorGuard] = None,
        retry_errors: int = 3,
    ):
        super().__init__(
            name=f"wait({delay}s)",
            guard=guard,
            retry_errors=retry_errors,
        )
        self.delay = delay

    async def async_update(self) -> py_trees.common.Status:
        await asyncio.sleep(delay=self.delay)
        return py_trees.common.Status.SUCCESS
