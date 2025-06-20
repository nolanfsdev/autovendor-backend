from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from supabase import create_client, Client
import os
import fitz  # PyMuPDF
import datetime

supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Missing SUPABASE_URL or SUPABASE_KEY env vars")

supabase: Client = create_client(supabase_url, supabase_key)

app = FastAPI()

# CORS (optional for frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OpenAI setup
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

# Supabase setup
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Read file
    contents = await file.read()

    # Extract text from PDF
    with fitz.open(stream=contents, filetype="pdf") as doc:
        text = ""
        for page in doc:
            text += page.get_text()

    # Analyze with GPT
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
{text[:3500]}  # truncate if needed
"""
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )
    gpt_output = response.choices[0].message.content

    # Save to Supabase
    supabase.table("contracts").insert({
        "filename": file.filename,
        "created_at": datetime.datetime.utcnow().isoformat(),
        "raw_text": text[:5000],
        "analysis": gpt_output
    }).execute()

    return {"flags": gpt_output}
