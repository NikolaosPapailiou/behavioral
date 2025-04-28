import asyncio
import threading
import time
from typing import Callable, Dict, Literal, Optional

import py_trees
from langchain_core.language_models.chat_models import BaseChatModel
from pydantic import BaseModel, Field

from behavioral.blackboard import BlackBoard


class ChatMessage(BaseModel):
    content: str
    role: Literal["user", "assistant", "system"] = "assistant"
    metadata: Dict


class ConversationState(BaseModel):
    """
    State of the conversation.
    """

    user_wants_to_end_conversation: bool = Field(
        title="User Wants to End Conversation",
        description="True, if the user wants to end the conversation.",
    )
    user_is_objecting_assistant: bool = Field(
        title="User is Objecting Assistant",
        description="True, user is objecting the current goal of the assistant?.",
    )
    user_engagement: float = Field(
        title="User Engagement",
        description="How engaged is the user? 0.0 is not engaged, 1.0 is fully engaged. Pick the most appropriate value in between based on the conversation history. Values below 0.4 mean that the AI Agent should try to re-engage the user.",
    )


class ConversationBehaviourTree(py_trees.trees.BehaviourTree):
    @staticmethod
    def create_conversation_flow(
        root: py_trees.behaviour.Behaviour,
        conversation_state_type: type = None,
        capture_state_on_assistant_message: bool = False,
    ):
        from behavioral import behaviors

        if conversation_state_type is None:
            return root

        conversation_with_state = py_trees.composites.Parallel(
            "conversation_with_state",
            policy=py_trees.common.ParallelPolicy.SuccessOnAll(synchronise=False),
        )
        capture_conversation_state = behaviors.CaptureConversationState(
            "capture_conversation_state",
            state_key="conversation_state",
            capture_state_type=conversation_state_type,
            capture_assistant_message=capture_state_on_assistant_message,
        )
        conversation_with_state.add_children([capture_conversation_state, root])
        return conversation_with_state

    def __init__(
        self,
        root: py_trees.behaviour.Behaviour,
        conversation_goal_prompt: str,
        chat_model: BaseChatModel,
        conversation_state_type: type = None,
        capture_state_on_assistant_message: bool = False,
        message_history: int = 10,
        namespace: str = None,
    ):
        super().__init__(
            ConversationBehaviourTree.create_conversation_flow(
                root=root,
                conversation_state_type=conversation_state_type,
                capture_state_on_assistant_message=capture_state_on_assistant_message,
            )
        )
        self.conversation_goal_prompt = conversation_goal_prompt
        self.chat_model = chat_model
        self.conversation_state_type = conversation_state_type
        self.capture_state_on_assistant_message = capture_state_on_assistant_message
        self.message_history = message_history
        self.chat_history = []
        self.namespace = namespace
        self.bb = BlackBoard()
        self.sleep_event = asyncio.Event()
        self.capture_state_running = False
        self.tick_lock = threading.Lock()
        self.last_message_time = time.time()
        self.start_time = time.time()
        self.ticks = 0
        self.logger = py_trees.logging.Logger(self.__class__.__name__)

    def setup(self) -> None:
        super().setup(namespace=self.namespace, conversation_tree=self)

    def add_user_message(self, message: str):
        self.last_message_time = time.time()
        self.chat_history.append(
            ChatMessage(
                role="user", content=message, metadata={"time": self.last_message_time}
            )
        )
        self.wakeup()

    # Multithreaded set event
    def wakeup(self):
        with self.tick_lock:
            self.loop.call_soon_threadsafe(self.sleep_event.set)

    def get_chat_history(self):
        return self.chat_history

    def has_pending_user_message(self):
        return len(self.chat_history) > 0 and self.chat_history[-1].role == "user"

    def get_last_user_message_time(self):
        return self.chat_history[-1].metadata["time"]

    def add_assistant_message(self) -> ChatMessage:
        self.last_message_time = time.time()
        message = ChatMessage(
            role="assistant",
            content="",
            metadata={"time": self.last_message_time, "completed": False},
        )
        self.chat_history.append(message)
        return message

    def get_active_chat_history(self):
        return self.chat_history[-self.message_history :]

    async def atick_tock(
        self,
        period_ms: int,
        number_of_iterations: int = py_trees.trees.CONTINUOUS_TICK_TOCK,
        pre_tick_handler: Optional[
            Callable[[py_trees.trees.BehaviourTree], None]
        ] = None,
        post_tick_handler: Optional[
            Callable[[py_trees.trees.BehaviourTree], None]
        ] = None,
    ) -> None:
        tick_tocks = 0
        self.loop = asyncio.get_running_loop()
        while not self.interrupt_tick_tocking and (
            tick_tocks < number_of_iterations
            or number_of_iterations == py_trees.trees.CONTINUOUS_TICK_TOCK
        ):
            self.tick(pre_tick_handler, post_tick_handler)
            try:
                with self.tick_lock:
                    self.sleep_event.clear()
                try:
                    async with asyncio.timeout(period_ms / 1000.0):
                        await self.sleep_event.wait()
                except TimeoutError:
                    pass
            except KeyboardInterrupt:
                break
            tick_tocks += 1
        self.interrupt_tick_tocking = False

    def tick(self, pre_tick_handler=None, post_tick_handler=None) -> None:
        tick_time = time.time()
        self.logger.debug(f"Tick #{self.ticks} seconds: {tick_time - self.start_time}")
        self.capture_state_running = False
        super().tick(
            pre_tick_handler=pre_tick_handler, post_tick_handler=post_tick_handler
        )
        self.ticks += 1

    def html_tree(self, max_height: int = None) -> str:
        debug_tree = py_trees.display.xhtml_tree(
            self.root,
            show_status=True,
        )
        prefix = "<div style='font-size:11px;"
        if max_height is not None:
            prefix += "max-height:" + str(max_height)
        return (
            prefix
            # + "px;overflow:auto;'><h2>Behavior Tree</h2><br>"
            + "px;overflow:auto;'><br>"
            + debug_tree
            + "</div>"
        )

    def debug_blackboard(self) -> str:
        ret = "## BlackBoard\n"
        for key in self.bb.keys():
            ret += "### " + key + "\n"
            value = self.bb.get_value(key)
            if value is not None:
                ret += "```\n" + str(value.model_dump_json(indent=2)) + "\n```\n"
        return ret
