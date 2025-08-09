import os
import time
from typing import Dict, Tuple, Optional
import openai
import anthropic
import google.generativeai as genai
from config import PRICING, MODELS

class LLMClient:
    def __init__(self):
        # Initialize OpenAI client
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.openai_client = openai.OpenAI(api_key=openai_key)
        else:
            self.openai_client = None
            
        # Initialize Anthropic client
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if anthropic_key:
            self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
        else:
            self.anthropic_client = None
            
        # Initialize Google Gemini
        google_key = os.getenv("GOOGLE_API_KEY")
        if google_key:
            genai.configure(api_key=google_key)
        else:
            print("Warning: Google API key not found")
    
    def generate(self, 
                 provider: str, 
                 model: str, 
                 prompt: str, 
                 params: Optional[Dict] = None) -> Tuple[str, Dict]:
        """
        Generate content using specified LLM provider and model.
        
        Returns: (generated_content, metadata)
        metadata includes: latency_ms, prompt_tokens, completion_tokens, cost_usd
        """
        if params is None:
            params = MODELS[provider]["params"]
            
        start_time = time.time()
        
        try:
            if provider == "openai":
                if not self.openai_client:
                    raise ValueError("OpenAI API key not configured")
                    
                response = self.openai_client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=params.get("temperature", 0.7),
                    max_tokens=params.get("max_tokens", 500)
                )
                
                content = response.choices[0].message.content
                metadata = {
                    "latency_ms": (time.time() - start_time) * 1000,
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "cost_usd": self._calculate_cost(
                        provider, model, 
                        response.usage.prompt_tokens, 
                        response.usage.completion_tokens
                    )
                }
                
            elif provider == "anthropic":
                if not self.anthropic_client:
                    raise ValueError("Anthropic API key not configured")
                    
                response = self.anthropic_client.messages.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=params.get("temperature", 0.7),
                    max_tokens=params.get("max_tokens", 500)
                )
                
                content = response.content[0].text
                metadata = {
                    "latency_ms": (time.time() - start_time) * 1000,
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "cost_usd": self._calculate_cost(
                        provider, model,
                        response.usage.input_tokens,
                        response.usage.output_tokens
                    )
                }
                
            elif provider == "google":
                model_obj = genai.GenerativeModel(model)
                response = model_obj.generate_content(
                    prompt,
                    generation_config=genai.GenerationConfig(
                        temperature=params.get("temperature", 0.7),
                        max_output_tokens=params.get("max_tokens", 500)
                    )
                )
                
                content = response.text
                
                # For Gemini, we'll estimate tokens based on character count
                # Rough estimate: 1 token ≈ 4 characters
                prompt_tokens = len(prompt) // 4
                completion_tokens = len(content) // 4
                
                metadata = {
                    "latency_ms": (time.time() - start_time) * 1000,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "cost_usd": self._calculate_cost(
                        provider, model,
                        prompt_tokens,
                        completion_tokens
                    )
                }
            else:
                raise ValueError(f"Unknown provider: {provider}")
                
            return content, metadata
            
        except Exception as e:
            # Return error information
            return None, {
                "error": str(e),
                "latency_ms": (time.time() - start_time) * 1000,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "cost_usd": 0
            }
    
    def _calculate_cost(self, provider: str, model: str, 
                       prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate cost based on token usage and pricing"""
        try:
            pricing = PRICING[provider][model]
            input_cost = (prompt_tokens / 1000) * pricing["input"]
            output_cost = (completion_tokens / 1000) * pricing["output"]
            return round(input_cost + output_cost, 6)
        except KeyError:
            print(f"Warning: Pricing not found for {provider}/{model}")
            return 0.0
    
    def test_connection(self) -> Dict[str, bool]:
        """Test connections to all configured LLM providers"""
        results = {}
        
        # Test OpenAI
        if self.openai_client:
            try:
                self.openai_client.models.list()
                results["openai"] = True
            except Exception as e:
                results["openai"] = False
                print(f"OpenAI connection failed: {e}")
        else:
            results["openai"] = False
            
        # Test Anthropic
        if self.anthropic_client:
            try:
                # Simple test with minimal tokens
                self.anthropic_client.messages.create(
                    model="claude-3-haiku-20240307",
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=1
                )
                results["anthropic"] = True
            except Exception as e:
                results["anthropic"] = False
                print(f"Anthropic connection failed: {e}")
        else:
            results["anthropic"] = False
            
        # Test Google
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            model.generate_content("Hi", generation_config=genai.GenerationConfig(max_output_tokens=1))
            results["google"] = True
        except Exception as e:
            results["google"] = False
            print(f"Google connection failed: {e}")
            
        return results