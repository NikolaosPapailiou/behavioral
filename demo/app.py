import asyncio
import time
import uuid
from typing import Any, Dict, List, Optional

import py_trees
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from langchain.chat_models import init_chat_model
from pydantic import BaseModel
from tree_library import tree_creators, tree_descriptions

load_dotenv()

app = FastAPI()
# Enable CORS for all routes and origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Available models
AVAILABLE_MODELS = [
    "google_genai:gemini-2.0-flash-lite",
    "google_genai:gemini-1.5-flash",
    "google_genai:gemini-2.0-flash",
]

# Default model
DEFAULT_MODEL = "google_genai:gemini-2.0-flash-lite"


# Thread manager to handle multiple conversation trees
class ThreadManager:
    def __init__(self):
        self.threads: Dict[str, Any] = {}
        self.last_update_times: Dict[str, float] = {}

        self.available_trees = list(tree_creators.keys())
        self.thread_models: Dict[str, str] = {}  # Track model used by each thread

        # Set py_trees logging level
        py_trees.logging.level = py_trees.logging.Level.DEBUG

        # Tasks dictionary to keep track of running tasks
        self.tasks: Dict[str, asyncio.Task] = {}

    async def create_thread(
        self, tree_type: str, model_name: str = DEFAULT_MODEL
    ) -> str:
        """Create a new conversation thread with the specified tree type and model"""
        if tree_type not in tree_creators:
            raise ValueError(f"Unknown tree type: {tree_type}")

        if model_name not in AVAILABLE_MODELS:
            raise ValueError(f"Unknown model: {model_name}")

        thread_id = str(uuid.uuid4())
        model = init_chat_model(model=model_name)
        tree = await tree_creators[tree_type](model)
        tree.setup()
        tree.visitors.append(py_trees.visitors.DebugVisitor())

        # Start periodic ticking for this tree as an asyncio task
        task = asyncio.create_task(tree.atick_tock(period_ms=30000))
        self.tasks[thread_id] = task

        self.threads[thread_id] = {
            "tree": tree,
            "type": tree_type,
            "created_at": time.time(),
        }
        self.thread_models[thread_id] = model_name
        self.last_update_times[thread_id] = time.time()

        return thread_id

    async def change_model(self, thread_id: str, model_name: str) -> bool:
        """Change the model used by a thread"""
        if thread_id not in self.threads:
            raise ValueError(f"Thread not found: {thread_id}")

        if model_name not in AVAILABLE_MODELS:
            raise ValueError(f"Unknown model: {model_name}")

        # If model is the same, do nothing
        if self.thread_models.get(thread_id) == model_name:
            return False

        # Create a new model and tree
        model = init_chat_model(model=model_name)
        self.threads[thread_id]["tree"].chat_model = model
        self.thread_models[thread_id] = model_name
        self.last_update_times[thread_id] = time.time()

        return True

    def get_thread(self, thread_id: str) -> Any:
        """Get a conversation thread by ID"""
        if thread_id not in self.threads:
            raise ValueError(f"Thread not found: {thread_id}")
        return self.threads[thread_id]["tree"]

    def get_tree_description(self, thread_id: str) -> str:
        """Get a conversation tree description by ID"""
        if thread_id not in self.threads:
            raise ValueError(f"Thread not found: {thread_id}")
        if "type" not in self.threads[thread_id]:
            raise ValueError("Thread has no tree type")
        type = self.threads[thread_id]["type"]
        if type not in tree_descriptions:
            return "No description"
        else:
            return tree_descriptions[type]

    def get_thread_model(self, thread_id: str) -> str:
        """Get the model used by a thread"""
        if thread_id not in self.thread_models:
            raise ValueError(f"Thread not found: {thread_id}")
        return self.thread_models.get(thread_id, DEFAULT_MODEL)

    async def delete_thread(self, thread_id: str) -> bool:
        """Delete a conversation thread"""
        if thread_id not in self.threads:
            return False

        # Cancel the associated task if it exists
        if thread_id in self.tasks:
            self.tasks[thread_id].cancel()
            try:
                await self.tasks[thread_id]
            except asyncio.CancelledError:
                pass
            del self.tasks[thread_id]

        # Remove the thread
        del self.threads[thread_id]
        if thread_id in self.last_update_times:
            del self.last_update_times[thread_id]
        if thread_id in self.thread_models:
            del self.thread_models[thread_id]

        return True

    def list_threads(self) -> List[Dict]:
        """List all active conversation threads"""
        return [
            {
                "id": thread_id,
                "type": thread_info["type"],
                "model": self.thread_models.get(thread_id, DEFAULT_MODEL),
                "created_at": thread_info["created_at"],
                "last_update": self.last_update_times.get(
                    thread_id, thread_info["created_at"]
                ),
            }
            for thread_id, thread_info in self.threads.items()
        ]

    def update_last_time(self, thread_id: str):
        """Update the last update time for a thread"""
        if thread_id in self.threads:
            self.last_update_times[thread_id] = time.time()


# Initialize the thread manager
thread_manager = ThreadManager()


# Pydantic models for request validation
class ThreadCreate(BaseModel):
    tree_type: str = "react"
    model_name: str = DEFAULT_MODEL


class ModelChange(BaseModel):
    model_name: str


class MessageSend(BaseModel):
    content: str
    thread_id: Optional[str] = None


@app.get("/api/threads")
async def list_threads():
    """List all active conversation threads"""
    return {
        "threads": thread_manager.list_threads(),
        "available_trees": thread_manager.available_trees,
        "available_models": AVAILABLE_MODELS,
    }


@app.post("/api/threads")
async def create_thread(request: ThreadCreate):
    """Create a new conversation thread"""
    try:
        thread_id = await thread_manager.create_thread(
            request.tree_type, request.model_name
        )
        return {"thread_id": thread_id, "status": "success"}
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=400, detail=str(e))


@app.put("/api/threads/{thread_id}/model")
async def change_model(thread_id: str, request: ModelChange):
    """Change the model for a conversation thread"""
    try:
        success = await thread_manager.change_model(thread_id, request.model_name)
        return {"status": "success", "changed": success}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/models")
async def get_models():
    """Get available models"""
    return {"models": AVAILABLE_MODELS, "default": DEFAULT_MODEL}


@app.delete("/api/threads/{thread_id}")
async def delete_thread(thread_id: str):
    """Delete a conversation thread"""
    success = await thread_manager.delete_thread(thread_id)
    if success:
        return {"status": "success"}
    else:
        raise HTTPException(status_code=404, detail="Thread not found")


@app.post("/api/send-message")
async def send_message(message: MessageSend):
    if not message.thread_id:
        raise HTTPException(status_code=404, detail=str("No valid thread id."))

    print(f"Received message for thread {message.thread_id}: {message.content}")

    try:
        tree = thread_manager.get_thread(message.thread_id)
        tree.add_user_message(message.content)
        thread_manager.update_last_time(message.thread_id)

        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/state")
async def get_state(thread_id: Optional[str] = None):
    """
    Get the complete state in a single request:
    - Chat history
    - Blackboard state
    - Tree structure
    - Last update timestamp
    """
    if not thread_id:
        raise HTTPException(status_code=404, detail=str("No valid thread id."))

    try:
        tree = thread_manager.get_thread(thread_id)
        last_update_time = thread_manager.last_update_times.get(thread_id)
        model_name = thread_manager.get_thread_model(thread_id)

        # Convert chat history to a serializable format
        chat_history = []
        for msg in tree.get_chat_history():
            chat_history.append(
                {
                    "role": msg.role,
                    "content": msg.content,
                    "metadata": {
                        "time": msg.metadata.get("time", 0),
                        "completed": msg.metadata.get("completed", False),
                    },
                }
            )

        # Combine all state in one response
        state = {
            "description": thread_manager.get_tree_description(thread_id),
            "chat_history": chat_history,
            "blackboard": tree.bb.debug_json(),
            "tree_html": tree.html_tree(),
            "last_update": last_update_time,
            "thread_id": thread_id,
            "model": model_name,
        }

        return state
    except ValueError as e:
        print(e)
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/last-update-time")
async def get_last_update_time(thread_id: Optional[str] = None):
    """Simple endpoint to check if state has changed"""
    if not thread_id:
        raise HTTPException(status_code=404, detail=str("No valid thread id."))

    try:
        last_update_time = thread_manager.last_update_times.get(thread_id)
        return {"last_update": last_update_time, "thread_id": thread_id}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# Keep the individual endpoints for compatibility
@app.get("/api/chat-history")
async def get_chat_history(thread_id: Optional[str] = None):
    if not thread_id:
        raise HTTPException(status_code=404, detail=str("No valid thread id."))

    try:
        tree = thread_manager.get_thread(thread_id)
        chat_history = []
        for msg in tree.get_chat_history():
            chat_history.append(
                {
                    "role": msg.role,
                    "content": msg.content,
                    "metadata": {
                        "time": msg.metadata.get("time", 0),
                        "completed": msg.metadata.get("completed", False),
                    },
                }
            )
        return chat_history
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/blackboard-state")
async def get_blackboard_state(thread_id: Optional[str] = None):
    if not thread_id:
        raise HTTPException(status_code=404, detail=str("No valid thread id."))

    try:
        tree = thread_manager.get_thread(thread_id)
        return tree.bb._bb.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/tree-structure")
async def get_tree_structure(thread_id: Optional[str] = None):
    if not thread_id:
        raise HTTPException(status_code=404, detail=str("No valid thread id."))

    try:
        tree = thread_manager.get_thread(thread_id)
        return {"html": tree.html_tree()}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


if __name__ == "__main__":
    import uvicorn

    print("Starting the server...")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
