from typing import List

import py_trees
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.runnables import RunnableSerializable
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from behavioral.conversation import ChatMessage

logger = py_trees.logging.Logger(__name__)


async def ainvoke(
    chat_model: BaseChatModel,
    conversation_goal_prompt: str,
    prompt: str,
    chat_history: list[ChatMessage],
    extra_chain_runnables: RunnableSerializable = None,
    tools: List[BaseTool] = None,
    structured_output: type[BaseModel] = None,
):
    logger.debug(f"Invoke: {chat_model.model}")
    model_prompt = [{"role": "system", "content": conversation_goal_prompt}]
    model_prompt.append(chat_history)
    model_prompt.append({"role": "system", "content": prompt})
    chain = chat_model
    if tools is not None:
        chain = chain.bind_tools(tools)
    if extra_chain_runnables is not None:
        chain = chain | extra_chain_runnables
    if structured_output is not None:
        chain = chain.with_structured_output(structured_output)
    ret = await chain.ainvoke(str(model_prompt))
    return ret


async def respond_to_user(
    chat_model: BaseChatModel,
    response_message: ChatMessage,
    conversation_goal_prompt,
    current_goal_prompt: str,
    chat_history: list,
    extra_chain_runnables: RunnableSerializable = None,
    tools: List[BaseTool] = None,
):
    logger.debug(f"Responding to user {chat_model.model}")
    messages = [
        {
            "role": "system",
            "content": conversation_goal_prompt
            + """

An external system guides your conversation with the user.
For your response, you must strictly follow the instructions of the external system reported as system messages.
The instructions can be achieved in multiple conversation steps. You don't have to achieve all goals of the instructions in one message.
Continue the conversation with the user naturally but don't let them drift the conversation from the system instructions.
Respond only with the content of your message. You are talking to the user directly. Do not repeat your previous messages.
""",
        },
    ]
    for m in chat_history:
        messages.append(m)

    messages.append(
        {
            "role": "system",
            "content": f"External system instruction: {current_goal_prompt}",
        }
    )

    chain = chat_model
    if tools is not None:
        chain = chain.bind_tools(tools)
    if extra_chain_runnables is not None:
        chain = chain | extra_chain_runnables
    async for chunk in chain.astream(str(messages)):
        response_message.content += chunk.content
    response_message.metadata["completed"] = True
    logger.debug(f"Responding to user {chat_model.model}")
    return response_message


async def capture_conversation_state(
    chat_model: BaseChatModel,
    chat_history: list,
    non_captured_messages: int,
    previous_state: BaseModel,
    state_type: type[BaseModel],
    extra_chain_runnables: RunnableSerializable = None,
    tools: List[BaseTool] = None,
) -> BaseModel:
    prompt = [
        {
            "role": "user",
            "content": f"""
You are an expert at capturing/updating the structured state of conversations between users and assistants.

You are distinguished for your attention to detail and for only including structured details that are actually present in the conversation with the user.
Leave structure fields empty or maintain their previous conversation state value if there is no relative information in the conversation history.
Do not come up with new data that are not in the conversation or the previous conversation state.

Conversation history:
{chat_history[:-non_captured_messages]}

Previous conversation state:
{previous_state.model_dump_json(indent=2) if previous_state else "None"}

New assistant/user messages:
{chat_history[-non_captured_messages:]}
        """,
        }
    ]
    return await capture_state(
        chat_model=chat_model,
        prompt=prompt,
        state_type=state_type,
        extra_chain_runnables=extra_chain_runnables,
        tools=tools,
    )


async def capture_goal_state(
    chat_model: BaseChatModel,
    goal_prompt: str,
    chat_history: list,
    non_captured_messages: int,
    previous_state: BaseModel,
    state_type: type[BaseModel],
    extra_chain_runnables: RunnableSerializable = None,
    tools: List[BaseTool] = None,
) -> BaseModel:
    prompt = [
        {
            "role": "user",
            "content": f"""
You are an expert at capturing/updating the structured state of conversations between users and assistants.

You are distinguished for your attention to detail and for only including structured details that are actually present in the conversation with the user.
Leave structure fields empty or maintain their previous conversation state value if there is no relative information in the conversation history.
Do not come up with new data that are not in the conversation or the previous conversation state.
Make sure to **always** check if the current assistant's goal is achieved or failed.

Current assistant conversation goal: 
{goal_prompt}

Conversation history:
{chat_history[:-non_captured_messages]}

Previous conversation state:
{previous_state.model_dump_json(indent=2) if previous_state else "None"}

New assistant/user messages:
{chat_history[-non_captured_messages:]}
        """,
        }
    ]
    return await capture_state(
        chat_model=chat_model,
        prompt=prompt,
        state_type=state_type,
        extra_chain_runnables=extra_chain_runnables,
        tools=tools,
    )


async def capture_state(
    chat_model: BaseChatModel,
    prompt: str,
    state_type: type[BaseModel],
    extra_chain_runnables: RunnableSerializable = None,
    tools: List[BaseTool] = None,
) -> BaseModel:
    logger.debug(f"Capturing state prompt {prompt}")
    chain = chat_model
    if tools is not None:
        chain = chain.bind_tools(tools)
    if extra_chain_runnables is not None:
        chain = chain | extra_chain_runnables
    if state_type is not None:
        chain = chain.with_structured_output(state_type)
    captured_state = await chain.ainvoke(prompt)
    return captured_state
