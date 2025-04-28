from typing import List

from pydantic import BaseModel, Field

from behavioral.behaviors import (AIToBlackboard, ConversationGoal,
                                  ConversationGoalWithStateEval,
                                  ConversationMessage, ExpandTree)
from behavioral.composites import Sequence
from behavioral.utils import PartialPromptParams


# states
class TopicSections(BaseModel):
    """
    Set of teaching sections for a teaching topic.
    """

    section_titles: List[str] = Field(
        title="Topic section titles",
        description="A list of teaching section titles for the topic.",
    )


class TopicAssessmentState(BaseModel):
    """
    State of a Teaching Topic assessment question.
    """

    question: str = Field(
        title="Question",
        description="The topic assessment question. Also include the multiple choice options.",
    )
    response: str = Field(
        title="Response",
        description="The user response to the topic assessment question.",
    )
    correct_response: bool = Field(
        title="Response Assessment",
        description="True, if the user response was correct. Do not be lenient in your assessment.",
    )


class TopicAssessmentsState(BaseModel):
    """
    State of a Teaching Topic assessment.
    """

    assessments: List[TopicAssessmentState] = Field(
        title="Topic assessment questions",
        description="A list of question assessments of the user for the topic.",
    )


def create_explain_section_behavior(
    prompt_params: PartialPromptParams, **kwargs
) -> Sequence:
    new_prompt_params = PartialPromptParams(
        topic_state_key=prompt_params.format("plan_sections({topic}).section_titles")
    )
    new_prompt_params.update(prompt_params)
    return ConversationGoal(
        name=new_prompt_params.format("explain_section({section})"),
        prompt_params=new_prompt_params,
        goal_prompt="""
    The current teaching subject is {conversation_state.subject}.
    The list of all topics in this subject are: {conversation_state.topics}.
    The current teaching topic is {topic}.
    You are currently ** only** explaining the section: {section}. 
    **Do not** start explaining other sections or topics in this subject.
    Mark the goal as achieved if you have sufficiently explained the section {section} and the user has understood it.
    """,
    )


def create_per_topic_behavior(prompt_params: PartialPromptParams, **kwargs) -> Sequence:
    print(f"Creating per topic behavior with prompt params: {prompt_params}")
    topic = prompt_params["topic"]
    topic_greet = ConversationMessage(
        f"topic_greet({topic})",
        f"The current teaching subject is {{conversation_state.subject}}. Let the user know that you will now start teaching the topic: {topic}. Do not end your message with questions.",
        prompt_params=prompt_params,
        max_messages_sent=1,
    )

    plan_sections = AIToBlackboard(
        f"plan_sections({topic})",
        f"""
    You are an expert at splitting teaching topics into small, well-contained teaching sections.
    Each section should be a small unit of teaching that can be taught with a couple of messages.
    Your list of sections need to effectively cover the topic. Create a list of 2 to 5 sections.
    Avoid creating sections that have been already taught in previous topics.

    The current teaching state is {{states}}.
    The current teaching topic is {topic}.

    """,
        capture_state_type=TopicSections,
        prompt_params=prompt_params,
        memory=True,
    )

    explain_sections = Sequence("explain_sections", memory=False)
    expand_sections = ExpandTree(
        name="expand_sections",
        expand_on_state_key=f"plan_sections({topic})",
        expand_on_state_attribute="section_titles",
        expand_target=explain_sections,
        expand_prompt_param_key="section",
        behavior_constructor=create_explain_section_behavior,
        prompt_params=prompt_params,
    )

    questions = ConversationGoal(
        f"questions({topic})",
        f"Ask the user if they want to ask any questions about the topic {topic}. Also respond to previous user questions. The goal is achieved if the user does not have any more questions. Do not fail the goal if the user has questions.",
        prompt_params=prompt_params,
    )
    topic_assessment = ConversationGoalWithStateEval(
        f"topic_assessment({topic})",
        f"""Assess the user on topic {topic} by asking multiple choice questions.
    Keep asking questions even if the user has already answered some of them.
    Pick questions that refer to different sections of the topic.
    If there is a previous question, explain which answer was correct before asking the new question.
    Do not repeat previous questions. Do not in any case start explaining or referring to the next section.
    """,
        goal_achieved_eval_check="""
len(state.assessments if state.assessments is not None else []) >= 3 and (
sum([a.correct_response if a is not None and a.correct_response is not None else 0 
for a in state.assessments] if state.assessments is not None else []) / 
len(state.assessments if state.assessments is not None else [1]) >= 0.7)
""",
        capture_state_type=TopicAssessmentsState,
        prompt_params=prompt_params,
    )
    topic_sum = ConversationMessage(
        f"topic_sum({topic})",
        f"Provide assessment feedback to the user and give a summary of what they learned in topic {topic}.",
        prompt_params=prompt_params,
        max_messages_sent=1,
    )
    seq = Sequence(f"explain_topic({topic})", memory=True)
    seq.add_children(
        [
            topic_greet,
            plan_sections,
            expand_sections,
            explain_sections,
            questions,
            topic_assessment,
            topic_sum,
        ]
    )
    return seq
