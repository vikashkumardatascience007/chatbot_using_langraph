

import json
import sqlite3
import requests
from typing import TypedDict, Annotated

from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.checkpoint.sqlite import SqliteSaver

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import tool
from langchain_community.chat_models import ChatOllama
from langchain_community.tools import DuckDuckGoSearchRun

load_dotenv()

# --------------------------------------------------
# 1. LLM (Ollama)
# --------------------------------------------------
llm = ChatOllama(
    model="mistral:latest",
    temperature=0.2
)

# --------------------------------------------------
# 2. Tools
# --------------------------------------------------
search_tool = DuckDuckGoSearchRun(region="us-en")


@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Perform a basic arithmetic operation.
    Supported operations: add, sub, mul, div
    """
    try:
        if operation == "add":
            result = first_num + second_num
        elif operation == "sub":
            result = first_num - second_num
        elif operation == "mul":
            result = first_num * second_num
        elif operation == "div":
            if second_num == 0:
                return {"error": "Division by zero"}
            result = first_num / second_num
        else:
            return {"error": "Unsupported operation"}

        return {"result": result}
    except Exception as e:
        return {"error": str(e)}


@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a symbol (AAPL, TSLA, etc.)
    """
    url = (
        "https://www.alphavantage.co/query"
        f"?function=GLOBAL_QUOTE&symbol={symbol}&apikey=C9PE94QUEW9VWGFM"
    )
    return requests.get(url).json()


TOOLS = {
    "calculator": calculator,
    "get_stock_price": get_stock_price,
    "search": search_tool,
}

# --------------------------------------------------
# 3. State
# --------------------------------------------------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# --------------------------------------------------
# 4. System Prompt (CRITICAL)
# --------------------------------------------------
SYSTEM_PROMPT = """
You are a tool-using assistant.

If a tool is needed, respond ONLY in valid JSON:

{
  "tool": "<tool_name>",
  "args": { ... }
}

If no tool is needed, respond ONLY in JSON:

{
  "tool": null,
  "response": "<final answer>"
}

Available tools:
- calculator(first_num, second_num, operation)
- get_stock_price(symbol)
- search(query)

Rules:
- NO extra text
- NO markdown
- ONLY JSON
"""

# --------------------------------------------------
# 5. Chat Node (LLM decides)
# --------------------------------------------------
def chat_node(state: ChatState):
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}

# --------------------------------------------------
# 6. Tool Router Node (Manual)
# --------------------------------------------------
def tool_node(state: ChatState):
    last_msg = state["messages"][-1].content

    try:
        data = json.loads(last_msg)
    except json.JSONDecodeError:
        return state  # fail safely

    tool_name = data.get("tool")
    if not tool_name:
        return state

    tool = TOOLS.get(tool_name)
    if not tool:
        return state

    result = tool.invoke(data.get("args", {}))

    return {
        "messages": state["messages"] + [
            HumanMessage(content=f"Tool result: {result}")
        ]
    }

# --------------------------------------------------
# 7. Condition: Do we need a tool?
# --------------------------------------------------
def needs_tool(state: ChatState):
    try:
        data = json.loads(state["messages"][-1].content)
        return data.get("tool") is not None
    except Exception:
        return False

# --------------------------------------------------
# 8. Checkpointer
# --------------------------------------------------
conn = sqlite3.connect("chatbot.db", check_same_thread=False)
checkpointer = SqliteSaver(conn)

# --------------------------------------------------
# 9. Graph
# --------------------------------------------------
graph = StateGraph(ChatState)

graph.add_node("chat", chat_node)
graph.add_node("tool", tool_node)

graph.add_edge(START, "chat")

graph.add_conditional_edges(
    "chat",
    needs_tool,
    {
        True: "tool",
        False: END
    }
)

graph.add_edge("tool", "chat")

chatbot = graph.compile(checkpointer=checkpointer)

# --------------------------------------------------
# 10. Run helper
# --------------------------------------------------
def run_chat(user_input: str, thread_id: str = "default"):
    result = chatbot.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config={"configurable": {"thread_id": thread_id}},
    )
    return result["messages"][-1].content
