from abc import ABC, abstractmethod
from concurrent.futures import Future
from typing import Any, Iterator, Optional

import py_trees

from behavioral.conversation import ConversationBehaviourTree
from behavioral.guards import BehaviorGuard
from behavioral.utils import PartialPromptParams


class Behavior(py_trees.behaviour.Behaviour, ABC):
    """A base class for all behaviors."""

    def __init__(
        self,
        name: str,
        guard: Optional[BehaviorGuard] = None,
        prompt_params: PartialPromptParams = PartialPromptParams(),
    ):
        super().__init__(name)
        self.guard = guard
        self.prompt_params = prompt_params

    def setup(
        self,
        namespace: str = None,
        conversation_tree: ConversationBehaviourTree = None,
        **kwargs: Any,
    ) -> None:
        super().setup(**kwargs)
        self.namespace = namespace
        self.conversation_tree = conversation_tree

    def tick(self) -> Iterator[py_trees.behaviour.Behaviour]:
        self.logger.debug("Behavior.tick()")
        if self.guard is not None:
            guard_enter_status = self.guard.check_enter(self)
            if guard_enter_status is not None:
                self.feedback_message = f"guard enter status: {guard_enter_status}"
                self.status = guard_enter_status
                self.current_child = self.children[0] if self.children else None
                yield self
                return

        for node in super().tick():
            if node is not self:
                yield node

        if self.status == py_trees.common.Status.RUNNING:
            yield self

        # Check exit guard
        if self.guard is None:
            yield self
            return
        guard_exit_status = self.guard.check_exit(self)
        if guard_exit_status is None:
            yield self
            return

        self.feedback_message = f"guard exit status: {guard_exit_status}"
        # Restart if exit guard is running
        if guard_exit_status == py_trees.common.Status.RUNNING:
            for node in self.tick():
                yield node
            return
        self.status = guard_exit_status
        yield self

    def format_prompt(self, prompt: str) -> str:
        # Add global bb
        bb_params = PartialPromptParams(self.conversation_tree.bb.to_dict())
        # Add local bb
        bb_params.update(self.conversation_tree.bb.to_dict(self.namespace))
        # Add Behavior params
        bb_params.update(self.prompt_params)
        return bb_params.format_with_eval(prompt)


class AsyncBehavior(Behavior, ABC):
    """A behavior that executes an async function in the background.

    This behavior starts an async function in the background and returns RUNNING
    until the function completes. Once completed, it returns SUCCESS or FAILURE
    based on the result of the async function.
    """

    def __init__(
        self,
        name: str,
        guard: Optional[BehaviorGuard] = None,
        prompt_params: PartialPromptParams = PartialPromptParams(),
        retry_errors: int = 3,
    ):
        """Initialize the async behavior.

        Args:
            name: The name of the behavior
            retry_errors: The number of times to retry the behavior if it fails. Use -1 for infinite retries.
        """
        super().__init__(
            name=name,
            guard=guard,
            prompt_params=prompt_params,
        )
        self.retry_errors = retry_errors
        self.num_errors = 0
        self.task: Optional[Future] = None

    def initialise(self) -> None:
        self.feedback_message = ""
        self.num_errors = 0
        self.task = None

    def update(self) -> py_trees.common.Status:
        """Update the behavior status based on the async task state."""
        if self.task is None:
            try:
                self.task = self.conversation_tree.loop.create_task(self.async_update())
                self.task.add_done_callback(self.callback)
                return py_trees.common.Status.RUNNING
            except Exception as e:
                self.logger.error(f"Error creating async task: {e}")
                self.feedback_message = f"Error creating async task: {e}"
                return py_trees.common.Status.RUNNING

        if self.task.done():
            self.logger.debug(f"Async task completed: {self.name}")
            try:
                return self.task.result()
            except Exception as e:
                self.num_errors += 1
                self.logger.error(f"Async task failed: {e}")
                self.feedback_message = f"Async task failed: {e}"
                if self._should_retry():
                    self.task = None
                    return self.update()
                return py_trees.common.Status.FAILURE
        return py_trees.common.Status.RUNNING

    def callback(self, fut):
        self.logger.debug(f"Async Callback for behavior: {self.name}")
        self.conversation_tree.wakeup()

    def terminate(self, new_status: py_trees.common.Status) -> None:
        """Cancel the async task when the behavior is interrupted."""
        if self.task is not None and not self.task.done():
            self.logger.debug(f"Cancelling async task {self.name}")
            self.task.cancel()
            self.task = None

    @abstractmethod
    async def async_update(self) -> py_trees.common.Status:
        """The async function that the behavior will execute."""
        pass

    def _should_retry(self):
        if self.retry_errors < 0:
            return True
        if self.num_errors < self.retry_errors:
            return True
        return False
