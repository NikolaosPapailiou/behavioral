from typing import List

from pydantic import BaseModel, Field

from behavioral.behaviors import (AIToBlackboard, ConversationMessage,
                                  ExpandTree, RemoveChildren)
from behavioral.composites import Sequence
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


def make_joke_behavior(**kwargs):
    return ConversationMessage(
        name="make_joke",
        message_prompt="Make a joke to catch user's engagement.",
    )


def ask_likes_behavior(**kwargs):
    return ConversationMessage(
        name="ask_likes",
        message_prompt="Explain something that you like and then ask the user if they like this or something else.",
    )


def ask_dislikes_behavior(**kwargs):
    return ConversationMessage(
        name="ask_dislikes",
        message_prompt="Explain something that you dislike and then ask the user if they dislike this or something else.",
    )


def say_interesting_fact(**kwargs):
    return ConversationMessage(
        name="say_interesting_fact",
        message_prompt="Say an interesting fact to the user.",
    )


def discuss_weather(**kwargs):
    return ConversationMessage(
        name="discuss_weather",
        message_prompt="Ask about the weather.",
    )


def casual_respond_behavior(**kwargs):
    return ConversationMessage(
        name="casual_respond",
        message_prompt="",
    )


available_behaviors = {
    "make_joke": make_joke_behavior,
    "ask_likes": ask_likes_behavior,
    "ask_dislikes": ask_dislikes_behavior,
    "interesting_fact": say_interesting_fact,
    "discuss_weather": discuss_weather,
    "casual_respond": casual_respond_behavior,
}

available_behaviors_descriptions = (
    "make_joke: Make a joke to catch user's engagement.\n"
    "ask_likes: Explain something that you like and then ask the user if they like this or something else.\n"
    "ask_dislikes: Explain something that you dislike and then ask the user if they dislike this or something else.\n"
    "interesting_fact: Say an interesting fact to the user.\n"
    "discuss_weather: Ask about the weather.\n"
    "casual_respond: Respond casually to the user.\n"
)


def create_behavior_decision_tree(chat_model, **kwargs):
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

    class SelectedBehavior(BaseModel):
        behavior: str = Field(description="The name of the next response behavior")

    pick_behavior = AIToBlackboard(
        "pick_behavior",
        f"""
Available response behaviors:
{available_behaviors_descriptions}

ConversationState:
{{conversation_state}}

Based on the chat history, pick one of the available response behaviors that you think that can better progress the conversation with the user.
    """,
        capture_state_type=SelectedBehavior,
    )

    run_behavior = Sequence("run_behavior", memory=False)
    expand_behavior = ExpandTree(
        "expand_behavior",
        expand_on_state_key="pick_behavior",
        expand_on_state_attribute="behavior",
        expand_target=run_behavior,
        pick_behavior_constructor=available_behaviors,
    )

    reset_behavior = RemoveChildren(
        name="reset_behavior",
        remove_target=run_behavior,
        reset_conversation_state_key="pick_behavior",
    )
    talk = Sequence(
        name="talk",
        children=[reset_behavior, pick_behavior, expand_behavior, run_behavior],
        guard=BehaviorGuard(
            # Wait for message
            guard_on_tick_enter=Guard(
                running_check=lambda a: not a.conversation_tree.has_pending_user_message()
            ),
        ),
    )
    flow = Sequence(name="conversation", children=[intro, talk])
    tree = ConversationBehaviourTree(
        root=flow,
        conversation_goal_prompt=conversation_goal_prompt,
        chat_model=chat_model,
        conversation_state_type=CustomConversationState,
    )
    return tree
