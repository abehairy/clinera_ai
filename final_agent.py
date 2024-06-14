import requests
from bs4 import BeautifulSoup
from unstructured.partition.html import partition_html
from pymongo import MongoClient

# Step 1: Scrape the medical news website
def scrape_jina_ai(url: str) -> str:
    response = requests.get("https://r.jina.ai/" + url)
    return response.text

# Step 2: Use Unstructured to process the scraped data
def process_with_unstructured(html_content):
    elements = partition_html(text=html_content)
    json_data = [element.to_dict() for element in elements]
    return json_data

def add_empty_text_embedding(data):
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                item['text_embedding'] = []
    elif isinstance(data, dict):
        data['text_embedding'] = []
    return data

# Step 3: Save the JSON data to MongoDB
def save_to_mongodb(data, db_name, collection_name):
    client = MongoClient('mongodb+srv://clinera:BxHgNChSxPKWvnHL@clinera.rlsmowf.mongodb.net/?retryWrites=true&w=majority&appName=clinera')
    db = client[db_name]
    collection = db[collection_name]

    # Ensuring that the data is a dictionary
    if isinstance(data, list):
        for item in data:
            if not isinstance(item, dict):
                raise TypeError("All items in the data list must be dictionaries")
        result = collection.insert_many(data)
    elif isinstance(data, dict):
        result = collection.insert_one(data)
    else:
        raise TypeError("Data must be a dictionary or a list of dictionaries")

    return result

# Step 4: Main function to tie everything together
def main(url, db_name, collection_name):
    html_content = scrape_jina_ai(url)
    if not html_content:
        print("Failed to scrape the website.")
        return
    
    json_data = process_with_unstructured(html_content)
    json_data = add_empty_text_embedding(json_data)
    print(json_data)
    inserted_id = save_to_mongodb(json_data, db_name, collection_name)
    
    print(f"Data successfully inserted with ID: {inserted_id}")

if __name__ == "__main__":
    medical_news_url = 'https://www.medscape.com/viewarticle/dea-training-mandate-8-hours-my-life-id-back-2024a1000avg'  # Replace with actual article URL
    database_name = 'clinera'
    collection_name = 'medical_content'
    
    main(medical_news_url, database_name, collection_name)
