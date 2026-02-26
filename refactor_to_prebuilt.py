import json
import os

notebook_path = '/Users/saimzafar2002-apple.com/Desktop/TCS/TCS_test.ipynb'

with open(notebook_path, 'r') as f:
    nb = json.load(f)

# 1. Update Agent Initialization Cell
agent_init_cell_content = [
    "from langgraph.prebuilt import create_react_agent\n",
    "from langchain_core.messages import HumanMessage, SystemMessage\n",
    "\n",
    "# Revised Prompts\n",
    "Policy_Prompt = \"You are a Policy Expert. Your goal is to find the most relevant bank policy for the user's ticket.\"\n",
    "CS_Prompt = \"You are a Customer Service Agent. Your goal is to provide a quick overview of the customer's profile and past support ticket details.\"\n",
    "\n",
    "# Tools\n",
    "Policy_tools = [search_bank_policy]\n",
    "CS_tools = [get_user_ticker, get_user_info]\n",
    "\n",
    "# Initialize Agents using Prebuilt LangGraph React Agent\n",
    "# This replaces AgentExecutor which was missing in this environment\n",
    "Policy_agent_node = create_react_agent(llm, Policy_tools, state_modifier=Policy_Prompt)\n",
    "CS_agent_node = create_react_agent(llm, CS_tools, state_modifier=CS_Prompt)\n",
    "\n",
    "# Wrapper nodes to ensure correct State handling if needed\n",
    "def policy_node(state: State):\n",
    "    # create_react_agent expects a state with 'messages'\n",
    "    return Policy_agent_node.invoke(state)\n",
    "\n",
    "def cs_node(state: State):\n",
    "    return CS_agent_node.invoke(state)"
]

# 2. Update Orchestrator Cell (Ensuring correct node names and rule-based logic)
orchestrator_cell_content = [
    "from __future__ import annotations\n",
    "from typing import Annotated, Literal, TypedDict\n",
    "from langgraph.graph import StateGraph, START, END\n",
    "from langgraph.types import Command\n",
    "from langgraph.graph.message import add_messages\n",
    "\n",
    "class State(TypedDict):\n",
    "    messages: Annotated[list, add_messages]\n",
    "    current_stage: str\n",
    "    completed_stages: list[str]\n",
    "    session_id: str \n",
    "\n",
    "def supervisor_node(state: State) -> Command:\n",
    "    \"\"\"Rule-based supervisor for reliable flow.\"\"\"\n",
    "    completed = state.get(\"completed_stages\", [])\n",
    "    current = state.get(\"current_stage\", \"\")\n",
    "    \n",
    "    if current and current not in completed:\n",
    "        completed.append(current)\n",
    "    \n",
    "    # Logic flow: Policy Check -> Customer Information Check\n",
    "    if \"Policy Check\" not in completed:\n",
    "        next_stage = \"Policy Check\"\n",
    "    elif \"Customer Information Check\" not in completed:\n",
    "        next_stage = \"Customer Information Check\"\n",
    "    else:\n",
    "        print(f\"🎉 All stages completed! Ending workflow. (Session: {state.get('session_id')})\")\n",
    "        return Command(goto=END)\n",
    "    \n",
    "    print(f\"🔄 Supervisor moving to: {next_stage}\")\n",
    "    return Command(\n",
    "        goto=next_stage,\n",
    "        update={\n",
    "            \"current_stage\": next_stage,\n",
    "            \"completed_stages\": completed\n",
    "        }\n",
    "    )\n",
    "\n",
    "def build_graph():\n",
    "    builder = StateGraph(State)\n",
    "    \n",
    "    # Add nodes\n",
    "    builder.add_node(\"Policy Check\", policy_node)\n",
    "    builder.add_node(\"Customer Information Check\", cs_node)\n",
    "    builder.add_node(\"supervisor\", supervisor_node)\n",
    "    \n",
    "    # Add edges\n",
    "    builder.add_edge(START, \"supervisor\")\n",
    "    builder.add_edge(\"Policy Check\", \"supervisor\")\n",
    "    builder.add_edge(\"Customer Information Check\", \"supervisor\")\n",
    "    \n",
    "    return builder.compile()\n",
    "\n",
    "graph = build_graph()"
]

# Replacement Logic
# We'll look for the cells we recently modified (they might have specific IDs or content)
for i, cell in enumerate(nb['cells']):
    # Look for the agent initialization cell
    if 'create_react_agent' in ''.join(cell['source']) or 'AgentExecutor' in ''.join(cell['source']):
        if 'Policy_executor' in ''.join(cell['source']) or 'Policy_agent_node' in ''.join(cell['source']):
             nb['cells'][i]['source'] = agent_init_cell_content
    
    # Look for the orchestrator cell
    if 'def supervisor_node(state: State)' in ''.join(cell['source']):
        nb['cells'][i]['source'] = orchestrator_cell_content

with open(notebook_path, 'w') as f:
    json.dump(nb, f, indent=1)

print("Successfully refactored to use langgraph.prebuilt.create_react_agent in TCS_test.ipynb")
