import os
import io
import time
import traceback
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import PyPDF2

# Firebase Admin Init
import firebase_admin
from firebase_admin import credentials, firestore

from agents.orchestrator import run_clarity

# ---- Load ENV ----
load_dotenv()
if not os.getenv("GOOGLE_API_KEY"):
    raise ValueError("❌ Add GOOGLE_API_KEY to .env!")

# ---- Firebase Init (only once) ----
if not firebase_admin._apps:
    cred = credentials.Certificate("firebase-admin.json")
    firebase_admin.initialize_app(cred)

db = firestore.client()

app = FastAPI(title="CLARITY Backend")

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ---- PDF text extractor ----
def extract_pdf_text(pdf_file: UploadFile) -> str:
    try:
        pdf_bytes = pdf_file.file.read()
        pdf_file.file.seek(0)
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        text = ""
        for page in reader.pages:
            try:
                t = page.extract_text()
                if t: text += t + "\n\n"
            except:
                continue
        return text.strip()
    except:
        return ""

# ---- MAIN ANALYSIS ENDPOINT ----
@app.post("/api/analyze")
async def analyze_policy(policy_text: str = Form(None), policy_pdf: UploadFile = File(None)):
    try:
        # Read input
        if policy_pdf and policy_pdf.filename:
            text = extract_pdf_text(policy_pdf)
            result = run_clarity(text)
        elif policy_text:
            result = run_clarity(policy_text)
        else:
            return {"status": "failed", "error": "No input"}

        # Store in Firestore
        fb = db.collection("clarity_outputs").add({
            "result": result,
            "createdAt": firestore.SERVER_TIMESTAMP
        })

        print("🔥 Stored JSON in Firestore with ID:", fb[1].id)

        return {"status": "success", "firebase_id": fb[1].id, "data": result}

    except Exception as e:
        traceback.print_exc()
        return {"status": "failed", "error": str(e)}

# ---- NEW ENDPOINT TO READ FIRESTORE JSON ----
@app.get("/api/history")
async def get_history():
    try:
        docs = db.collection("clarity_outputs").order_by("createdAt", direction=firestore.Query.DESCENDING).limit(1).stream()
        for doc in docs:
            d = doc.to_dict()
            return JSONResponse({
                "status": "success",
                "firebase_id": doc.id,
                "result": d.get("result")
            })

        return JSONResponse({"status": "failed", "error": "No history found"}, status_code=404)

    except Exception as e:
        print("❌ Firestore read error:", e)
        return JSONResponse({"status": "failed", "error": str(e)}, status_code=500)
@app.get("/firestore/{analysis_id}")
async def fetch_analysis(analysis_id: str):
    try:
        doc = db.collection("clarity_outputs").document(analysis_id).get()
        if not doc.exists:
            return {"status": "failed", "error": "Not found"}
        return {"status": "success", "result": doc.to_dict()["result"]}
    except:
        return {"status": "failed", "error": "Server error"}
