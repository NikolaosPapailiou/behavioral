import typing

import py_trees


class Retry(py_trees.decorators.Decorator):
    """
    Keep trying, pastafarianism is within reach.

    :data:`~py_trees.common.Status.FAILURE` is
    :data:`~py_trees.common.Status.RUNNING` up to a specified number of
    attempts.

    Args:
        child: the child behaviour or subtree
        num_failures: maximum number of permitted failures
        name: the decorator name
    """

    def __init__(
        self, name: str, child: py_trees.behaviour.Behaviour, num_failures: int
    ):
        super().__init__(name=name, child=child)
        self.failures = 0
        self.num_failures = num_failures
        self.failed_in_this_tick = False

    def tick(self) -> typing.Iterator[py_trees.behaviour.Behaviour]:
        """
        Manage the decorated child through the tick.

        Yields:
            a reference to itself or one of its children
        """
        self.logger.debug("%s.tick()" % self.__class__.__name__)
        # initialise just like other behaviours/composites
        if self.status != py_trees.common.Status.RUNNING:
            self.initialise()
        # interrupt proceedings and process the child node
        # (including any children it may have as well)
        for node in self.decorated.tick():
            yield node
        # resume normal proceedings for a Behaviour's tick
        new_status = self.update()
        if new_status not in list(py_trees.common.Status):
            self.logger.error(
                "A behaviour returned an invalid status, setting to INVALID [%s][%s]"
                % (new_status, self.name)
            )
            new_status = py_trees.common.Status.INVALID
        if new_status != py_trees.common.Status.RUNNING:
            self.stop(new_status)
        self.status = new_status

        if new_status == py_trees.common.Status.RUNNING and self.failed_in_this_tick:
            for node in self.tick():
                yield node
        else:
            yield self

    def initialise(self) -> None:
        """Reset the currently registered number of attempts."""
        self.failures = 0

    def update(self) -> py_trees.common.Status:
        """
        Retry until failure count is reached.

        Returns:
            :data:`~py_trees.common.Status.SUCCESS` on success,
            :data:`~py_trees.common.Status.RUNNING` on running, or pre-nth failure
            :data:`~py_trees.common.Status.FAILURE` only on the nth failure.
        """
        self.failed_in_this_tick = False
        if self.decorated.status == py_trees.common.Status.FAILURE:
            self.failed_in_this_tick = True
            self.failures += 1
            if self.failures < self.num_failures:
                self.feedback_message = f"attempt failed [status: {self.failures} failure from {self.num_failures}]"
                return py_trees.common.Status.RUNNING
            else:
                self.feedback_message = f"final failure [status: {self.failures} failure from {self.num_failures}]"
                return py_trees.common.Status.FAILURE
        elif self.decorated.status == py_trees.common.Status.RUNNING:
            self.feedback_message = (
                f"running [status: {self.failures} failure from {self.num_failures}]"
            )
            return py_trees.common.Status.RUNNING
        else:  # SUCCESS
            self.feedback_message = (
                f"succeeded [status: {self.failures} failure from {self.num_failures}]"
            )
            return py_trees.common.Status.SUCCESS
