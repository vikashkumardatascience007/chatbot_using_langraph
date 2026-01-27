from langgraph.graph import StateGraph, START, END
from typing import TypedDict, Annotated
from langchain_core.messages import BaseMessage,HumanMessage
from langchain_community.chat_models import ChatOllama
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import InMemorySaver

class ChatState(TypedDict):
    messages:Annotated[list[BaseMessage], add_messages]

llm=ChatOllama(model="mistral:latest",temperature=0.2)

def chat_node(state:ChatState):

    # take user uery state
    messages=state['messages']

    # send to llm
    response=llm.invoke(messages)

    # response store state
    return {'messages':[response]}

checkpointer = MemorySaver()

graph = StateGraph(ChatState)
graph.add_node("chat_node", chat_node)
graph.add_edge(START, "chat_node")
graph.add_edge("chat_node", END)

chatbot = graph.compile(checkpointer=checkpointer)

thread_id = "1"
