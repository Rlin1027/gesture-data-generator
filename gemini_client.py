import google.generativeai as genai
from PIL import Image
import os
import json
import io

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
            
            # Attempt to extract image from response
            # Check if any part is an image
            if hasattr(response, 'parts'):
                for part in response.parts:
                    if hasattr(part, 'image'):
                        return part.image
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Decode inline data if needed, but part.image usually handles it in SDK
                        try:
                            return Image.open(io.BytesIO(part.inline_data.data))
                        except:
                            pass
            
            # If we are here, maybe the model refused or returned text
            if hasattr(response, 'text'):
                print(f"Model returned text instead of image: {response.text}")
            
            return None

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
            
            # Attempt to extract image from response
            if hasattr(response, 'parts'):
                for part in response.parts:
                    if hasattr(part, 'image'):
                        return part.image
                    if hasattr(part, 'inline_data') and part.inline_data:
                        try:
                            return Image.open(io.BytesIO(part.inline_data.data))
                        except:
                            pass
            
            if hasattr(response, 'text'):
                print(f"Model returned text instead of image: {response.text}")
                
            return None

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
            # User requested gemini-2.0-flash-lite
            try:
                analysis_model = genai.GenerativeModel("gemini-2.0-flash-lite-preview-02-05")
                response = analysis_model.generate_content([prompt, image])
            except Exception:
                try:
                    analysis_model = genai.GenerativeModel("gemini-2.0-flash-lite")
                    response = analysis_model.generate_content([prompt, image])
                except Exception:
                    # Fallback to 1.5 Flash if 2.0 fails
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
