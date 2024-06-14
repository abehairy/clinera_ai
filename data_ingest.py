import os
import requests
from bs4 import BeautifulSoup
from neo4j import GraphDatabase
import json
import logging
from tqdm import tqdm
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Get environment variables
openai_api_key = os.getenv("OPENAI_API_KEY")
neo4j_uri = os.getenv("NEO4J_URI")
neo4j_user = os.getenv("NEO4J_USER")
neo4j_password = os.getenv("NEO4J_PASSWORD")

class WebScraper:
    def __init__(self, base_url, openai_api_key):
        self.base_url = base_url
        self.visited_urls = set()
        self.max_links = 1
        self.openai_api_key = openai_api_key

    def scrape_page(self, url):
        logger.info(f"Scraping page: {url}")
        response = requests.get(url)
        return response.text

    def extract_links(self, html_content):
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if href.startswith('http'):
                links.append(href)
            elif href.startswith('/'):
                links.append(self.base_url + href)
        return links

    def save_to_file(self, filename, content):
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(content)

    def run(self, initial_url, neo4j_handler):
        links_to_scrape = [initial_url]
        while links_to_scrape and len(self.visited_urls) < self.max_links:
            current_url = links_to_scrape.pop(0)
            if current_url in self.visited_urls:
                continue

            logger.info(f"Processing URL: {current_url}")
            html_content = self.scrape_page(current_url)
            self.save_to_file('response.txt', html_content)
            self.visited_urls.add(current_url)

            # Decompose content and send to OpenAI
            neo4j_commands = self.generate_neo4j_commands_decomposed(html_content)
            if neo4j_commands:
                neo4j_handler.execute_commands(neo4j_commands)

            links = self.extract_links(html_content)
            for link in links:
                if link not in self.visited_urls:
                    links_to_scrape.append(link)
                    if len(links_to_scrape) >= self.max_links:
                        break

    def generate_neo4j_commands_decomposed(self, content):
        # Limit content to the top 40,000 characters
        limited_content = content[:40000]
        
        # Split content into chunks of 10,000 characters
        chunks = [limited_content[i:i + 10000] for i in range(0, len(limited_content), 10000)]

        all_commands = ""
        for chunk in tqdm(chunks, desc="Processing chunks", unit="chunk"):
            prompt = f"Generate Neo4j commands to create nodes and relationships from the following content:\n\n{chunk}\n\nCommands:"
            url = "https://api.openai.com/v1/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.openai_api_key}"
            }
            data = {
                "model": "gpt-4",
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant that generates Neo4j commands."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1500  # Adjust max tokens
            }
            response = requests.post(url, headers=headers, data=json.dumps(data))
            response_json = response.json()

            if 'choices' not in response_json:
                logger.error(f"Error in OpenAI API response: {response_json}")
                continue

            commands = response_json['choices'][0]['message']['content'].strip()
            valid_commands = self.clean_commands(commands)
            all_commands += valid_commands + "\n" if valid_commands else ""

        return all_commands

    def clean_commands(self, commands):
        # Clean the commands to ensure only valid Cypher commands are executed
        valid_commands = []
        cypher_keywords = ["CREATE", "MATCH", "MERGE", "RETURN", "DELETE", "DETACH", "SET", "REMOVE", "WITH", "UNWIND"]
        for command in commands.split('\n'):
            command = command.strip()
            if command and any(command.upper().startswith(keyword) for keyword in cypher_keywords):
                if command.upper().startswith("MATCH") and command.upper().endswith("MATCH"):
                    continue  # Skip commands ending with MATCH without RETURN or other valid clause
                valid_commands.append(command)
            else:
                logger.warning(f"Ignored invalid command: {command}")
        return "\n".join(valid_commands)

class Neo4jHandler:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def execute_commands(self, commands):
        with self.driver.session() as session:
            for command in commands.split('\n'):
                try:
                    session.write_transaction(lambda tx: tx.run(command))
                except Exception as e:
                    logger.error(f"Error executing command '{command}': {e}")

if __name__ == "__main__":
    base_url = "https://www.medscape.com"
    initial_url = "https://www.medscape.com/viewarticle/solving-restless-legs-largest-genetic-study-date-may-help-2024a1000b40?form=fpf"

    # Scraping data
    scraper = WebScraper(base_url, openai_api_key)

    # Connecting to Neo4j
    try:
        neo4j_handler = Neo4jHandler(neo4j_uri, neo4j_user, neo4j_password)
        scraper.run(initial_url, neo4j_handler)
    except Exception as e:
        logger.error(f"An error occurred: {e}")
    finally:
        neo4j_handler.close()
