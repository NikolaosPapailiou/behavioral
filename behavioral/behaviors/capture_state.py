from typing import List, Optional

import py_trees
from langchain_core.runnables import RunnableSerializable
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from behavioral.base import AsyncBehavior
from behavioral.guards import BehaviorGuard
from behavioral.utils import PartialPromptParams, capture_conversation_state


class CaptureConversationState(AsyncBehavior):
    def __init__(
        self,
        name: str,
        capture_state_type: type = BaseModel,
        extra_chain_runnables: RunnableSerializable = None,
        tools: List[BaseTool] = None,
        state_key: str = "conversation_state",
        capture_assistant_message: bool = False,
        guard: Optional[BehaviorGuard] = None,
        prompt_params: PartialPromptParams = PartialPromptParams(),
        retry_errors: int = 3,
    ):
        super().__init__(
            name=name,
            guard=guard,
            prompt_params=prompt_params,
            retry_errors=retry_errors,
        )
        self.capture_state_type = capture_state_type
        self.capture_assistant_message = capture_assistant_message
        self.extra_chain_runnables = extra_chain_runnables
        self.tools = tools
        self.state_key = state_key
        self.last_captured_message = 0
        self.captured_state = None

    def update(self) -> py_trees.common.Status:
        self.feedback_message = ""
        if self.task is not None:
            self.logger.debug("Already Capturing state")
            status = super().update()
            if status == py_trees.common.Status.RUNNING:
                self.logger.debug("State cpture not finished yet.")
                self.conversation_tree.capture_state_running = True
            super().initialise()
            return py_trees.common.Status.SUCCESS

        # Already captured all messages
        if (
            len(self.conversation_tree.chat_history) <= self.last_captured_message
            and len(self.conversation_tree.chat_history) > 0
        ):
            self.logger.debug(
                f"Already captured all messages {len(self.conversation_tree.chat_history)} <= {self.last_captured_message}"
            )
            return py_trees.common.Status.SUCCESS
        has_not_captured_user_message = any(
            m.role == "user"
            for m in self.conversation_tree.chat_history[self.last_captured_message :]
        )
        has_not_captured_assistant_message = any(
            m.role == "assistant" and m.metadata["completed"]
            for m in self.conversation_tree.chat_history[self.last_captured_message :]
        )
        self.logger.debug(
            f"has_not_captured_user_message: {has_not_captured_user_message}, has_not_captured_assistant_message: {has_not_captured_assistant_message}, capture_assistant_message: {self.capture_assistant_message}"
        )
        if (
            len(self.conversation_tree.chat_history) == 0
            or has_not_captured_user_message
            or (has_not_captured_assistant_message and self.capture_assistant_message)
        ):
            self.logger.debug("Capturing state")
            self.conversation_tree.capture_state_running = True
            return super().update()
        return py_trees.common.Status.SUCCESS

    async def capture_state(self) -> py_trees.common.Status:
        try:
            self.captured_state = await capture_conversation_state(
                chat_model=self.conversation_tree.chat_model,
                extra_chain_runnables=self.extra_chain_runnables,
                tools=self.tools,
                chat_history=self.conversation_tree.get_active_chat_history(),
                non_captured_messages=len(self.conversation_tree.chat_history)
                - self.last_captured_message,
                previous_state=self.captured_state,
                state_type=self.capture_state_type,
            )
            self.conversation_tree.bb.set_value(
                key=self.state_key,
                value=self.captured_state,
                namespace=self.namespace,
            )
            self.last_captured_message = len(self.conversation_tree.chat_history)
        except Exception as e:
            self.feedback_message = f"Error: {e}"
            self.logger.error(f"Error while capturing state: {e}")
        return py_trees.common.Status.SUCCESS

    async def async_update(self) -> py_trees.common.Status:
        status = await self.capture_state()
        return status
