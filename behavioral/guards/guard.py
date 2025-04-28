from typing import Any, Callable, Dict, Optional, Union

import py_trees

from behavioral.conversation import ConversationBehaviourTree


class Guard:
    def __init__(
        self,
        success_check: Optional[Callable] = None,
        success_check_kwargs: Dict = {},
        failure_check: Optional[Callable] = None,
        failure_check_kwargs: Dict = {},
        running_check: Optional[Callable] = None,
        running_check_kwargs: Dict = {},
    ):
        self.success_check = success_check
        self.success_check_kwargs = success_check_kwargs
        self.failure_check = failure_check
        self.failure_check_kwargs = failure_check_kwargs
        self.running_check = running_check
        self.running_check_kwargs = running_check_kwargs
        self.logger = py_trees.logging.Logger(self.__class__.__name__)

    def setup(
        self,
        namespace: str = None,
        conversation_tree: ConversationBehaviourTree = None,
        **kwargs: Any,
    ) -> None:
        self.namespace = namespace
        self.conversation_tree = conversation_tree

    def check_all(self) -> Union[py_trees.common.Status, None]:
        if self.success_check is not None:
            success = self.success_check(self, **self.success_check_kwargs)
            self.logger.debug(f"Success check: {success}")
            if success:
                return py_trees.common.Status.SUCCESS
        if self.failure_check is not None:
            failure = self.failure_check(self, **self.failure_check_kwargs)
            self.logger.debug(f"Failure check: {failure}")
            if failure:
                return py_trees.common.Status.FAILURE
        if self.running_check is not None:
            running = self.running_check(self, **self.running_check_kwargs)
            self.logger.debug(f"Running check: {running}")
            if running:
                return py_trees.common.Status.RUNNING
        return None


class BehaviorGuard:
    def __init__(
        self,
        guard_on_tick_enter: Optional[Guard] = None,
        guard_on_tick_exit: Optional[Guard] = None,
    ):
        self.guard_on_tick_enter = guard_on_tick_enter
        self.guard_on_tick_exit = guard_on_tick_exit
        self.logger = py_trees.logging.Logger(self.__class__.__name__)

    def check_enter(self) -> Union[py_trees.common.Status, None]:
        if self.guard_on_tick_enter is None:
            return None
        self.logger.debug("guard_on_tick_enter.check_all")
        return self.guard_on_tick_enter.check_all()

    def check_exit(self) -> Union[py_trees.common.Status, None]:
        if self.guard_on_tick_exit is None:
            return None
        self.logger.debug("guard_on_tick_exit.check_all")
        return self.guard_on_tick_exit.check_all()
