import examples

tree_creators = {
    # behaviors
    "behaviors/conversation_goal": examples.create_conversation_goal_tree,
    "behaviors/conversation_state": examples.create_conversation_state_tree,
    "behaviors/conversation_conditions": examples.create_conversation_conditions_tree,
    "behaviors/behavior_decision": examples.create_behavior_decision_tree,
    "behaviors/dynamic_behaviors": examples.create_dynamic_behaviors_tree,
    "behaviors/parallel_actions": examples.create_parallel_actions_tree,
    # agents
    "agent/websearch-react-tools": examples.create_websearch_react_tools_tree,
    "agent/calculator-react-mcp": examples.create_calculator_react_mcp_tree,
    # flows
    "flow/teacher": examples.create_teacher_tree,
}
tree_descriptions = {
    # behaviors
    "behaviors/conversation_goal": (
        "The goal of the AI is to find out your name! "
        "It will try until it gets the name or believes that the goal is not possible. "
    ),
    "behaviors/conversation_state": (
        "This AI is capturing interesting information from your discussion. "
    ),
    "behaviors/conversation_conditions": (
        "The AI tries to maintain an engaging converstation by attempting different behaviors based on rules. "
        "The selected behavior rules are based on the captured conversation state. "
    ),
    "behaviors/behavior_decision": (
        "The AI tries to maintain an engaging converstation by attempting different behaviors. "
        "The behavior at each message is selected by the AI from a set of available behaviors. "
        "The decision is based on the convesation state and captured history. "
        "The selected behaviors are dynamically added to the tree and removed after completion. "
    ),
    "behaviors/dynamic_behaviors": (
        "This AI wants to tell you a story! "
        "It shows how the AI can plan and dynamically execute a sequence of behavior steps, based on the captured conversation state."
    ),
    "behaviors/parallel_actions": ("Runs 2 async actions in parallel."),
    # agents
    "agent/websearch-react-tools": (
        "AI Agent with web search and web page fetch tools."
        "This uses REACT to execute tools until the Agent is ready to respond."
    ),
    "agent/calculator-react-mcp": (
        "AI Agent with access to a calculator MCP tools."
        "This uses REACT to execute tools until the Agent is ready to respond."
    ),
    # flows
    "flow/teacher": (
        "This AI wants to teach you!"
        "This shows a complex, long-running conversation flow requiring dynamic planning, inactivity based behaviors and high priority interupts."
    ),
}
