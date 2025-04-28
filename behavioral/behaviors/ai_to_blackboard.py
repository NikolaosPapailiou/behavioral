from typing import List, Optional

import py_trees
from langchain_core.runnables import RunnableSerializable
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from behavioral.base import AsyncBehavior
from behavioral.guards import BehaviorGuard
from behavioral.utils import PartialPromptParams, ainvoke


class AIToBlackboard(AsyncBehavior):
    def __init__(
        self,
        name: str,
        prompt: str,
        extra_chain_runnables: RunnableSerializable = None,
        tools: List[BaseTool] = None,
        capture_state_type: BaseModel = None,
        state_key: str = None,
        memory: bool = False,
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
        self.prompt = prompt
        self.extra_chain_runnables = extra_chain_runnables
        self.tools = tools
        self.capture_state_type = capture_state_type
        self.state_key = state_key
        if self.state_key is None:
            self.state_key = self.name
        self.memory = memory
        self.formatted_prompt = None
        self.captured_state = None
        self.last_captured_message = 0

    def initialise(self):
        super().initialise()
        if not self.memory:
            self.captured_state = None
            self.conversation_tree.bb.remove_key(
                key=self.name,
                namespace=self.namespace,
            )

    def update(self) -> py_trees.common.Status:
        self.feedback_message = ""
        if self.task is not None:
            return super().update()
        if self.captured_state is not None:
            return py_trees.common.Status.SUCCESS
        return super().update()

    async def async_update(self) -> py_trees.common.Status:
        await self._capture_state()
        return py_trees.common.Status.SUCCESS

    async def _capture_state(self):
        self.captured_state = await ainvoke(
            chat_model=self.conversation_tree.chat_model,
            tools=self.tools,
            extra_chain_runnables=self.extra_chain_runnables,
            conversation_goal_prompt=self.conversation_tree.conversation_goal_prompt,
            prompt=self.format_prompt(prompt=self.prompt),
            chat_history=self.conversation_tree.get_active_chat_history(),
            structured_output=self.capture_state_type,
        )
        print(f"State:{self.name} -> {self.captured_state}")
        self.conversation_tree.bb.set_value(
            key=self.state_key,
            value=self.captured_state,
            namespace=self.namespace,
        )
        self.last_captured_message = len(self.conversation_tree.chat_history)
