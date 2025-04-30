import operator

import py_trees

from behavioral.base import Behavior


class CheckBlackboardVariableValue(Behavior):
    """
    Non-blocking check to determine if a blackboard variable matches a given value/expression.

    Inspect a blackboard variable and if it exists, check that it
    meets the specified criteria (given by operation type and expected value).
    This is non-blocking, so it will always tick with
    :data:`~py_trees.common.Status.SUCCESS` or
    :data:`~py_trees.common.Status.FAILURE`.

    Args:
        name: name of the behaviour
        check: a comparison expression to check against

    .. note::
        If the variable does not yet exist on the blackboard, the behaviour will
        return with status :data:`~py_trees.common.Status.FAILURE`.

    .. tip::
        The python `operator module`_ includes many useful comparison operations.
    """

    def __init__(self, name: str, check: py_trees.common.ComparisonExpression):
        super().__init__(name=name)
        self.check = check
        name_components = self.check.variable.split(".")
        self.key = name_components[0]
        self.key_attributes = ".".join(
            name_components[1:]
        )  # empty string if no other parts

    def update(self) -> py_trees.common.Status:
        """
        Check for existence, or the appropriate match on the expected value.

        Returns:
             :class:`~py_trees.common.Status`: :data:`~py_trees.common.Status.FAILURE`
                 if not matched, :data:`~py_trees.common.Status.SUCCESS` otherwise.
        """
        self.logger.debug("%s.update()" % self.__class__.__name__)
        try:
            value = self.conversation_tree.bb.get_value(
                key=self.key, namespace=self.namespace
            )
            if self.key_attributes:
                try:
                    value = operator.attrgetter(self.key_attributes)(value)
                except AttributeError:
                    self.feedback_message = (
                        "blackboard key-value pair exists, but the value does not "
                        f"have the requested nested attributes [{self.key}]"
                    )
                    return py_trees.common.Status.FAILURE
        except KeyError:
            self.feedback_message = (
                "key '{}' does not yet exist on the blackboard".format(
                    self.check.variable
                )
            )
            return py_trees.common.Status.FAILURE

        success = self.check.operator(value, self.check.value)

        if success:
            self.feedback_message = "'%s' comparison succeeded [v: %s][e: %s]" % (
                self.check.variable,
                value,
                self.check.value,
            )
            return py_trees.common.Status.SUCCESS
        else:
            self.feedback_message = "'%s' comparison failed [v: %s][e: %s]" % (
                self.check.variable,
                value,
                self.check.value,
            )
            return py_trees.common.Status.FAILURE


class RespondToUserFromBlackboard(Behavior):
    def __init__(self, name: str, bb_variable: str):
        super().__init__(name=name)
        self.bb_variable = bb_variable
        name_components = self.bb_variable.split(".")
        self.key = name_components[0]
        self.key_attributes = ".".join(
            name_components[1:]
        )  # empty string if no other parts

    def update(self) -> py_trees.common.Status:
        self.logger.debug("%s.update()" % self.__class__.__name__)
        self.feedback_message = ""
        if self.conversation_tree.capture_state_running:
            self.logger.debug("Not sending message during state capture.")
            return py_trees.common.Status.RUNNING
        try:
            value = self.conversation_tree.bb.get_value(
                key=self.key, namespace=self.namespace
            )
            if self.key_attributes:
                try:
                    value = operator.attrgetter(self.key_attributes)(value)
                except AttributeError:
                    self.feedback_message = (
                        "blackboard key-value pair exists, but the value does not "
                        f"have the requested nested attributes [{self.key}]"
                    )
                    return py_trees.common.Status.FAILURE
        except KeyError:
            self.feedback_message = (
                "key '{}' does not yet exist on the blackboard".format(
                    self.check.variable
                )
            )
            return py_trees.common.Status.FAILURE

        message = self.conversation_tree.add_assistant_message()
        message.content = value
        return py_trees.common.Status.SUCCESS


class RemoveBlackboardVariable(Behavior):
    def __init__(self, name: str, key: str):
        super().__init__(name=name)
        self.key = key

    def update(self) -> py_trees.common.Status:
        """
        Unset and always return success.

        Returns:
             :data:`~py_trees.common.Status.SUCCESS`
        """
        if self.conversation_tree.bb.remove_key(self.key, self.namespace):
            self.feedback_message = "'{}' found and removed".format(self.key)
        else:
            self.feedback_message = "'{}' not found, nothing to remove"
        return py_trees.common.Status.SUCCESS


class IncrementBlackboardVariable(Behavior):
    def __init__(self, name: str, bb_variable: str):
        super().__init__(name=name)
        self.bb_variable = bb_variable
        name_components = self.bb_variable.split(".")
        self.key = name_components[0]
        self.key_attributes = ".".join(
            name_components[1:]
        )  # empty string if no other parts

    def update(self) -> py_trees.common.Status:
        """
        Unset and always return success.

        Returns:
             :data:`~py_trees.common.Status.SUCCESS`
        """
        value = self.conversation_tree.bb.get_value(self.key, self.namespace)
        if self.key_attributes == "":
            if value is None:
                value = 0
            value += 1
        else:
            if value is None:
                self.feedback_message = (
                    "key '{}' does not yet exist on the blackboard".format(self.key)
                )
                return py_trees.common.Status.FAILURE
            try:
                operator.iadd(operator.attrgetter(self.key_attributes)(value), 1)
            except AttributeError:
                self.feedback_message = (
                    "blackboard key-value pair exists, but the value does not "
                    f"have the requested nested attributes [{self.key}]"
                )
                return py_trees.common.Status.FAILURE
        self.conversation_tree.bb.set_value(self.key, value, self.namespace)
        self.feedback_message = f"[{value}]"
        return py_trees.common.Status.SUCCESS
