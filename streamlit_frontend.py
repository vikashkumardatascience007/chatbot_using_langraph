import streamlit as st
from langgraph_backend import chatbot
from langchain_core.messages import HumanMessage
# mesg_his=[]
thread_id=1
config = {"configurable": {"thread_id": thread_id}}


if 'mesg_his' not in st.session_state:
    st.session_state['mesg_his']=[]

for msg in st.session_state['mesg_his']:
    print(msg,'ppppppppppp')
    with st.chat_message(msg['role']):
        st.text(msg['content'])

user_input=st.chat_input('Type here ')

if user_input:

    # first add message to message history 
    st.session_state['mesg_his'].append({
        'role':'user',
        'content':user_input
      })
    with st.chat_message('user'):
        st.text(user_input)

    res=chatbot.invoke({"messages": [HumanMessage(content=user_input)]}, config=config)
    ai_msg=res['messages'][-1].content

    # first add message to message history 
    st.session_state['mesg_his'].append({
        'role':'assistant',
        'content':ai_msg
      })
    with st.chat_message('assistant'):
        st.text(ai_msg)

