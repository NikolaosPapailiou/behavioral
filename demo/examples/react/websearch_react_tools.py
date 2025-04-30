from langchain_community.tools import DuckDuckGoSearchResults
from langchain_core.tools import tool

from behavioral.behavior_lib import create_react_behavior
from behavioral.conversation import ConversationBehaviourTree

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


async def create_websearch_react_tools_tree(chat_model, **kwargs):
    tools = [
        DuckDuckGoSearchResults(num_results=20, output_format="json"),
        get_webpage_full_content,
    ]

    react_tools = await create_react_behavior(
        tools=tools,
        max_runs=3,
        max_tool_calls=10,
    )
    tree = ConversationBehaviourTree(
        root=react_tools,
        conversation_goal_prompt=SYSTEM_INSTRUCTION,
        chat_model=chat_model,
        message_history=10,
    )
    return tree
