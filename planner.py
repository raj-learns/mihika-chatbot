from dotenv import load_dotenv
import os
import json
from typing import Annotated
from langchain.chat_models import init_chat_model
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate

    
load_dotenv()


# loader = PyPDFLoader("Biopolymers-BD-1.pdf")
# docs = loader.load()


# splitter = RecursiveCharacterTextSplitter(
#     chunk_size=1000,
#     chunk_overlap=200
# )

# chunks = splitter.split_documents(docs)


# embeddings = OpenAIEmbeddings()

# db = FAISS.from_documents(chunks, embeddings)

# retriever = db.as_retriever()

# docs = retriever.invoke("How to prepare for exam?")


class State(TypedDict):
    goal: str
    steps: List[str]
    intent: str
    confidence: float
    
class IntentDetection(BaseModel):
    intent: str = Field(description="The intent of the user input from the following 'complex task' or 'simple task'" )
    confidence: float = Field(description="The confidence score of the intent detection, between 0 and 1") 

llm = ChatOpenAI(
    model="openai/gpt-4o-mini"
)
initial_state = {
    "goal": input("Task: "),
    "steps": []
}

llm2 = llm.with_structured_output(IntentDetection)

prompt = ChatPromptTemplate.from_template(
    f"""Extract the desired information from the following query
    Only extract the property mentioned in the IntentDetection class
    Queey:
    {initial_state['goal']}
    """)

def detect_intent(state: State) -> IntentDetection:
    response = llm2.invoke(prompt.format(goal=state["goal"]))
    return {"intent" : response.intent, "confidence": response.confidence}

def generate_plan_complex(state: State) -> State:
    if not state["goal"]:
        return state
    try:
        # context = "\n".join([doc.page_content for doc in docs])
        # response = llm.invoke([
        #     {"role": "system", "content": "Answer based only on given context."},
        #     {"role": "user", "content": f"Context:\n{context}\n\nQuestion: What will be steps to prepare for the exam, means topics needed to study? Return ONLY a JSON object with key steps containing a list of strings. Le me know if you are not getting context."}
        #         ])

        response = llm.invoke(
            [
                {"role": "system", "content": "You are a helpful assistant that creates a plan to complete the task. We want structured output, i.e. a list of steps to complete the task. Thats all you need to do. If the same goal is given steps should be same. If the goal is different, steps should be different. Do not add any extra information. Do not add any explanation. Just give the steps to complete the task. Return ONLY a JSON object with key steps containing a list of strings."},
                {"role": "user", "content": f"Create a plan to complete the following task: {state['goal']}"}
            ]
        )
        try:
            state["steps"] = json.loads(response.content).get("steps", [])
            return state
        except json.JSONDecodeError:
            print("Failed to parse JSON response. Response content:", response.content)
            return state
    except Exception as e:
        print(f"Error generating plan: {e}")
    return state


def generate_plan_simple(state: State) -> State:
    if not state["goal"]:
        return state
    try:
        # context = "\n".join([doc.page_content for doc in docs])
        # response = llm.invoke([
        #     {"role": "system", "content": "Answer based only on given context."},
        #     {"role": "user", "content": f"Context:\n{context}\n\nQuestion: What will be steps to prepare for the exam, means topics needed to study? Return ONLY a JSON object with key steps containing a list of strings. Le me know if you are not getting context."}
        #         ])

        response = llm.invoke(
            [
                {"role": "system", "content": "You are a helpful assistant that creates a plan to complete the task. We want structured output, i.e. a list of steps to complete the task. Steps dhould be 0f 4-5 words. Do not add any explanation. Just give the steps to complete the task. Return ONLY a JSON object with key steps containing a list of strings."},
                {"role": "user", "content": f"Create a plan to complete the following task: {state['goal']}"}
            ]
        )
        try:
            state["steps"] = json.loads(response.content).get("steps", [])
            return state
        except json.JSONDecodeError:
            print("Failed to parse JSON response. Response content:", response.content)
            return state
    except Exception as e:
        print(f"Error generating plan: {e}")
    return state

def route_intent(intent: IntentDetection):
    return intent.intent


builder = StateGraph(State)

builder.add_node("planner", generate_plan_complex)
builder.add_node("simple_planner", generate_plan_simple)
builder.add_node("intent_detection", detect_intent)
builder.add_edge(START, "intent_detection")
builder.add_conditional_edges(
    "intent_detection",
    route_intent,
    {
        "complex task": "planner",
        "simple task": "simple_planner"
    }
)

builder.add_edge("planner", END)
builder.add_edge("simple_planner", END)

graph = builder.compile()
result = graph.invoke(initial_state)
steps = result["steps"]

    
for i, step in enumerate(steps, 1):
    print(f"Step {i}: {step}")
