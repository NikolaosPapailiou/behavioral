from typing import Any, Iterator, List, Optional

import py_trees

from behavioral.conversation import ConversationBehaviourTree
from behavioral.guards import BehaviorGuard


class Sequence(py_trees.composites.Sequence):
    def __init__(
        self,
        name,
        memory: bool = True,
        children: Optional[List[py_trees.behaviour.Behaviour]] = None,
        guard: Optional[BehaviorGuard] = None,
    ):
        super().__init__(
            name=name,
            memory=memory,
            children=children,
        )
        self.guard = guard

    def setup(
        self,
        namespace: str = None,
        conversation_tree: ConversationBehaviourTree = None,
        **kwargs: Any,
    ) -> None:
        super().setup(**kwargs)
        self.namespace = namespace
        self.conversation_tree = conversation_tree

    def tick(self) -> Iterator[py_trees.behaviour.Behaviour]:
        self.logger.debug("Sequence.tick()")
        if self.guard is not None:
            guard_enter_status = self.guard.check_enter(self)
            if guard_enter_status is not None:
                self.status = guard_enter_status
                self.current_child = self.children[0] if self.children else None
                yield self
                return

        for node in super().tick():
            if node is not self:
                yield node

        if self.status == py_trees.common.Status.RUNNING:
            yield self

        # Check exit guard
        if self.guard is None:
            yield self
            return
        guard_exit_status = self.guard.check_exit(self)
        if guard_exit_status is None:
            yield self
            return

        # Restart if exit guard is running
        if guard_exit_status == py_trees.common.Status.RUNNING:
            for node in self.tick():
                yield node
            return
        self.status = guard_exit_status
        yield self


class Selector(py_trees.composites.Selector):
    def __init__(
        self,
        name,
        memory: bool = True,
        children: Optional[List[py_trees.behaviour.Behaviour]] = None,
        guard: Optional[BehaviorGuard] = None,
    ):
        super().__init__(
            name=name,
            memory=memory,
            children=children,
        )
        self.guard = guard

    def setup(
        self,
        namespace: str = None,
        conversation_tree: ConversationBehaviourTree = None,
        **kwargs: Any,
    ) -> None:
        super().setup(**kwargs)
        self.namespace = namespace
        self.conversation_tree = conversation_tree

    def tick(self) -> Iterator[py_trees.behaviour.Behaviour]:
        self.logger.debug("Selector.tick()")
        if self.guard is not None:
            guard_enter_status = self.guard.check_enter(self)
            if guard_enter_status is not None:
                self.status = guard_enter_status
                self.current_child = self.children[0] if self.children else None
                yield self
                return

        for node in super().tick():
            if node is not self:
                yield node

        # Check exit guard
        if self.guard is None:
            yield self
            return
        guard_exit_status = self.guard.check_exit(self)
        if guard_exit_status is None:
            yield self
            return

        # Restart if exit guard is running
        if guard_exit_status == py_trees.common.Status.RUNNING:
            for node in self.tick():
                yield node
            return
        self.status = guard_exit_status
        yield self


class Parallel(py_trees.composites.Parallel):
    def __init__(
        self,
        name,
        policy: py_trees.common.ParallelPolicy.Base,
        children: Optional[List[py_trees.behaviour.Behaviour]] = None,
        guard: Optional[BehaviorGuard] = None,
    ):
        super().__init__(
            name=name,
            policy=policy,
            children=children,
        )
        self.guard = guard

    def setup(
        self,
        namespace: str = None,
        conversation_tree: ConversationBehaviourTree = None,
        **kwargs: Any,
    ) -> None:
        super().setup(**kwargs)
        self.namespace = namespace
        self.conversation_tree = conversation_tree

    def tick(self) -> Iterator[py_trees.behaviour.Behaviour]:
        self.logger.debug("Parallel.tick()")
        if self.guard is not None:
            guard_enter_status = self.guard.check_enter(self)
            if guard_enter_status is not None:
                self.status = guard_enter_status
                self.current_child = self.children[0] if self.children else None
                yield self
                return

        for node in super().tick():
            if node is not self:
                yield node

        # Check exit guard
        if self.guard is None:
            yield self
            return
        guard_exit_status = self.guard.check_exit(self)
        if guard_exit_status is None:
            yield self
            return

        # Restart if exit guard is running
        if guard_exit_status == py_trees.common.Status.RUNNING:
            for node in self.tick():
                yield node
            return
        self.status = guard_exit_status
        yield self
