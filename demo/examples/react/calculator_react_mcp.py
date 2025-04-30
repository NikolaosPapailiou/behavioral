from contextlib import AsyncExitStack

from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from behavioral.behavior_lib import create_react_behavior
from behavioral.conversation import ConversationBehaviourTree

SYSTEM_INSTRUCTION = (
    "You are a helpfull assistant with tools. "
    "Decide if you need to use any of the available tools to help you respond to the user. "
    "Be thorough, use available tools if they can help you help the user better or provide more accurate responses. "
)

exit_stack: AsyncExitStack = AsyncExitStack()


async def initialize():
    try:
        server_params = StdioServerParameters(
            command="python",
            args=["demo/examples/react/mcp_calculator.py"],
        )
        client_transport = await exit_stack.enter_async_context(
            stdio_client(server_params)
        )

        read, write = client_transport
        session = await exit_stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        tools = await load_mcp_tools(session)
        return tools

    except Exception as e:
        print(f"Error initializing server {e}")
        raise


async def create_calculator_react_mcp_tree(chat_model, **kwargs):
    mcp_tools = await initialize()
    react_mcp = await create_react_behavior(
        tools=mcp_tools,
        max_runs=5,
        max_tool_calls=5,
    )
    tree = ConversationBehaviourTree(
        root=react_mcp,
        conversation_goal_prompt=SYSTEM_INSTRUCTION,
        chat_model=chat_model,
        message_history=10,
    )
    return tree
