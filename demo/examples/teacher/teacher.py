from typing import List

from examples.teacher.topic import create_per_topic_behavior
from pydantic import Field

from behavioral.behaviors import ConversationMessage, ExpandTree
from behavioral.checks import check_blackboard_val, is_user_active
from behavioral.composites import Sequence
from behavioral.conversation import (ConversationBehaviourTree,
                                     ConversationState)
from behavioral.guards import BehaviorGuard, Guard
from behavioral.utils import PartialPromptParams


# States
class TeachingConversationState(ConversationState):
    intro_done: bool = Field(
        title="Intro Done",
        description="True if the assistant has introduced himself to the user.",
    )
    subject: str = Field(
        title="Teaching Subject",
        description="The teaching subject selected by the user. **Only fill this if the user has accepted the subject**",
    )
    topics: List[str] = Field(
        title="Topics",
        description="A list of teaching topics for the subject. Only add topics if they were accepted by the user.",
    )


async def create_teacher_behavior(prompt_params: PartialPromptParams, **kwargs):
    intro = ConversationMessage(
        "intro",
        "Introduce yourself and the purpose of the conversation.",
        respond_without_user_message=True,
        prompt_params=prompt_params,
        guard=BehaviorGuard(
            guard_on_tick_enter=Guard(
                success_check=check_blackboard_val,
                success_check_kwargs={
                    "key": "conversation_state",
                    "attribute": "intro_done",
                },
            ),
        ),
        max_messages_sent=1,
    )
    subject = ConversationMessage(
        "subject",
        "Propose and have the user accept a teaching subject. Just decide on the subject and don't split it into topics yet.",
        prompt_params=prompt_params,
        guard=BehaviorGuard(
            guard_on_tick_enter=Guard(
                success_check=check_blackboard_val,
                success_check_kwargs={
                    "key": "conversation_state",
                    "attribute": "subject",
                    "check": lambda a: a != "",
                },
            ),
        ),
    )
    split_topics = ConversationMessage(
        "split_topics",
        """Suggest a list of topics titles to the user and ask them for confirmation.
        Do not start explaining topics before the user agrees on a set of topics.
        Pick 2 to 5 topics.
        """,
        prompt_params=prompt_params,
        guard=BehaviorGuard(
            guard_on_tick_enter=Guard(
                success_check=check_blackboard_val,
                success_check_kwargs={
                    "key": "conversation_state",
                    "attribute": "topics",
                    "check": lambda a: a != [],
                },
            ),
        ),
    )

    explain_topics_seq = Sequence("explain_topics", memory=True)
    expand_topics = ExpandTree(
        name="expand_topics",
        expand_on_state_key="conversation_state",
        expand_on_state_attribute="topics",
        expand_target=explain_topics_seq,
        expand_prompt_param_key="topic",
        behavior_constructor=create_per_topic_behavior,
        prompt_params=prompt_params,
    )

    respond_to_inactivity = ConversationMessage(
        "respond_to_inactivity",
        "The user was inactive in the conversation, send a funny message to let them know that you are waiting for their response.",
        max_messages_sent=2,
        respond_without_user_message=True,
        prompt_params=prompt_params,
        guard=BehaviorGuard(
            guard_on_tick_enter=Guard(
                success_check=is_user_active,
                success_check_kwargs={
                    "time_since_last_message": 120,
                },
            ),
        ),
    )

    end = ConversationMessage(
        "end",
        "Summarize the teaching session and thank the user for their time.",
        prompt_params=prompt_params,
    )

    teach = Sequence("teach", memory=True)
    teach.add_children(
        [
            intro,
            subject,
            split_topics,
            expand_topics,
            explain_topics_seq,
            end,
        ]
    )
    teach_chat = Sequence("teach_chat", memory=False)
    teach_chat.add_children([respond_to_inactivity, teach])
    return teach_chat


conversation_goal_prompt = """
You are Nikos a helpful teacher that wants to teach users whatever they want to learn.
You are following a process of selecting a subject, then splitting it in topics and teaching each topic independently and assessing the user. 
Teach only factual and truthful information.
"""


async def create_teacher_tree(
    chat_model,
    prompt_params: PartialPromptParams = PartialPromptParams(),
    namespace: str = None,
    **kwargs,
):
    tree = ConversationBehaviourTree(
        root=await create_teacher_behavior(prompt_params),
        conversation_goal_prompt=conversation_goal_prompt,
        chat_model=chat_model,
        conversation_state_type=TeachingConversationState,
        namespace=namespace,
    )
    return tree
