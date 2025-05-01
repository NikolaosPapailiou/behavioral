from typing import Optional

import py_trees

from behavioral.base import Behavior
from behavioral.guards import BehaviorGuard
from behavioral.utils import PartialPromptParams


class RespondToUser(Behavior):
    def __init__(
        self,
        name: str,
        message: str,
        guard: Optional[BehaviorGuard] = None,
        prompt_params: PartialPromptParams = PartialPromptParams(),
    ):
        super().__init__(
            name=name,
            guard=guard,
            prompt_params=prompt_params,
        )
        self.message = message

    def update(self) -> py_trees.common.Status:
        message = self.conversation_tree.add_assistant_message()
        message.content = self.format_prompt(prompt=self.message)
        return py_trees.common.Status.SUCCESS
