import asyncio
from typing import List, Optional

import py_trees
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from behavioral.base import AsyncBehavior
from behavioral.guards import BehaviorGuard


class ToolExecution(BaseModel):
    tool_call: str = ""
    tool_output: str = ""


class ToolExecutions(BaseModel):
    tool_executions: dict[str, ToolExecution] = {}


class RunTools(AsyncBehavior):
    def __init__(
        self,
        name: str,
        tools: List[BaseTool],
        guard: Optional[BehaviorGuard] = None,
        retry_errors: int = 3,
        invoke_bb_key: str = "invoke",
        tools_bb_output="tool_results",
    ):
        super().__init__(
            name=name,
            guard=guard,
            retry_errors=retry_errors,
        )
        self.tools = tools
        self.invoke_bb_key = invoke_bb_key
        self.tools_bb_output = tools_bb_output
        self.tools_dict = {}
        for tool in self.tools:
            self.tools_dict[tool.name] = tool

    async def async_update(self) -> py_trees.common.Status:
        self.logger.debug("Calling tools")
        tool_calls = self.conversation_tree.bb.get_value(
            key=self.invoke_bb_key, namespace=self.namespace
        ).tool_calls
        tool_output = self.conversation_tree.bb.get_value(
            key=self.tools_bb_output, namespace=self.namespace
        )
        if tool_output is None:
            tool_output = ToolExecutions()
            self.conversation_tree.bb.set_value(
                key=self.tools_bb_output, value=tool_output, namespace=self.namespace
            )
        tasks = []
        for tool_call in tool_calls:
            self.logger.debug(f"Calling tool: {tool_call}")
            tool_output.tool_executions[tool_call["id"]] = ToolExecution(
                tool_call=str(tool_call)
            )
            selected_tool = self.tools_dict[tool_call["name"].lower()]
            tasks.append(asyncio.create_task(selected_tool.ainvoke(tool_call["args"])))
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # self.logger.debug("Results: {results}")
        for i in range(len(results)):
            tool_output.tool_executions[tool_calls[i]["id"]] = ToolExecution(
                tool_call=str(tool_calls[i]), tool_output=str(results[i])
            )
        return py_trees.common.Status.SUCCESS
