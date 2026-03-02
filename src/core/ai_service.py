import asyncio
import base64
import logging
import os
from typing import Optional

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)


class AIService:
    """Handles AI-related operations using Google Gemini"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            logger.warning("No GEMINI_API_KEY found in environment")
        else:
            genai.configure(api_key=self.api_key)
    
    async def analyze_screenshot(self, image_data: str, question: str) -> str:
        """Analyze screenshot using Gemini API"""
        try:
            if not self.api_key:
                return "Error: Gemini API key not configured"
            
            # Decode base64 image
            img_bytes = base64.b64decode(image_data)
            
            # Create Gemini model and query
            model = genai.GenerativeModel('gemini-2.0-flash')
            prompt = f"Please analyze this screenshot and answer: {question}"
            
            response = model.generate_content([
                prompt,
                {"mime_type": "image/png", "data": img_bytes}
            ])
            return response.text
            
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            return f"Analysis failed: {str(e)}"

    async def analyze_text(self, question: str) -> str:
        """Analyze text using Gemini API (text-only)"""
        try:
            if not self.api_key:
                return "Error: Gemini API key not configured"

            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(question)
            return response.text
        except Exception as e:
            logger.error(f"Text analysis failed: {e}")
            return f"Analysis failed: {str(e)}"
