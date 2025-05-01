import py_trees

from behavioral.behaviors import RespondToUser, Wait
from behavioral.composites import Parallel, Sequence
from behavioral.conversation import ConversationBehaviourTree


def create_timer_behavior(delay: float):
    message_before = RespondToUser(
        name=f"message_before_{delay}s",
        message=f"Setting timer: {delay}s",
    )
    wait = Wait(delay=delay)
    message_after = RespondToUser(
        name=f"message_after_{delay}s",
        message=f"{delay}s passed",
    )
    return Sequence(
        name=f"timer_{delay}s", children=[message_before, wait, message_after]
    )


async def create_parallel_actions_tree(chat_model, **kwargs):
    timer_5s = create_timer_behavior(5)
    timer_10s = create_timer_behavior(10)
    timer_15s = create_timer_behavior(15)
    timer_20s = create_timer_behavior(20)
    parallel_timers = Parallel(
        name="parallel_timers",
        policy=py_trees.common.ParallelPolicy.SuccessOnAll(),
        children=[timer_5s, timer_10s, timer_15s, timer_20s],
    )
    tree = ConversationBehaviourTree(
        root=parallel_timers,
        conversation_goal_prompt="",
        chat_model=chat_model,
    )
    return tree
