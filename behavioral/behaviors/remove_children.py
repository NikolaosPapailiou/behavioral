import py_trees

from behavioral.base import Behavior


class RemoveChildren(Behavior):
    def __init__(
        self,
        name: str,
        remove_target: py_trees.composites.Composite,
        reset_conversation_state_key: str = None,
    ):
        super().__init__(name)
        self.remove_target = remove_target
        self.reset_conversation_state_key = reset_conversation_state_key

    def update(self) -> py_trees.common.Status:
        self.feedback_message = ""
        try:
            self.logger.debug("Removing activity tree")
            remove_all_children = getattr(
                self.remove_target, "remove_all_children", None
            )
            if callable(remove_all_children):
                remove_all_children()
            else:
                self.logger.error(
                    f"node does not have 'remove_all_children' [{type(self.remove_target)}]"
                )
                self.feedback = f"node does not have 'remove_all_children' [{type(self.remove_target)}]"
                return py_trees.common.Status.FAILURE
            if self.reset_conversation_state_key is not None:
                self.conversation_tree.bb.remove_key(
                    key=self.reset_conversation_state_key, namespace=self.namespace
                )
            return py_trees.common.Status.SUCCESS
        except Exception as e:
            self.logger.error(f"Error: {e}")
            self.feedback = f"Error: {e}"
