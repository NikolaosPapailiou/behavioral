from typing import List, Optional

from langchain_core.runnables import RunnableSerializable
from langchain_core.tools import BaseTool
from pydantic import BaseModel

from behavioral.behaviors.conversation_goal import ConversationGoal
from behavioral.guards import BehaviorGuard
from behavioral.utils import PartialPromptParams


class ConversationGoalWithStateEval(ConversationGoal):
    def __init__(
        self,
        name: str,
        goal_prompt: str,
        goal_achieved_eval_check: str,
        guard: Optional[BehaviorGuard] = None,
        prompt_params: PartialPromptParams = PartialPromptParams(),
        retry_errors: int = 3,
        goal_failed_eval_check: str = None,
        extra_chain_runnables: RunnableSerializable = None,
        tools: List[BaseTool] = None,
        capture_state_type: type = BaseModel,
        respond_without_user_message: bool = False,
        max_messages_sent: int = -1,
        seconds_since_last_message: float = 60,
    ):
        super().__init__(
            name=name,
            goal_prompt=goal_prompt,
            guard=guard,
            prompt_params=prompt_params,
            retry_errors=retry_errors,
            extra_chain_runnables=extra_chain_runnables,
            tools=tools,
            capture_state_type=capture_state_type,
            respond_without_user_message=respond_without_user_message,
            max_messages_sent=max_messages_sent,
            seconds_since_last_message=seconds_since_last_message,
        )
        self.goal_achieved_eval_check = goal_achieved_eval_check
        self.goal_failed_eval_check = goal_failed_eval_check

    def goal_achieved(self) -> bool:
        self.feedback_message = ""
        if self.captured_state is None:
            return False
        eval_check = eval(self.goal_achieved_eval_check, {"state": self.captured_state})
        self.feedback_message = f"Eval check: {eval_check}"
        return eval_check

    def goal_failed(self) -> bool:
        if self.goal_failed_eval_check is None:
            return False
        eval_check = eval(self.goal_failed_eval_check, {"state": self.captured_state})
        self.feedback_message = f"Eval check: {eval_check}"
        return eval_check
