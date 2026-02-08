import os
import asyncio
from typing import TypedDict, Annotated
import sys

# -------- ENV FIX --------
os.environ.pop("SSL_CERT_FILE", None)
os.environ["OLLAMA_HOST"] = "http://localhost:11434"

from langgraph.graph import StateGraph, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_ollama import ChatOllama
from langchain_mcp_adapters.client import MultiServerMCPClient

# -------- LLM --------
llm = ChatOllama(
    model="mistral:latest",
    temperature=0.2
)

# -------- MCP CLIENT --------
client = MultiServerMCPClient(
    {
        "arith": {
            "transport": "stdio",
            "command": sys.executable,
            "args": ["mcp-client-and-server-langgraph/calculator_mcp_server.py"],
        },
        "expense": {
            "transport": "streamable_http",   
            "url": "https://splendid-gold-dingo.fastmcp.app/mcp"
        }
    }
)

# -------- STATE --------
class ChatState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

# -------- GRAPH --------
async def build_graph():
    tools = await client.get_tools()
    print(tools,'tuissdijfspsvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvvv')
    llm_with_tools = llm.bind_tools(tools)

    async def chat_node(state: ChatState):
        response = await llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}

    graph = StateGraph(ChatState)

    graph.add_node("chat", chat_node)
    graph.add_node("tools", ToolNode(tools))

    graph.add_edge(START, "chat")
    graph.add_conditional_edges("chat", tools_condition)
    graph.add_edge("tools", "chat")

    return graph.compile()

# -------- RUN --------
async def main():
    chatbot = await build_graph()

    result = await chatbot.ainvoke(
        {
            "messages": [
                HumanMessage(
                    content=(
                        "Find the addition of 3 and 7 "
                        "and explain it like a cricket commentator"
                    )
                )
            ]
        }
    )

    print("\n🏏 ANSWER:\n")
    print(result["messages"][-1].content)

if __name__ == "__main__":
    import sys
    asyncio.run(main())
