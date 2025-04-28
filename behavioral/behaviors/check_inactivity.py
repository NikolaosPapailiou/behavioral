import time

import py_trees

from behavioral.base import Behavior


class CheckUserIsActive(Behavior):
    def __init__(self, time_since_last_message: float):
        super().__init__(name="IsUserActive")
        self.time_since_last_message = time_since_last_message

    def update(self) -> py_trees.common.Status:
        self.feedback_message = ""
        if len(self.conversation_tree.chat_history) == 0:
            return py_trees.common.Status.SUCCESS
        current_time = time.time()
        self.feedback_message = "Time since last user message: {current_time - self.conversation_tree.last_message_time}s"
        if (
            current_time - self.conversation_tree.last_message_time
            > self.time_since_last_message
        ):
            self.logger.debug(
                f"User is inactive. Time since last message: {current_time - self.conversation_tree.last_message_time}s"
            )
            return py_trees.common.Status.FAILURE
        self.logger.debug(
            f"User is active. Time since last message: {current_time - self.conversation_tree.last_message_time}s"
        )
        return py_trees.common.Status.SUCCESS


class CheckNoPendingUserMessage(Behavior):
    def __init__(self):
        super().__init__(name="HasPendingUserMessage")

    def update(self) -> py_trees.common.Status:
        if not self.conversation_tree.has_pending_user_message():
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE


class CheckHasPendingUserMessage(Behavior):
    def __init__(self):
        super().__init__(name="HasPendingUserMessage")

    def update(self) -> py_trees.common.Status:
        if self.conversation_tree.has_pending_user_message():
            return py_trees.common.Status.SUCCESS
        return py_trees.common.Status.FAILURE
