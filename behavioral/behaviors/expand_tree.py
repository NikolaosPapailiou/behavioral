import random
from typing import Callable, Optional

import py_trees

from behavioral.base import Behavior
from behavioral.guards import BehaviorGuard
from behavioral.utils import PartialPromptParams


class ExpandTree(Behavior):
    def __init__(
        self,
        name: str,
        expand_on_state_variable: str,
        expand_target: py_trees.composites.Composite,
        guard: Optional[BehaviorGuard] = None,
        prompt_params: PartialPromptParams = PartialPromptParams(),
        expand_prompt_param_key: str = "item",
        behavior_item_name_variable: str = None,
        behavior_constructor: Callable = None,
        pick_behavior_constructor: dict[str, Callable] = None,
    ):
        super().__init__(
            name=name,
            guard=guard,
            prompt_params=prompt_params,
        )
        self.expand_on_state_variable = expand_on_state_variable
        name_components = self.expand_on_state_variable.split(".")
        self.expand_on_state_key = name_components[0]
        self.expand_on_state_attribute = ".".join(
            name_components[1:]
        )  # empty string if no other parts
        self.expand_target = expand_target
        self.expand_prompt_param_key = expand_prompt_param_key
        self.behavior_item_name_variable = behavior_item_name_variable
        self.behavior_constructor = behavior_constructor
        self.pick_behavior_constructor = pick_behavior_constructor

    def has_expanded(self) -> bool:
        if len(self.expand_target.children) > 0:
            return True
        return False

    def update(self) -> py_trees.common.Status:
        self.feedback_message = ""
        if not self.has_expanded():
            return self.expand()
        return py_trees.common.Status.SUCCESS

    def expand(self):
        try:
            self.logger.debug("Expanding")
            items = self.conversation_tree.bb.get_value(
                key=self.expand_on_state_key, namespace=self.namespace
            )
            if self.expand_on_state_attribute:
                items = getattr(items, self.expand_on_state_attribute)
            if isinstance(items, str):
                items = [items]
            for item in items:
                behavior_constructor = self.behavior_constructor
                if self.pick_behavior_constructor:
                    behavior_constructor = self.pick_behavior_constructor[item]
                if behavior_constructor is None:
                    raise ValueError(f"No behavior constructor found for {item}")
                prompt_params = PartialPromptParams()
                prompt_params.update(
                    {
                        self.expand_prompt_param_key: item,
                    }
                )
                prompt_params.update(self.prompt_params)
                new_namespace = "" if self.namespace is None else self.namespace
                item_name = item
                if self.behavior_item_name_variable is not None:
                    item_name = getattr(item, self.behavior_item_name_variable)

                new_namespace += (
                    "/"
                    + self.name
                    + "("
                    + item_name
                    + ")["
                    + str(random.randint(0, 1000000))
                    + "]"
                )
                behavior = behavior_constructor(
                    chat_model=self.conversation_tree.chat_model,
                    prompt_params=prompt_params,
                    namespace=new_namespace,
                )
                py_trees.trees.setup(
                    behavior,
                    namespace=new_namespace,
                    conversation_tree=self.conversation_tree,
                )
                self.expand_target.add_child(behavior)

            return py_trees.common.Status.SUCCESS
        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.feedback_message = f"Error: {e}"
            return py_trees.common.Status.FAILURE
