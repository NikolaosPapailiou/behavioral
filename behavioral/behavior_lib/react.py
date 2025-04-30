from typing import List

import py_trees
from langchain_core.tools import BaseTool

from behavioral.behaviors import (AIToBlackboard, ConversationMessage,
                                  RemoveBlackboardVariable,
                                  RespondToUserFromBlackboard, RunTools)
from behavioral.checks import get_blackboard_val
from behavioral.composites import Selector, Sequence
from behavioral.guards import BehaviorGuard, Guard


async def create_react_behavior(
    tools: List[BaseTool], max_runs: int = 10, max_tool_calls: int = 10, **kwargs
):
    invoke = AIToBlackboard(
        name="invoke",
        prompt="""
You are solving the user question by a sequence of tool executions 

Previously executed tools with results:
{tool_results}

Only add the tools that are needed for this stage of computation.
Do not proactively execute tools that depend on other tool results that you haven't yet executed.
Respond if ready to answer the question otherwise execute some tools.
""",
        tools=tools,
        state_key="invoke",
    )

    def has_tools(behavior):
        invoke_result = get_blackboard_val(
            behavior=behavior,
            key="invoke",
        )
        return (
            invoke_result is not None
            and invoke_result.tool_calls is not None
            and len(invoke_result.tool_calls) > 0
        )

    run_tools = RunTools(
        name="run_tools",
        # if no tools succeed
        guard=BehaviorGuard(
            guard_on_tick_enter=Guard(success_check=lambda a: not has_tools(a))
        ),
        tools=tools,
        invoke_bb_key="invoke",
        tools_bb_output="tool_results",
        max_runs=max_runs,
        max_tool_calls=max_tool_calls,
    )

    react_loop = Sequence(
        "react_loop",
        guard=BehaviorGuard(
            # continue if this iteration succeeded and tools were executed
            guard_on_tick_exit=Guard(
                running_check=lambda a: a.status == py_trees.common.Status.SUCCESS
                and has_tools(a)
            ),
        ),
        children=[invoke, run_tools],
    )

    # Respond if no more tools from invoke output
    respond = RespondToUserFromBlackboard(name="respond", bb_variable="invoke.content")
    # If max tools reached respond with a new message
    respond_on_failure = ConversationMessage(
        name="respond_on_failure",
        message_prompt="""
Previously executed tools with results:
{tool_results}

Respond to the user question based on the tool results.
""",
    )

    react_and_respond = Sequence(
        "react_and_respond",
        children=[
            RemoveBlackboardVariable("reset_tool_results", key="tool_results"),
            react_loop,
            respond,
        ],
    )
    react = Selector(
        name="react",
        guard=BehaviorGuard(
            # Wait for user message
            guard_on_tick_enter=Guard(
                running_check=lambda a: not a.conversation_tree.has_pending_user_message()
            ),
        ),
        children=[react_and_respond, respond_on_failure],
    )
    return react
