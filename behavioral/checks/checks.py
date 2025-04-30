import operator
import time
from typing import Callable, Optional

from behavioral.base import Behavior


def check_blackboard_val(
    behavior: Behavior,
    key: str,
    attribute: Optional[str] = None,
    check: Optional[Callable] = None,
    **kwargs,
):
    value = behavior.conversation_tree.bb.get_value(key, namespace=behavior.namespace)
    if value is None:
        return False

    if attribute is not None:
        value = operator.attrgetter(attribute)(value)
        if value is None:
            return False
    if check is None:
        return bool(value)
    return check(value, **kwargs)


def get_blackboard_val(
    behavior: Behavior,
    key: str,
    attribute: Optional[str] = None,
):
    value = behavior.conversation_tree.bb.get_value(key, namespace=behavior.namespace)
    if value is None:
        return None

    if attribute is not None:
        value = operator.attrgetter(attribute)(value)
        if value is None:
            return None
    return value


def is_user_active(behavior: Behavior, time_since_last_message):
    if len(behavior.conversation_tree.chat_history) == 0:
        return True
    current_time = time.time()
    if (
        current_time - behavior.conversation_tree.last_message_time
        > time_since_last_message
    ):
        return False
    return True
