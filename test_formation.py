#!/usr/bin/env python3
"""
Test script to verify Formation model integration works properly.
This script demonstrates how to use the Formation model directly.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables from .env file
load_dotenv()

def main():
    """Test Formation model integration."""
    try:
        # Add the src directory to the Python path
        sys.path.insert(0, "src")
        
        # Import our model helper
        from utils.llm_models import get_llm_model, get_available_models
        
        # Display available models
        models_info = get_available_models()
        
        print("\n======== AVAILABLE MODELS ========")
        print(f"Current configuration: {models_info['current_configuration']}")
        print("\nAvailable providers:")
        for provider in models_info['available_providers']:
            print(f"- {provider}")
        
        print("\nA few sample models by provider:")
        for provider, models in models_info['available_models'].items():
            if len(models) > 0:
                print(f"- {provider}: {', '.join(models[:3])}" + (", ..." if len(models) > 3 else ""))
        
        # Check if Formation API key is set
        formation_api_key = os.environ.get("FORMATION_API_KEY")
        if not formation_api_key:
            print("\n⚠️  FORMATION_API_KEY not set. Please set it in your .env file.")
            print("Skipping model test.")
            return
        
        # Create a model instance
        print("\n======== TESTING FORMATION MODEL ========")
        print("Creating Formation model instance...")
        formation_model = get_llm_model(provider="formation", model_id="best-quality")
        
        # Display model information
        print(f"Model ID: {getattr(formation_model, 'id', 'Unknown')}")
        print(f"Provider: {getattr(formation_model, 'provider', 'Unknown')}")
        
        # Test a simple generation
        print("\nTesting model with a simple prompt...")
        try:
            from agno.models.message import Message
            
            # Prepare messages
            messages = [
                Message(role="system", content="You are a helpful assistant who provides brief answers."),
                Message(role="user", content="What is financial modeling? Answer in 3 sentences.")
            ]
            
            # Generate a response synchronously
            response = formation_model.invoke(messages)
            print("\nModel response:")
            
            # Extract content from response
            if "choices" in response and len(response["choices"]) > 0:
                content = response["choices"][0].get("message", {}).get("content", "No content")
                print(f"\n{content}")
            else:
                print("No content in response.")
            
            print("\n✅ Formation model test successful!")
            
        except Exception as e:
            print(f"\n❌ Error testing model: {str(e)}")
    
    except ImportError as e:
        print(f"\n❌ Import error: {str(e)}")
        print("Make sure you have all required dependencies installed.")
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")

if __name__ == "__main__":
    main() 