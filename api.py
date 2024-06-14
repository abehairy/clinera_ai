

import re
import asyncio
from fastapi import FastAPI, HTTPException, Query
from fastapi import FastAPI, HTTPException, Request, Depends, status
from datetime import datetime  # Import the datetime class from the datetime module
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uuid
import os
from data_api_crawler import search_clinical_trials

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



@app.get("/api/ask")
async def ask(query):
  result = search_clinical_trials(query)

  return result
