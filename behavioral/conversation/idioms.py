import py_trees


def message_until_condition(
    check: py_trees.common.ComparisonExpression,
    task: py_trees.behaviour.BehaviourSubClass,
) -> py_trees.behaviour.Behaviour:
    from behavioral.behaviors import CheckBlackboardVariableValue

    sel = py_trees.composites.Selector(name=task.name + "_selector", memory=False)
    seq = py_trees.composites.Sequence(name=task.name + "_sequence", memory=False)
    check_before = CheckBlackboardVariableValue(
        name=task.name + "_check_before", check=check
    )
    check_after = CheckBlackboardVariableValue(
        name=task.name + "_check_after", check=check
    )
    sel.add_children([check_before, seq])
    seq.add_children([task, check_after])
    return py_trees.decorators.FailureIsRunning(
        name=task.name + "_run_until_condition", child=sel
    )


def message_on_condition(
    check: py_trees.common.ComparisonExpression,
    task: py_trees.behaviour.BehaviourSubClass,
) -> py_trees.behaviour.Behaviour:
    from behavioral.behaviors import CheckBlackboardVariableValue

    sel = py_trees.composites.Selector(name=task.name + "_selector", memory=False)
    check = CheckBlackboardVariableValue(name=task.name + "_check", check=check)
    sel.add_children([check, task])
    return py_trees.decorators.FailureIsRunning(
        name=task.name + "_run_until_condition", child=sel
    )
