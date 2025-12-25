# CLARITY - RBI Compliance Agents
import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Gemini 2.5 Flash (both naming conventions)
MODELNAME = "gemini-2.5-flash"
MODEL_NAME = MODELNAME  # For legacy agents

# Configure Gemini API
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print(f"✅ CLARITY Agents loaded - Using {MODELNAME}")
print(f"✅ Gemini API configured - Both MODELNAME & MODEL_NAME available")

# Export both for compatibility
__all__ = ['MODELNAME', 'MODEL_NAME']
