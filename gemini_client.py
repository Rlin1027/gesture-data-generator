import google.generativeai as genai
from PIL import Image
import os
import json

class GeminiClient:
    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash-image"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)

    def generate_variation(self, seed_image: Image.Image, prompt: str) -> Image.Image:
        """
        Generate a variation of the seed image.
        Prompt should instruct to keep gesture but change background/attributes.
        """
        full_prompt = [
            "You are a synthetic data generator for NPU training.",
            "Input is a grayscale gesture image (320x180).",
            "Task: Generate a high-quality synthetic training sample based on this seed.",
            "CRITICAL CONSTRAINTS:",
            "1. HAND ANATOMY: Must be perfect. 5 fingers, natural joints. No deformities.",
            "2. GESTURE: Keep the exact hand pose and angle of the seed image.",
            "3. FORMAT: Output must be grayscale, 320x180 resolution.",
            "4. REALISM: Add realistic sensor noise, grain, or motion blur if appropriate for the scene.",
            f"SCENARIO INSTRUCTION: {prompt}",
            seed_image
        ]
        
        try:
            response = self.model.generate_content(full_prompt)
            return response
        except Exception as e:
            print(f"Error in generate_variation: {e}")
            raise e

    def modify_gesture(self, seed_image: Image.Image, reference_image: Image.Image, prompt: str) -> Image.Image:
        """
        Modify the gesture based on reference.
        """
        full_prompt = [
            "You are a synthetic data generator for NPU training.",
            "Input 1: Seed image (Source Style/Identity).",
            "Input 2: Reference image (Target Gesture).",
            "Task: Transfer the style of Input 1 to the gesture of Input 2.",
            "CRITICAL CONSTRAINTS:",
            "1. HAND ANATOMY: Must be perfect. 5 fingers, natural joints.",
            "2. OUTPUT: 320x180 grayscale.",
            f"INSTRUCTION: {prompt}",
            seed_image,
            reference_image
        ]

        try:
            response = self.model.generate_content(full_prompt)
            return response
        except Exception as e:
            print(f"Error in modify_gesture: {e}")
            raise e

    def analyze_image(self, image: Image.Image) -> dict:
        """
        Analyze the image for quality control.
        Returns a JSON dict with analysis results.
        """
        prompt = """
        Analyze this hand gesture image for a machine learning dataset.
        Check for:
        1. Anatomical Correctness (Finger count, joints).
        2. Lighting Quality.
        3. Realism Score (1-10).
        4. Potential Issues (Blur, Artifacts, Occlusion).
        
        Output ONLY a raw JSON object with the following keys:
        {
            "fingerCount": "string (e.g., '5 (Normal)')",
            "lighting": "string (description)",
            "realismScore": number (1-10),
            "issues": "string (None or description of issues)"
        }
        Do not use markdown code blocks. Just the JSON string.
        """
        
        try:
            # Use a text-capable model for analysis if the image model doesn't support text output well
            # But gemini-1.5-flash/pro supports both. gemini-2.5-flash-image might be specialized.
            # Let's try using the same model first, assuming it's multimodal.
            # If it fails, we might need to switch model for analysis.
            # For safety, let's use gemini-1.5-flash for analysis as it's reliable for VQA.
            # However, we want to use the user's key and model preference.
            # Let's stick to self.model for now, but if it's an image-only generation model, this might fail.
            # "gemini-2.5-flash-image" suggests it might be optimized for image gen.
            # Let's try to use "gemini-1.5-flash" for analysis specifically if possible, 
            # or just use the current model and hope it handles VQA.
            # Actually, usually "gemini-pro-vision" or "gemini-1.5-flash" is better for VQA.
            # Let's instantiate a specific VQA model using the same key.
            
            analysis_model = genai.GenerativeModel("gemini-1.5-flash")
            response = analysis_model.generate_content([prompt, image])
            
            text = response.text
            # Clean up potential markdown
            text = text.replace("```json", "").replace("```", "").strip()
            return json.loads(text)
            
        except Exception as e:
            print(f"Error in analyze_image: {e}")
            return {
                "fingerCount": "Error",
                "lighting": "Unknown",
                "realismScore": 0,
                "issues": f"Analysis failed: {str(e)}"
            }
