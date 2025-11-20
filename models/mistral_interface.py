"""
Interface for interacting with Mistral model via Ollama
"""
import ollama
from typing import Optional, List, Dict, Any


class MistralInterface:
    """
    Wrapper for Mistral model interactions via Ollama
    
    This provides a simple, consistent interface for all attacks/defenses
    to use when talking to Mistral.
    """
    
    def __init__(
        self, 
        model_name: str = "mistral:7b-instruct-q4_0",
        temperature: float = 0.7,
        max_tokens: int = 1024
    ):
        """
        Initialize 
        Args:
            model_name: Ollama model name (default: mistral:7b-instruct-q4_0)
            temperature: Sampling temperature 0-1 (higher = more random)
            max_tokens: Maximum response length
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.conversation_history: List[Dict[str, str]] = []
        
        print(f"✓ Initialized Mistral interface: {model_name}")
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """
        Generate a response from Mistral
        Args:
            prompt: User prompt/question
            system_prompt: Optional system instructions
            temperature: Override default temperature
            max_tokens: Override default max tokens
            stream: Whether to stream response (default: False)
        
        Returns:
            Model response as string
        """
        # Build messages
        messages = []
        
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt
            })
        
        messages.append({
            "role": "user",
            "content": prompt
        })
        
        # Use provided values or defaults
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": temp,
                    "num_predict": tokens
                },
                stream=stream
            )
            
            if stream:
                # Return generator for streaming
                return response
            else:
                return response['message']['content']
        
        except Exception as e:
            print(f"Error generating response: {e}")
            raise
    
    def chat(
        self,
        message: str,
        system_prompt: Optional[str] = None,
        reset_history: bool = False
    ) -> str:
        """
        Have a multi-turn conversation and maintain  history
        
        Args:
            message: User message
            system_prompt: Optional system instructions (only used if history is empty)
            reset_history: Clear conversation history before this message
        """
        if reset_history:
            self.conversation_history = []
        
        # Add system prompt if this is first message
        if not self.conversation_history and system_prompt:
            self.conversation_history.append({
                "role": "system",
                "content": system_prompt
            })
        
        # Add user message
        self.conversation_history.append({
            "role": "user",
            "content": message
        })
        
        try:
            response = ollama.chat(
                model=self.model_name,
                messages=self.conversation_history,
                options={
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens
                }
            )
            
            assistant_message = response['message']['content']
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
        
        except Exception as e:
            print(f"Error in chat: {e}")
            raise
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []
        print("✓ Conversation history cleared")
    
    def get_history(self) -> List[Dict[str, str]]:
        """Get current conversation history"""
        return self.conversation_history.copy()
    
    def test_connection(self) -> bool:
        """
        Test if model is accessible and responding
        
        Returns:
            True if model works, False otherwise
        """
        try:
            response = self.generate("Say 'OK' if you can read this.", max_tokens=10)
            return "ok" in response.lower()
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False


# Tests
def quick_test():
    """Quick test of Mistral interface"""
    print("Testing Mistral Interface...")
    print("-" * 50)
    
    # Initialize
    model = MistralInterface()
    
    # Test 1: Simple generation
    print("\n1. Simple generation:")
    response = model.generate("What is 2+2? Answer in one sentence.")
    print(f"   Q: What is 2+2?")
    print(f"   A: {response}")
    
    # Test 2: With system prompt
    print("\n2. With system prompt:")
    response = model.generate(
        prompt="What is the capital of France?",
        system_prompt="You are a helpful geography teacher. Be concise."
    )
    print(f"   Q: What is the capital of France?")
    print(f"   A: {response}")
    
    # Test 3: Multi-turn conversation
    print("\n3. Multi-turn conversation:")
    model.clear_history()
    r1 = model.chat("My favorite color is blue.")
    print(f"   User: My favorite color is blue.")
    print(f"   Mistral: {r1}")
    
    r2 = model.chat("What's my favorite color?")
    print(f"   User: What's my favorite color?")
    print(f"   Mistral: {r2}")
    
    print("\n" + "-" * 50)
    print("✓ All tests completed!")


if __name__ == "__main__":
    # Run tests when file is run directly
    quick_test()