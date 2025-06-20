from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF
import openai
import os

from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

# (Optional) Allow local frontend testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_contract(file: UploadFile = File(...)):
    try:
        # Read the uploaded PDF
        contents = await file.read()
        pdf = fitz.open(stream=contents, filetype="pdf")
        full_text = ""
        for page in pdf:
            full_text += page.get_text()

        # Prompt GPT-4 to flag risky contract clauses
        prompt = f"""
You are a contract risk reviewer.

Analyze the following vendor contract and return a list of risky clauses such as:
- Auto-renewal
- Termination fees
- Missing compliance language
- Payment terms longer than 30 days
- Lack of liability or indemnity clauses

Contract:
\"\"\"
{full_text[:6000]}  # limit tokens
\"\"\"

Respond in this JSON format:
{{
  "auto_renewal": "...",
  "termination_fees": "...",
  "compliance_gaps": "...",
  "payment_terms": "...",
  "other_risks": "..."
}}
"""

        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a legal contract risk analyzer."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4
        )

        result = response['choices'][0]['message']['content']
        return JSONResponse(content={"flags": result})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
