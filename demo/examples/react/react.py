from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool

from behavioral.behaviors import (AIToBlackboard, RemoveBlackboardVariable,
                                  RespondToUserFromBlackboard, RunTools)
from behavioral.composites import Sequence
from behavioral.conversation import ConversationBehaviourTree
from behavioral.guards import BehaviorGuard, Guard

SYSTEM_INSTRUCTION = (
    "You are a helpfull deep research assistant, well-know for your ability to explore the web, find facts from webpages and produce reports. "
    "You always validate your sources by checking the content of actual webpages and don't respond just from the web results. "
    "When asked a question from the user you will create a comprehensive, well-structured research report based on searching the web and exploring "
    "the full content of the relevant web pages. "
    "Your report should be structured as **markdown**, critical information in your response should always contain reference links to the actual webpage. "
    "Use text markdown links and DONOT add vissible text urls "
    "DO NOT use many bullet points but rather use sections and paragraphs with titles or tables. "
    "You can perform multiple web search and page fetchs to provide a response. "
    "You don't have to ask the user for permission to use tools. "
)


@tool
async def get_webpage_full_content(url: str):
    """Use this to get the full content of a web page based on its URL.
    Use this tool if you think a web result snippet is interesting and you want to get all the information contained in the page.

    Args:
        url: The web page url(link)
    """
    try:
        from langchain_community.document_loaders import AsyncChromiumLoader
        from langchain_community.document_transformers import \
            BeautifulSoupTransformer

        bs_transformer = BeautifulSoupTransformer()
        loader = AsyncChromiumLoader([url])
        html = await loader.aload()
        docs_transformed = bs_transformer.transform_documents(
            html, tags_to_extract=["p", "li", "div", "a"]
        )
        return docs_transformed[0].page_content
    except Exception as e:
        return {"error": f"get_webpage_full_content tool failed: {e}"}


def create_react_tree(chat_model, **kwargs):
    tree = ConversationBehaviourTree(
        root=create_react_behavior(chat_model=chat_model),
        conversation_goal_prompt=SYSTEM_INSTRUCTION,
        chat_model=chat_model,
        message_history=50,
    )
    return tree


def create_react_behavior(chat_model, **kwargs):
    available_tools = [
        DuckDuckGoSearchResults(num_results=20, output_format="json"),
        get_webpage_full_content,
    ]

    invoke = AIToBlackboard(
        name="invoke",
        prompt="""
Previously executed tools with results:
{tool_results}

You can use web search tools for getting realtime information and new of what is currently happening. 
The web search snippets contain only part of the actual web page information. 
To provide detailed responses with facts please use the get_webpage_full_content to fetch the full web page content of the most relevant search pages.

Answer to the user question or execute a tool.
""",
        tools=available_tools,
        state_key="invoke",
    )

    def no_tools(a):
        invoke_result = a.conversation_tree.bb.get_value(
            "invoke", namespace=a.namespace
        )
        return (
            invoke_result is None
            or invoke_result.tool_calls is None
            or len(invoke_result.tool_calls) == 0
        )

    tools = RunTools(
        name="tools",
        guard=BehaviorGuard(guard_on_tick_enter=Guard(success_check=no_tools)),
        tools=available_tools,
        invoke_bb_key="invoke",
        tools_bb_output="tool_results",
    )
    react = Sequence(
        "react",
        guard=BehaviorGuard(
            # Wait for message
            guard_on_tick_enter=Guard(
                running_check=lambda a: not a.conversation_tree.has_pending_user_message()
            ),
            # unitl no tools in AI response
            guard_on_tick_exit=Guard(running_check=lambda a: not no_tools(a)),
        ),
        memory=True,
        children=[invoke, tools],
    )
    respond = RespondToUserFromBlackboard(name="respond", bb_variable="invoke.content")
    react_and_respond = Sequence(
        "react_and_respond",
        memory=True,
        children=[
            RemoveBlackboardVariable("reset_tool_results", key="tool_results"),
            react,
            respond,
        ],
    )
    return react_and_respond
