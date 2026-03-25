"""
LLM Client - Ollama integration for local LLM inference
"""

import os
import json
from typing import List, Dict, Any, Optional
import logging
import requests

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for Ollama LLM inference."""
    
    def __init__(
        self,
        host: str = "localhost:11434",
        model: str = "minimax-m2.5:cloud",
        timeout: int = 120
    ):
        """
        Initialize Ollama client.
        
        Args:
            host: Ollama host address
            model: Model name to use
            timeout: Request timeout in seconds
        """
        self.host = host
        self.model = model
        self.timeout = timeout
        self.base_url = f"http://{host}"
        self.available = self._check_connection()
        self.available_models = self._get_models() if self.available else [model]
    
    def _check_connection(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            logger.warning(f"Cannot connect to Ollama at {self.base_url}")
            return False
    
    def _get_models(self) -> List[str]:
        """Get list of available models."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return [m['name'] for m in data.get('models', [])]
        except Exception as e:
            logger.error(f"Error fetching models: {e}")
        return [self.model]
    
    def chat(
        self,
        message: str,
        context: Optional[str] = None,
        system: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Send chat message to Ollama.
        
        Args:
            message: User message
            context: Optional context from RAG
            system: Optional system prompt
            temperature: Response temperature
        
        Returns:
            Model response
        """
        if not self.available:
            return "Error: Ollama is not available. Please start the Ollama server."
        
        # Build messages
        messages = []
        
        if system:
            messages.append({"role": "system", "content": system})
        
        if context:
            messages.append({
                "role": "system",
                "content": f"Use the following context to answer the question:\n\n{context}"
            })
        
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result['message']['content']
        
        except requests.exceptions.Timeout:
            return "Error: Request timed out. Try again with a simpler query."
        
        except requests.exceptions.HTTPError as e:
            return f"Error: HTTP {e.response.status_code}"
        
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            return f"Error: {str(e)}"
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Generate response (simple completion).
        
        Args:
            prompt: Input prompt
            system: Optional system prompt
            temperature: Response temperature
        
        Returns:
            Generated text
        """
        if not self.available:
            return "Error: Ollama is not available."
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature
            }
        }
        
        if system:
            payload["system"] = system
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            result = response.json()
            return result.get('response', '')
        
        except Exception as e:
            logger.error(f"Generate error: {e}")
            return f"Error: {str(e)}"
    
    def extract_structured(
        self,
        text: str,
        schema: Dict[str, str],
        template: str = "invoice"
    ) -> Dict[str, Any]:
        """
        Extract structured data from text.
        
        Args:
            text: Document text
            schema: Field names and descriptions
            template: Extraction template type
        
        Returns:
            Extracted fields
        """
        system_prompt = f"""You are a document extraction assistant. Extract the following fields from the document text.

Fields to extract:
{json.dumps(schema, indent=2)}

Return ONLY a valid JSON object with the extracted fields. If a field cannot be found, use null.

Document type: {template}"""
        
        prompt = f"Extract the following fields from this document:\n\n{text}"
        
        response = self.chat(prompt, system=system_prompt, temperature=0.1)
        
        # Parse JSON response
        try:
            # Find JSON in response
            start = response.find('{')
            end = response.rfind('}') + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except json.JSONDecodeError:
            pass
        
        # Return empty dict if parsing failed
        return {field: None for field in schema}
    
    def summarize(self, text: str, max_length: int = 500) -> str:
        """Summarize text."""
        prompt = f"Summarize the following text in {max_length} characters or less:\n\n{text}"
        return self.generate(prompt, temperature=0.3)
    
    def answer_with_sources(
        self,
        question: str,
        sources: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Answer question with source citations.
        
        Args:
            question: User question
            sources: List of source documents with 'text' and 'metadata'
        
        Returns:
            Answer with citations
        """
        # Build context
        context = "\n\n".join([
            f"[Source {i+1}: {s['metadata'].get('source', 'Unknown')}, Page {s['metadata'].get('page', 'N/A')}]\n{s['text']}"
            for i, s in enumerate(sources)
        ])
        
        system_prompt = """Answer the question based on the provided context. 
Include citations by referencing the source numbers when using information from specific sources.
If the answer is not in the context, say so clearly."""
        
        answer = self.chat(
            question,
            context=context,
            system=system_prompt,
            temperature=0.3
        )
        
        return {
            'answer': answer,
            'sources': sources,
            'model': self.model
        }