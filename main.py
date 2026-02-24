from fastapi import FastAPI, UploadFile, File
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
from pypdf import PdfReader
from docx import Document

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

# resume reader

class MatchResult(BaseModel):
    match_score: float
    shortlisted: bool
    interview_questions: List[str]

def extract_text(file: UploadFile, content: bytes) :

    filename = file.filename.lower()

    # PDF
    if filename.endswith(".pdf"):
        reader = PdfReader(file.file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text

    # DOCX
    elif filename.endswith(".docx"):
        doc = Document(file.file)
        return "\n".join([p.text for p in doc.paragraphs])

    # TXT fallback
    else:
        return content.decode("utf-8", errors="ignore")
    
resume_store = ""
JD_store = ""

@app.post("/upload_resume")
async def upload_resume(file: UploadFile = File(...)):
    content = await file.read()
    text = extract_text(file, content)
    global resume_store
    resume_store = text
    return {"message": "Resume uploaded successfully"}

@app.post("/upload_jd")
async def upload_jd(file: UploadFile = File(...)):
    content = await file.read()
    text = extract_text(file, content)     
    global JD_store
    JD_store = text
    return {"message": "JD uploaded successfully", "text": text}

def analyze_match(resume_text: str, jd_text: str):

    prompt = f"""
    You are a technical recruiter.

    From the JOB DESCRIPTION extract:
    - A list of required skills (as a Python list).

    From the RESUME extract:
    - A list of candidate skills (as a Python list).

    Then:
    - Provide matched_skills (intersection).
    - Provide missing_skills.
    - Generate 5 interview questions based on JD and missing skills.

    Return strictly in JSON format like:

    {{
        "required_skills": [],
        "candidate_skills": [],
        "matched_skills": [],
        "missing_skills": [],
        "interview_questions": []
    }}

    JOB DESCRIPTION:
    {jd_text}

    RESUME:
    {resume_text}
    """
    response = llm.invoke(prompt)
    content = response.content.strip()
    import re
    import json
    json_match = re.search(r"\{.*\}", content, re.DOTALL)

    if not json_match:
        raise ValueError("AI did not return valid JSON")

    data = json.loads(json_match.group())

    required = data["required_skills"]
    matched = data["matched_skills"]
    print("Required:", required)
    print("Matched:", matched)

    if len(required) == 0:
        score = 0
    else:
        score = (len(matched) / len(required)) * 100

    shortlisted = score >= 60

    return MatchResult(
        match_score=round(score, 2),
        shortlisted=shortlisted,
        interview_questions=data["interview_questions"]
    )
    
@app.get("/compare")
def compare_resume_jd():

    global resume_store, JD_store

    if not resume_store or not JD_store:
        return {"error": "Resume or JD not uploaded"}

    result = analyze_match(resume_store, JD_store)

    return result
