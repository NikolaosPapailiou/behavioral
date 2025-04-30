from typing import List

from pydantic import Field

from behavioral.behaviors import ConversationMessage
from behavioral.composites import Sequence
from behavioral.conversation import (ConversationBehaviourTree,
                                     ConversationState)


class CustomConversationState(ConversationState):
    name: str = Field(
        title="User Name",
        description="The name of the user. Not the name of the assistant. Empty if not known yet.",
    )
    likes: List[str] = Field(
        title="User Likes",
        description="Things that the user mentioned that they like.",
    )
    dislikes: List[str] = Field(
        title="User Dislikes",
        description="Things that the user mentioned that they dislike.",
    )
    info: List[str] = Field(
        title="Information About the User",
        description="List of information about the user that you think should be remembered.",
    )


async def create_conversation_state_tree(chat_model, **kwargs):
    conversation_goal_prompt = "Your name is Bob, you are a very social person that wants to get to know others and have a good time."
    intro = ConversationMessage(
        name="intro",
        message_prompt="It's your first message to a conversation with a new user. Reach out to get to know them.",
        respond_without_user_message=True,
        max_messages_sent=1,
    )
    talk = ConversationMessage(
        name="talk",
        message_prompt="Continue the conversation and engage the user.",
    )
    flow = Sequence(name="conversation", children=[intro, talk])
    tree = ConversationBehaviourTree(
        root=flow,
        conversation_goal_prompt=conversation_goal_prompt,
        chat_model=chat_model,
        conversation_state_type=CustomConversationState,
    )
    return tree
