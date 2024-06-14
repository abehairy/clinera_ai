# Import relevant functionality
from langchain_anthropic import ChatAnthropic
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.prebuilt import create_react_agent
from data_api_crawler import search_clinical_trials
from dotenv import load_dotenv
load_dotenv()


# Create the agent
memory = SqliteSaver.from_conn_string(":memory:")
model = ChatAnthropic(model_name="claude-3-sonnet-20240229")
search = TavilySearchResults(max_results=2)
tools = [search_clinical_trials]
agent_executor = create_react_agent(model, tools, checkpointer=memory)

# Use the agent
config = {"configurable": {"thread_id": "abc123"}}
for chunk in agent_executor.stream(
    {"messages": [HumanMessage(content="get the latest clinical trial study details on trastuzumab?")]}, config
):
    print(chunk)
    print("----")

# for chunk in agent_executor.stream(
#     {"messages": [HumanMessage(content="whats the weather where I live?")]}, config
# ):
#     print(chunk)
#     print("----")