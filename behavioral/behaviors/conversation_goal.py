import time
from typing import List, Optional

import py_trees
from langchain_core.runnables import RunnableSerializable
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from behavioral.base import AsyncBehavior
from behavioral.guards import BehaviorGuard
from behavioral.utils import (PartialPromptParams, capture_goal_state,
                              respond_to_user)


class ConversationGoalState(BaseModel):
    """
    State of a conversation goal.
    """

    goal_achieved: bool = Field(
        title="Goal Achieved",
        description="True, if the goal has been achieved in the conversation.",
    )
    goal_progress: float = Field(
        title="Goal Progress",
        description="Progress of the goal in the conversation. 0.0 is not started, 1.0 is completed.",
    )


class ConversationGoalStateWithFailure(ConversationGoalState):
    """
    State of a conversation goal with failure.
    """

    goal_failed: bool = Field(
        title="Goal Failed",
        description="True, if the goal has failed or not possible to achieve in the conversation.",
    )


class ConversationGoal(AsyncBehavior):
    def __init__(
        self,
        name: str,
        goal_prompt: str,
        guard: Optional[BehaviorGuard] = None,
        prompt_params: PartialPromptParams = PartialPromptParams(),
        retry_errors: int = 3,
        extra_chain_runnables: RunnableSerializable = None,
        tools: List[BaseTool] = None,
        capture_state_type: type = ConversationGoalState,
        respond_without_user_message: bool = False,
        max_messages_sent: int = -1,
        seconds_since_last_message: float = 60,
        memory: bool = True,
        initialize_after_user_messages: int = 2,
    ):
        super().__init__(
            name=name,
            guard=guard,
            prompt_params=prompt_params,
            retry_errors=retry_errors,
        )
        self.goal_prompt = goal_prompt
        self.extra_chain_runnables = extra_chain_runnables
        self.tools = tools
        self.capture_state_type = capture_state_type
        self.respond_without_user_message = respond_without_user_message
        self.messages_sent = 0
        self.max_messages_sent = max_messages_sent
        self.seconds_since_last_message = seconds_since_last_message
        self.next_message_time = None
        self.captured_state = None
        self.memory = memory
        self.initialize_after_user_messages = initialize_after_user_messages
        self.last_captured_message = 0

    def goal_achieved(self) -> bool:
        if self.captured_state is None:
            return False
        return self.captured_state.goal_achieved

    def goal_failed(self) -> bool:
        if (
            self.max_messages_sent != -1
            and self.messages_sent >= self.max_messages_sent
        ):
            self.feedback_message = "max messages sent"
            self.logger.debug("Goal failed because max messages sent")
            return True
        if self.captured_state is None:
            return False
        if not hasattr(self.captured_state, "goal_failed"):
            return False
        return self.captured_state.goal_failed

    def initialise(self) -> None:
        user_mesages_since_last_capture = sum(
            m.role == "user"
            for m in self.conversation_tree.chat_history[self.last_captured_message :]
        )
        if (
            not self.memory
            and user_mesages_since_last_capture >= self.initialize_after_user_messages
        ):
            self.messages_sent = 0
            self.next_message_time = None
            self.captured_state = None
            # self.bb.captured_states[self.name]=None
            self.conversation_tree.bb.remove_key(
                key=self.name, namespace=self.namespace
            )
        else:
            self.captured_state = self.conversation_tree.bb.get_value(
                key=self.name, namespace=self.namespace
            )
        return super().initialise()

    def update(self) -> py_trees.common.Status:
        self.feedback_message = ""
        if self.task is not None:
            return super().update()
        if self.conversation_tree.capture_state_running:
            self.logger.debug("No message during capture")
            return py_trees.common.Status.RUNNING
        if self.goal_achieved():
            return py_trees.common.Status.SUCCESS
        if self.goal_failed():
            return py_trees.common.Status.FAILURE
        current_time = time.time()
        if (
            not self.conversation_tree.has_pending_user_message()
            and not self.respond_without_user_message
        ):
            return py_trees.common.Status.RUNNING
        if (
            self.next_message_time
            and current_time < self.next_message_time
            and not self.conversation_tree.has_pending_user_message()
        ):
            return py_trees.common.Status.RUNNING

        return super().update()

    async def async_update(self) -> py_trees.common.Status:
        if self.messages_sent > 0:
            await self._capture_state()
        if self.goal_achieved():
            return py_trees.common.Status.SUCCESS
        if self.goal_failed():
            return py_trees.common.Status.FAILURE
        # Initialize to send more responses
        await self._respond_to_user()
        super().initialise()
        return py_trees.common.Status.RUNNING

    async def _respond_to_user(self):
        try:
            await respond_to_user(
                chat_model=self.conversation_tree.chat_model,
                extra_chain_runnables=self.extra_chain_runnables,
                tools=self.tools,
                response_message=self.conversation_tree.add_assistant_message(),
                conversation_goal_prompt=self.conversation_tree.conversation_goal_prompt,
                current_goal_prompt=self.format_prompt(prompt=self.goal_prompt),
                chat_history=self.conversation_tree.get_active_chat_history(),
            )
            self.messages_sent += 1
            self.next_message_time = time.time() + self.seconds_since_last_message
        except Exception as e:
            self.feedback_message = f"Error {e}"
            self.logger.error(f"Error responding to user: {e}")

    async def _capture_state(self):
        try:
            self.captured_state = await capture_goal_state(
                chat_model=self.conversation_tree.chat_model,
                extra_chain_runnables=self.extra_chain_runnables,
                tools=self.tools,
                goal_prompt=self.format_prompt(prompt=self.goal_prompt),
                chat_history=self.conversation_tree.get_active_chat_history(),
                non_captured_messages=len(self.conversation_tree.chat_history)
                - self.last_captured_message,
                previous_state=self.captured_state,
                state_type=self.capture_state_type,
            )
            self.last_captured_message = len(self.conversation_tree.chat_history)
            self.conversation_tree.bb.set_value(
                key=self.name,
                value=self.captured_state,
                namespace=self.namespace,
            )
        except Exception as e:
            self.feedback_message = f"Error: {e}"
            self.logger.error(f"Error capturing state: {e}")

    def terminate(self, new_status: py_trees.common.Status) -> None:
        return super().terminate(new_status)
