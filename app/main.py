from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from supabase import create_client, Client
import os
import fitz  # PyMuPDF
import datetime
import json
import logging

app = FastAPI()

# CORS (optional for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Set up logging
logging.basicConfig(level=logging.INFO)

# OpenAI setup
openai_api_key = os.getenv("OPENAI_API_KEY")
if not openai_api_key:
    raise ValueError("Missing OPENAI_API_KEY env var")
openai_client = OpenAI(api_key=openai_api_key)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    # Supabase setup
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    if not supabase_url or not supabase_key:
        raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY env vars")
    supabase: Client = create_client(supabase_url, supabase_key)

    contents = await file.read()

    # Extract text from PDF
    try:
        with fitz.open(stream=contents, filetype="pdf") as doc:
            text = "".join(page.get_text() for page in doc)
    except Exception as e:
        logging.error(f"PDF extraction failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to read PDF")

    # GPT prompt
    prompt = f"""
You are a contract risk analyzer. Identify red flags in the following vendor contract text in plain English:
1. Auto-renewal clauses
2. Termination fees
3. Payment terms longer than 30 days
4. Compliance or legal risks
5. Exclusivity or lock-in

Return them as a JSON object under keys:
- auto_renewal
- termination_fees
- payment_terms
- compliance_gaps
- exclusivity_clauses

Contract:
{text[:3500]}
"""

    # Call GPT with retries
    gpt_output = ""
    for attempt in range(3):
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
            )
            gpt_output = response.choices[0].message.content
            break
        except Exception as e:
            logging.warning(f"GPT call failed (attempt {attempt + 1}): {e}")
            if attempt == 2:
                raise HTTPException(status_code=500, detail="OpenAI API failed after 3 attempts")

    # Parse GPT output to JSON
    try:
        flags = json.loads(gpt_output)
    except Exception as e:
        logging.warning(f"Failed to parse GPT output as JSON: {e}")
        flags = {"raw": gpt_output}

    # Save to Supabase
    try:
        supabase.table("contracts").insert({
            "file_name": file.filename,
            "created_at": datetime.datetime.utcnow().isoformat(),
            "raw_text": text[:5000],
            "flags": flags
        }).execute()
    except Exception as e:
        logging.error(f"Supabase insert failed: {e}")
        raise HTTPException(status_code=500, detail="Database insert failed")

    return {"flags": flags}
