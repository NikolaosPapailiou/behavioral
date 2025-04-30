from typing import List

from pydantic import BaseModel, Field

from behavioral.behaviors import (AIToBlackboard, ConversationGoal,
                                  ConversationGoalState, ConversationMessage,
                                  ExpandTree)
from behavioral.composites import Sequence
from behavioral.conversation import ConversationBehaviourTree
from behavioral.utils import PartialPromptParams


class StoryState(ConversationGoalState):
    story_theme_details: List[str] = Field(
        title="Story Theme Details",
        description="Story theme details that the user(**not the assistatn**) mentioned or aggreed that they want. Examples: space exploration, with cowboys, commedy, funny etc.",
    )


class StoryEpisode(BaseModel):
    episode_title: str = Field(description="The episode title")
    episode_short_description: str = Field(
        description="A short description of the episode containing the **major** plot points that need to be covered not more than 30 words."
    )


class Character(BaseModel):
    name: str
    short_descritpion: str


class StoryPlan(BaseModel):
    story_abstract: str = Field(
        "A short description of this episode. This should only contain the **major** plot points that need to be covered."
    )
    episodes: List[StoryEpisode]
    characters: List[Character]


def create_per_episode_behavior(prompt_params: PartialPromptParams, **kwargs):
    episode = prompt_params["episode"]
    print(f"!!@@@episode{episode}")
    return ConversationMessage(
        name=f"narate_episode({episode.episode_title})",
        prompt_params=prompt_params,
        message_prompt=prompt_params.format("""
    You are narrating a story with 
    Story Theme: 
    {get_story_details}

    Story Plan:
    {plan_story}

    The current story episode is: {episode.episode_title}. 
    With short description {episode.episode_short_description}

    Narrate the current episode. Do not use more than 1000 words.
    """),
        max_messages_sent=1,
    )


async def create_dynamic_behaviors_tree(chat_model, **kwargs):
    conversation_goal_prompt = "Your name is Edward, you are a very good storyteller."
    intro = ConversationMessage(
        name="intro",
        message_prompt="Introduce yourself and the purpose of the conversation.",
        respond_without_user_message=True,
        max_messages_sent=1,
    )

    get_story_details = ConversationGoal(
        name="get_story_details",
        goal_prompt="Propose a story theme and ask the user for their theme preferences. The goal is achieved if you captured at least 1 theme detail.",
        capture_state_type=StoryState,
    )
    plan_story = AIToBlackboard(
        "plan_story",
        """
    You are an expert at creating stories scenarios with a set of 3-5 episodes.
    Make the plot interesting in oredr to engage the user.
    Each episode should be able to be narrated in less than 100 words.

    Story theme {get_story_details}.
    """,
        capture_state_type=StoryPlan,
        memory=True,
    )

    tell_story = Sequence("tell_story", memory=True)
    expand_episodes = ExpandTree(
        name="expand_episodes",
        expand_on_state_key="plan_story",
        expand_on_state_attribute="episodes",
        expand_target=tell_story,
        expand_prompt_param_key="episode",
        behavior_constructor=create_per_episode_behavior,
    )

    flow = Sequence(
        name="conversation",
        children=[intro, get_story_details, plan_story, expand_episodes, tell_story],
    )
    tree = ConversationBehaviourTree(
        root=flow,
        conversation_goal_prompt=conversation_goal_prompt,
        chat_model=chat_model,
    )
    return tree
