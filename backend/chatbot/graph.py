import os
import sys
import sqlite3
import pandas as pd
import chromadb
from typing import Annotated, TypedDict
from langchain.tools import tool
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings, HuggingFacePipeline
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from langgraph.graph.message import add_messages
from transformers import pipeline, GPT2Tokenizer

# Fix for SQLite on Mac
if sys.platform.startswith('darwin'):
    try:
        __import__('pysqlite3')
        sys.modules['sqlite3'] = sys.modules['pysqlite3']
    except ImportError:
        pass

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(os.path.dirname(BASE_DIR), "TestTCS.db")
CHROMA_PATH = os.path.join(os.path.dirname(BASE_DIR), "chroma_db")
PDF_PATH = os.path.join(os.path.dirname(BASE_DIR), "Customer-Service-Policy.pdf")

# Initialize LLM
pipe = pipeline("text-generation", model="gpt2", max_new_tokens=100)
llm = HuggingFacePipeline(pipeline=pipe)

# Tools
@tool
def get_user_ticker(user_id: str):
    """Fetch user ticket history from database."""
    conn = sqlite3.connect(DB_PATH)
    query = f"SELECT * FROM ticket_history WHERE user_id = '{user_id}'"
    result_df = pd.read_sql_query(query, conn)
    conn.close()
    return result_df.to_string()

@tool
def get_user_info(user_id: str):
    """Fetch user personal information from database."""
    conn = sqlite3.connect(DB_PATH)
    query = f"SELECT * FROM Customers WHERE user_id = '{user_id}'"
    result_df = pd.read_sql_query(query, conn)
    conn.close()
    return result_df.to_string()

@tool
def search_bank_policy(query: str) -> str:
    """Search the official Bank Anti-Fraud Policy documentation."""
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    chroma_client = chromadb.PersistentClient(path=CHROMA_PATH)
    vector_db = Chroma(
        client=chroma_client,
        embedding_function=embeddings,
        collection_name="CS_policies"
    )
    docs = vector_db.similarity_search(query, k=1)
    return docs[0].page_content if docs else "No relevant policy found."

# Prompt Template
template = """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

prompt = PromptTemplate.from_template(template)

# Executors
Policy_executor = AgentExecutor(
    agent=create_react_agent(llm, [search_bank_policy], prompt),
    tools=[search_bank_policy],
    handle_parsing_errors=True
)

CS_executor = AgentExecutor(
    agent=create_react_agent(llm, [get_user_ticker, get_user_info], prompt),
    tools=[get_user_ticker, get_user_info],
    handle_parsing_errors=True
)

# Nodes
def policy_node(state):
    user_msg = state["messages"][-1].content
    result = Policy_executor.invoke({"input": user_msg})
    return {"messages": [HumanMessage(content=result["output"], name="Policy_Agent")]}

def cs_node(state):
    user_msg = state["messages"][-1].content
    result = CS_executor.invoke({"input": user_msg})
    return {"messages": [HumanMessage(content=result["output"], name="CS_Agent")]}

# State & Graph
class State(TypedDict):
    messages: Annotated[list, add_messages]
    current_stage: str
    completed_stages: list[str]

def supervisor_node(state: State) -> Command:
    completed = state.get("completed_stages", [])
    current = state.get("current_stage", "")
    if current and current not in completed:
        completed.append(current)
    
    if "Policy Check" not in completed:
        next_stage = "Policy Check"
    elif "Customer Information Check" not in completed:
        next_stage = "Customer Information Check"
    else:
        return Command(goto=END)
    
    return Command(
        goto=next_stage,
        update={"current_stage": next_stage, "completed_stages": completed}
    )

def build_graph():
    builder = StateGraph(State)
    builder.add_node("Policy Check", policy_node)
    builder.add_node("Customer Information Check", cs_node)
    builder.add_node("supervisor", supervisor_node)
    builder.add_edge(START, "supervisor")
    builder.add_edge("Policy Check", "supervisor")
    builder.add_edge("Customer Information Check", "supervisor")
    return builder.compile()

graph = build_graph()
