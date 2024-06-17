import re
import asyncio
from fastapi import FastAPI, HTTPException, Request, Depends, status
from datetime import datetime  # Import the datetime class from the datetime module
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uuid
import os
from data_api_crawler import search_clinical_trials
from final_agent import ask_query

app = FastAPI(
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"  # Ensure this points to the correct full path
)

origins = [
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/ask")
async def ask(request: Request):
    body = await request.json()
    query = body.get('query')
    print(query)
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    result = ask_query(query)
    return result
