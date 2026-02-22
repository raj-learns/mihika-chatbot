from fastapi import FastAPI
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from typing import List, TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from typing import Annotated
from fastapi.middleware.cors import CORSMiddleware

memory = MemorySaver()
load_dotenv()
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


llm = ChatOpenAI(
    model="openai/gpt-4o-mini"
)

class Message(BaseModel):
    role: str
    content: str
    thread_id: str
    
class State(TypedDict):
  messages: Annotated[list, add_messages]

def chatbot(state: State) -> State:

    system_prompt = {
        "role": "system",
        "content": """
        You are Mihika, a friendly AI assistant created by Raj.
        Your job is to help users in their day-to-day decisions.
        You speak in a warm, conversational tone.
        Keep answers simple and supportive.
        Details of Raj: 
        He is a 21 yearr old civil engineering student in IIT Ropar.
        He is passionate about learning and exploring new technologies.
        His contact no. is 8683905746.
        Email: 2022ceb1025@iitrpr.ac.in
        """
    }

    messages = [system_prompt] + state["messages"]

    return {"messages": [llm.invoke(messages)]}

    
builder = StateGraph(State)
builder.add_node("chatbot", chatbot)    
builder.add_edge(START, "chatbot")
builder.add_edge("chatbot", END)
graph = builder.compile(checkpointer=memory)

@app.post("/chat")    
def chat(message: Message):
    config = {"configurable" : {"thread_id" : message.thread_id}}
    response = graph.invoke(
    {"messages": [{"role": message.role, "content": message.content}]},
    config=config
)

    return {"messages": response["messages"][-1].content,
            "session_id": message.thread_id
            }




@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/item/{item_id}")
def read_item(item_id: int, q: str = None) :
    return {"game-id": item_id, "query" : q}

# @app.post("/user")
# def create_user(user: User):
#     print(user)
#     return {
#         "message": "User created successfully",
#         "user": user
#     }