const axios = require('axios');
const MongoClient = require('mongodb').MongoClient;

async function getEmbedding(query) {
    const url = 'https://api.openai.com/v1/embeddings';
    const openai_key = 'sk-proj-w52tT0ejyKYYqDRM4r3rT3BlbkFJzeJQ36r0FqQqABEfxNwC'; 
    
    // Call OpenAI API to get the embeddings.
    let response = await axios.post(url, {
        input: query,
        model: "text-embedding-3-small"
    }, {
        headers: {
            'Authorization': `Bearer ${openai_key}`,
            'Content-Type': 'application/json'
        }
    });
    
    if(response.status === 200) {
        return response.data.data[0].embedding;
    } else {
        throw new Error(`Failed to get embedding. Status code: ${response.status}`);
    }
}

async function findSimilarDocuments(embedding) {
    const url = 'mongodb+srv://clinera:BxHgNChSxPKWvnHL@clinera.rlsmowf.mongodb.net/?retryWrites=true&w=majority&appName=clinera'; // Replace with your MongoDB url.
    const client = new MongoClient(url);
    
    try {
        await client.connect();
        
        const db = client.db('clinera'); 
        const collection = db.collection('medical_content'); 
        
        const documents = await collection.aggregate([
  {"$vectorSearch": {
    "queryVector": embedding,
    "path": "text_embedding",
    "numCandidates": 100,
    "limit": 1,
    "index": "ContentSearch",
      }}
]).toArray();
        
        return documents;
    } finally {
        await client.close();
    }
}

async function main() {
    const query = 'Who is Larry?'; 
    
    try {
        const embedding = await getEmbedding(query);
        const documents = await findSimilarDocuments(embedding);
        console.log(documents);
        const returnAnswer = await getAnswer(query, documents);
        console.log(returnAnswer);
    } catch(err) {
        console.error(err);
    }
}

async function getAnswer(query, documents) {
    // Combine the query and documents into a single prompt
    const documentTexts = documents.map(doc => doc.text).join('\n\n');

    const prompt = `Using the following documents, answer the query:
    Query: ${query}
    Documents:
    ${documentTexts}
    Answer:`;

    const url = "https://api.openai.com/v1/chat/completions";
    const apiKey = "sk-proj-w52tT0ejyKYYqDRM4r3rT3BlbkFJzeJQ36r0FqQqABEfxNwC";  // Replace with your actual API key

    const headers = {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${apiKey}`
    };

    const data = {
        "model": "gpt-4o",
        "messages": [
            { "role": "system", "content": "You are a helpful assistant." },
            { "role": "user", "content": prompt }
        ],
        "max_tokens": 1500  // Adjust max tokens as needed
    };

    try {
        const response = await fetch(url, {
            method: "POST",
            headers: headers,
            body: JSON.stringify(data)
        });

        const responseData = await response.json();
        return responseData.choices[0].message.content;
    } catch (err) {
        console.error(err);
        throw err;
    }
}



main();