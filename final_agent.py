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


def get_embedding(query):
    url = 'https://api.openai.com/v1/embeddings'
    openai_key = 'sk-proj-w52tT0ejyKYYqDRM4r3rT3BlbkFJzeJQ36r0FqQqABEfxNwC'  # Replace with your actual API key
    
    response = requests.post(url, json={
        'input': query,
        'model': "text-embedding-3-small"
    }, headers={
        'Authorization': f'Bearer {openai_key}',
        'Content-Type': 'application/json'
    })
    
    if response.status_code == 200:
        return response.json()['data'][0]['embedding']
    else:
        raise Exception(f'Failed to get embedding. Status code: {response.status_code}')

def find_similar_documents(embedding):
    
    client = MongoClient('mongodb+srv://clinera:BxHgNChSxPKWvnHL@clinera.rlsmowf.mongodb.net/?retryWrites=true&w=majority&appName=clinera')
    
    try:
        db = client['clinera']
        collection = db['medical_content']
        
        documents = collection.aggregate([
            {"$vectorSearch": {
                "queryVector": embedding,
                "path": "text_embedding",
                "numCandidates": 100,
                "limit": 1,
                "index": "ContentSearch",
            }}
        ])
        
        return documents
    finally:
        client.close()

def get_answer(query, documents):
    document_texts = '\n\n'.join([doc['text'] for doc in documents])
    
    prompt = f'Using the following documents, answer the query:\nQuery: {query}\nDocuments:\n{document_texts}\nAnswer:'
    
    url = "https://api.openai.com/v1/chat/completions"
    api_key = "sk-proj-w52tT0ejyKYYqDRM4r3rT3BlbkFJzeJQ36r0FqQqABEfxNwC"  # Replace with your actual API key

    headers = {
        "Content-Type": "application/json",
        "Authorization": f'Bearer {api_key}'
    }
    
    data = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 1500  # Adjust max tokens as needed
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f'Error in generating answer. Status code: {response.status_code}')

def ask_query(query):
    #query = 'Who is Larry?'

    try:
        embedding = get_embedding(query)
        print(embedding)
        documents = find_similar_documents(embedding)
        print(documents)
        answer = get_answer(query, documents)
        print(answer)
        return answer
    except Exception as err:
        print(str(err))

# Step 4: Main function to tie everything together
def main(url, db_name, collection_name):
    query = 'Who is Larry?'
    
    try:
        embedding = get_embedding(query)
        print(embedding)
        documents = find_similar_documents(embedding)
        print(documents)
        answer = get_answer(query, documents)
        print(answer)
    except Exception as err:
        print(str(err))


    # html_content = scrape_jina_ai(url)
    # if not html_content:
    #     print("Failed to scrape the website.")
    #     return
    
    # json_data = process_with_unstructured(html_content)
    # json_data = add_empty_text_embedding(json_data)
    # print(json_data)
    # inserted_id = save_to_mongodb(json_data, db_name, collection_name)
    
    # print(f"Data successfully inserted with ID: {inserted_id}")

if __name__ == "__main__":
    medical_news_url = ''  # Replace with actual article URL
    database_name = 'clinera'
    collection_name = 'medical_content'
    
    main(medical_news_url, database_name, collection_name)
