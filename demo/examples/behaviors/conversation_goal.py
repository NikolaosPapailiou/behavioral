from pydantic import Field

from behavioral.behaviors import (ConversationGoal,
                                  ConversationGoalStateWithFailure)
from behavioral.conversation import ConversationBehaviourTree


class GetUserNameState(ConversationGoalStateWithFailure):
    name: str = Field(
        title="Name",
        description="The name of the user. Not the name of the assistant. Empty if not known yet.",
    )


def create_conversation_goal_tree(chat_model, **kwargs):
    conversation_goal_prompt = (
        "You are a helpfull and friendly assistant having a conversation with a user."
    )
    get_user_name = ConversationGoal(
        name="get_user_name",
        goal_prompt="Continue the conversation with the user and find way to intelligently ask the user for their name. Try at least 3 time before you mark the goalas failed.",
        capture_state_type=GetUserNameState,
        respond_without_user_message=True,
        seconds_since_last_message=300,
    )
    tree = ConversationBehaviourTree(
        root=get_user_name,
        conversation_goal_prompt=conversation_goal_prompt,
        chat_model=chat_model,
    )
    return tree
