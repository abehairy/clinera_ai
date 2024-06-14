import yaml
from langchain.requests import RequestsWrapper
from langchain.agents.agent_toolkits.openapi.spec import reduce_openapi_spec
from langchain_openai import ChatOpenAI
from langchain.agents.agent_toolkits.openapi import planner
from dotenv import load_dotenv
import os

# Constants
MODEL = 'gpt-4'

# Load environment variables
load_dotenv()

# Initialize the ChatOpenAI model
llm = ChatOpenAI(model=MODEL, verbose=True)


def load_api_spec(yaml_path):
    """Load and reduce an OpenAPI spec from a YAML file."""
    with open(yaml_path) as f:
        safe_api_spec = yaml.safe_load(f)
    return reduce_openapi_spec(safe_api_spec)


def construct_headers(raw_spec):
    """Construct API headers from the spec. Modify this to extract necessary header information."""
    # Example: Extracting a bearer token if specified in the YAML.
    # This function should be customized based on your specific header requirements.
    headers = {}
    # Implement your header extraction logic here
    return headers


def remove_refs(data):
    """Recursively remove $ref keys from the API spec."""
    if isinstance(data, dict):
        if "$ref" in data:
            del data["$ref"]
        for key, value in data.items():
            remove_refs(value)
    elif isinstance(data, list):
        for item in data:
            remove_refs(item)


def create_agent_from_yaml(yaml_path):
    """Create an OpenAPI agent from a YAML path."""
    api_spec = load_api_spec(yaml_path)
    headers = construct_headers(api_spec)
    requests_wrapper = RequestsWrapper(headers=headers)
    agent = planner.create_openapi_agent(api_spec, requests_wrapper, llm, allow_dangerous_requests=True)
    return agent


def run_agent_query(yaml_path, user_query):
    """Run a query using the agent created from the given YAML path."""
    agent = create_agent_from_yaml(yaml_path)
    return agent.run(user_query)


# Example usage
if __name__ == "__main__":
    # yaml_path = "./ct-simple-v2.yaml"
    # user_query = "get the latest clinical trial study details on trastuzumab?"
    # yaml_path = "./rxnav-interactions.yaml"
    # user_query = "what are the drug to drug interactions between simvastatin and Sulfamethoxazole?"
    # yaml_path = "./nih-conditions-api.yaml"
    # user_query = "what is the condition for flu"
    result = run_agent_query(yaml_path, user_query)
    print(result)
