import json
import os

notebook_path = '/Users/saimzafar2002-apple.com/Desktop/TCS/TCS_test.ipynb'

with open(notebook_path, 'r') as f:
    nb = json.load(f)

# ReAct logic to be inserted into the notebook
agent_nodes_content = [
    "from langchain_classic.agents import AgentExecutor, create_react_agent\n",
    "from langchain_core.prompts import PromptTemplate\n",
    "from langchain_core.messages import HumanMessage\n",
    "\n",
    "template = \"\"\"You are a helpful assistant. Use tools if necessary.\n",
    "\n",
    "Tools:\n",
    "{tools}\n",
    "\n",
    "Format:\n",
    "Thought: what to do\n",
    "Action: one of [{tool_names}]\n",
    "Action Input: input\n",
    "Observation: result\n",
    "... (repeat as needed)\n",
    "Thought: final answer\n",
    "Final Answer: final response\n",
    "\n",
    "Begin!\n",
    "Question: {input}\n",
    "Thought: {agent_scratchpad}\"\"\"\n",
    "\n",
    "prompt = PromptTemplate.from_template(template)\n",
    "\n",
    "# Define executors (manual ReAct loop)\n",
    "Policy_executor = AgentExecutor(\n",
    "    agent=create_react_agent(llm, [search_bank_policy], prompt),\n",
    "    tools=[search_bank_policy],\n",
    "    verbose=True,\n",
    "    handle_parsing_errors=True\n",
    ")\n",
    "\n",
    "CS_executor = AgentExecutor(\n",
    "    agent=create_react_agent(llm, [get_user_ticker, get_user_info], prompt),\n",
    "    tools=[get_user_ticker, get_user_info],\n",
    "    verbose=True,\n",
    "    handle_parsing_errors=True\n",
    ")\n",
    "\n",
    "def policy_node(state: State):\n",
    "    user_msg = state[\"messages\"][-1].content\n",
    "    result = Policy_executor.invoke({\"input\": user_msg})\n",
    "    return {\"messages\": [HumanMessage(content=result[\"output\"], name=\"Policy_Agent\")]}\n",
    "\n",
    "def cs_node(state: State):\n",
    "    user_msg = state[\"messages\"][-1].content\n",
    "    result = CS_executor.invoke({\"input\": user_msg})\n",
    "    return {\"messages\": [HumanMessage(content=result[\"output\"], name=\"CS_Agent\")]}"
]

patched = False
for i, cell in enumerate(nb['cells']):
    source_str = ''.join(cell['source'])
    if 'from langchain_classic.agents import AgentExecutor' in source_str or 'Policy_executor = AgentExecutor' in source_str or 'from langchain.agents import AgentExecutor' in source_str:
        nb['cells'][i]['source'] = agent_nodes_content
        patched = True
        break

if not patched:
    for i, cell in enumerate(nb['cells']):
         if 'def supervisor_node' in ''.join(cell['source']):
             nb['cells'].insert(i, {"cell_type": "code", "metadata": {}, "source": agent_nodes_content, "id": "react_nodes_inserted"})
             patched = True
             break

with open(notebook_path, 'w') as f:
    json.dump(nb, f, indent=1)

if patched:
    print("Successfully patched TCS_test.ipynb with corrected langchain_classic ReAct logic.")
else:
    print("Could not find a suitable location to patch the notebook.")