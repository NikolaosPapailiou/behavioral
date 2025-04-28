import time
from typing import List, Optional

import py_trees
from langchain_core.runnables import RunnableSerializable
from langchain_core.tools import BaseTool

from behavioral.base import AsyncBehavior
from behavioral.guards import BehaviorGuard
from behavioral.utils import PartialPromptParams, respond_to_user


class ConversationMessage(AsyncBehavior):
    def __init__(
        self,
        name: str,
        message_prompt: str,
        prompt_params: PartialPromptParams = PartialPromptParams(),
        extra_chain_runnables: RunnableSerializable = None,
        tools: List[BaseTool] = None,
        guard: Optional[BehaviorGuard] = None,
        retry_errors: int = 3,
        respond_without_user_message: bool = False,
        max_messages_sent: int = -1,
        seconds_since_last_message: float = 0.0,
    ):
        super().__init__(
            name=name,
            guard=guard,
            prompt_params=prompt_params,
            retry_errors=retry_errors,
        )
        self.message_prompt = message_prompt
        self.extra_chain_runnables = extra_chain_runnables
        self.tools = tools
        self.respond_without_user_message = respond_without_user_message
        self.formatted_message_prompt = None
        self.messages_sent = 0
        self.max_messages_sent = max_messages_sent
        self.seconds_since_last_message = seconds_since_last_message
        self.next_message_time = None

    def initialise(self):
        super().initialise()

    def update(self) -> py_trees.common.Status:
        self.feedback_message = ""
        if self.task is not None:
            return super().update()
        if self.conversation_tree.capture_state_running:
            self.logger.debug("No message during capture")
            return py_trees.common.Status.RUNNING
        if (
            self.max_messages_sent != -1
            and self.messages_sent >= self.max_messages_sent
        ):
            self.logger.debug("Max messages sent reached")
            self.feedback_message = "Max messages sent reached"
            return py_trees.common.Status.SUCCESS
        if (
            not self.conversation_tree.has_pending_user_message()
            and not self.respond_without_user_message
        ):
            self.logger.debug("No pending user message")
            self.feedback_message = "No pending user message"
            return py_trees.common.Status.FAILURE

        current_time = time.time()
        if (
            self.next_message_time and current_time < self.next_message_time
            # and not self.conversation_tree.has_pending_user_message()
        ):
            self.logger.debug("Next message time not reached")
            self.feedback_message = "Next message time not reached"
            return py_trees.common.Status.FAILURE
        self.logger.debug("Sending message")
        return super().update()

    async def async_update(self) -> py_trees.common.Status:
        self.logger.debug("async_update()")
        await respond_to_user(
            chat_model=self.conversation_tree.chat_model,
            extra_chain_runnables=self.extra_chain_runnables,
            tools=self.tools,
            response_message=self.conversation_tree.add_assistant_message(),
            conversation_goal_prompt=self.conversation_tree.conversation_goal_prompt,
            current_goal_prompt=self.format_prompt(prompt=self.message_prompt),
            chat_history=self.conversation_tree.get_active_chat_history(),
        )
        self.messages_sent += 1
        self.next_message_time = time.time() + self.seconds_since_last_message
        return py_trees.common.Status.SUCCESS

    def terminate(self, new_status: py_trees.common.Status) -> None:
        return super().terminate(new_status)
