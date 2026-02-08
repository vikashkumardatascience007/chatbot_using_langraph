import os
import asyncio
import re
from typing import TypedDict, Annotated

# SSL FIX (MUST BE FIRST)
os.environ.pop("SSL_CERT_FILE", None)
os.environ["OLLAMA_HOST"] = "http://localhost:11434"

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.tools import tool
from langchain_ollama import ChatOllama


# Local offline Ollama
llm = ChatOllama(
    model="mistral:latest",
    temperature=0.2
)

# ---------------- TOOLS ----------------

@tool
def calculator(first_num: float, second_num: float, operation: str) -> dict:
    """
    Supported operations: add, sub, mul, div, mod
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
        elif operation == "mod":
            result = first_num % second_num
        else:
            return {"error": f"Unsupported operation '{operation}'"}

        return {"result": result}

    except Exception as e:
        return {"error": str(e)}


# ---------------- STATE ----------------

class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# ---------------- GRAPH ----------------

def build_graph():

    async def chat_node(state: ChatState):
        response = await llm.ainvoke(state["messages"])
        return {"messages": [response]}

    async def tool_router(state: ChatState):
        last_msg = state["messages"][-1].content

        match = re.search(r"modulus of (\d+) and (\d+)", last_msg, re.I)
        if not match:
            return {}

        a, b = map(float, match.groups())

        result = calculator.invoke({
            "first_num": a,
            "second_num": b,
            "operation": "mod"
        })

        commentary = (
            f"And that’s a beauty! 🎯 "
            f"{int(a)} mod {int(b)} is **{int(result['result'])}**! "
            f"Right off the middle of the bat!"
        )

        return {
            "messages": [AIMessage(content=commentary)]
        }

    graph = StateGraph(ChatState)

    graph.add_node("chat", chat_node)
    graph.add_node("tool_router", tool_router)

    graph.add_edge(START, "chat")
    graph.add_edge("chat", "tool_router")

    return graph.compile()


# ---------------- RUN ----------------

async def main():
    chatbot = build_graph()

    result = await chatbot.ainvoke({
        "messages": [
            HumanMessage(
                content="Find the modulus of 132354 and 23 and give answer like a cricket commentator."
            )
        ]
    })

    print(result["messages"][-1].content)


if __name__ == "__main__":
    asyncio.run(main())
