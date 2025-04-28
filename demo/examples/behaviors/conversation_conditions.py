from typing import List

from pydantic import Field

from behavioral.behaviors import ConversationMessage
from behavioral.checks import check_blackboard_val
from behavioral.composites import Selector, Sequence
from behavioral.conversation import (ConversationBehaviourTree,
                                     ConversationState)
from behavioral.guards import BehaviorGuard, Guard


class CustomConversationState(ConversationState):
    name: str = Field(
        title="User Name",
        description="The name of the user(**not the assistant**). Empty if not known yet.",
    )
    likes: List[str] = Field(
        title="User Likes",
        description="Things that the user (**not the assistant**) mentioned, indicated or agreed that they like.",
    )
    dislikes: List[str] = Field(
        title="User Dislikes",
        description="Things that the user (**not the assistant**) mentioned, indicated or agreed that they dislike.",
    )
    info: List[str] = Field(
        title="Information About the User",
        description="List of information about the user(**not the assistant**) that should be remembered.",
    )


def create_conversation_conditions_tree(chat_model, **kwargs):
    conversation_goal_prompt = (
        "Your name is Bob, you are a very social person that wants to get to know others and have a good time."
        "Always continue the conversation with the user in a natural manner and transition smoothly according to the provided goals."
    )
    intro = ConversationMessage(
        name="intro",
        message_prompt="It's your first message to a conversation with a new user. Reach out to get to know them.",
        respond_without_user_message=True,
        max_messages_sent=1,
    )

    make_joke = ConversationMessage(
        name="make_joke",
        message_prompt="Make a joke to catch user's engagement.",
        guard=BehaviorGuard(
            guard_on_tick_enter=Guard(
                failure_check=check_blackboard_val,
                failure_check_kwargs={
                    "key": "conversation_state",
                    "attribute": "user_engagement",
                    "check": lambda a: a > 0.4,
                },
            ),
        ),
        seconds_since_last_message=120,
    )
    ask_likes = ConversationMessage(
        name="ask_likes",
        message_prompt="Explain something that you like and then ask the user if they like this or something else.",
        guard=BehaviorGuard(
            guard_on_tick_enter=Guard(
                failure_check=check_blackboard_val,
                failure_check_kwargs={
                    "key": "conversation_state",
                    "attribute": "likes",
                    "check": lambda a: len(a) > 0,
                },
            ),
        ),
        seconds_since_last_message=180,
    )
    ask_dislikes = ConversationMessage(
        name="ask_dislikes",
        message_prompt="Explain something that you dislike and then ask the user if they dislike this or something else.",
        guard=BehaviorGuard(
            guard_on_tick_enter=Guard(
                failure_check=check_blackboard_val,
                failure_check_kwargs={
                    "key": "conversation_state",
                    "attribute": "dislikes",
                    "check": lambda a: len(a) > 0,
                },
            ),
        ),
        seconds_since_last_message=180,
    )
    casual_respond = ConversationMessage(
        name="casual_respond",
        message_prompt="",
    )
    talk = Selector(
        name="talk",
        children=[make_joke, ask_likes, ask_dislikes, casual_respond],
        memory=False,
    )
    flow = Sequence(name="conversation", children=[intro, talk])
    tree = ConversationBehaviourTree(
        root=flow,
        conversation_goal_prompt=conversation_goal_prompt,
        chat_model=chat_model,
        conversation_state_type=CustomConversationState,
    )
    return tree
