"""
Vision service for generating descriptions of images using FeatherlessAI.
"""
import base64
import time
from io import BytesIO
from typing import Optional

from openai import OpenAI
from PIL import Image

from ..core.config import FEATHERLESS_API_KEY, FEATHERLESS_BASE_URL, FEATHERLESS_VISION_MODEL


class VisionService:
    def __init__(self):
        """Initialize the vision service with FeatherlessAI client."""
        if not FEATHERLESS_API_KEY:
            raise ValueError("FEATHERLESS_API_KEY not configured")
        
        self.client = OpenAI(
            api_key=FEATHERLESS_API_KEY,
            base_url=FEATHERLESS_BASE_URL
        )
        self.model = FEATHERLESS_VISION_MODEL
        self.max_retries = 3
        self.retry_delay = 2  # seconds
    
    def _encode_image(self, image_bytes: bytes) -> str:
        """Encode image bytes to base64 string."""
        return base64.b64encode(image_bytes).decode('utf-8')
    
    def _optimize_image(self, image_bytes: bytes, max_size: int = 1024) -> bytes:
        """
        Optimize image size to reduce API costs while maintaining quality.
        Resizes image if larger than max_size while preserving aspect ratio.
        """
        img = Image.open(BytesIO(image_bytes))
        
        # Convert to RGB if necessary (handles PNG with transparency, etc.)
        if img.mode not in ('RGB', 'L'):
            img = img.convert('RGB')
        
        # Resize if needed
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Save to bytes
        output = BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        return output.getvalue()
    
    def describe_image(
        self,
        image_bytes: bytes,
        prompt: Optional[str] = None,
        optimize: bool = True
    ) -> str:
        """
        Generate a detailed description of an image using FeatherlessAI vision model.
        
        Args:
            image_bytes: Raw image bytes
            prompt: Custom prompt for description (default: general technical description)
            optimize: Whether to optimize image size before sending (recommended)
        
        Returns:
            Text description of the image
        """
        # Optimize image if requested
        if optimize:
            image_bytes = self._optimize_image(image_bytes)
        
        # Encode to base64
        base64_image = self._encode_image(image_bytes)
        
        # Default prompt for technical/code-related images
        if not prompt:
            prompt = """Describe this image in detail. Focus on:
- What type of content it shows (code, diagram, UI, screenshot, etc.)
- Key elements and their purpose
- Any text, code, or technical information visible
- Overall context and what it represents

Be specific and technical in your description."""
        
        # Retry logic for handling temporary API failures
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": prompt
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=500,
                    temperature=0.3  # Lower temperature for more consistent descriptions
                )
                
                description = response.choices[0].message.content.strip()
                print(f"Generated image description: {description[:100]}...")
                return description
                
            except Exception as e:
                last_error = e
                error_msg = str(e)
                
                # Check if it's a retryable error (503, 429, etc.)
                if "503" in error_msg or "429" in error_msg or "server_error" in error_msg.lower():
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                        print(f"FeatherlessAI error (attempt {attempt + 1}/{self.max_retries}): {error_msg}")
                        print(f"Retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                
                # Non-retryable error or final attempt
                print(f"Failed to generate image description: {e}")
                raise
        
        # All retries failed
        print(f"Failed to generate image description after {self.max_retries} attempts: {last_error}")
        raise last_error
