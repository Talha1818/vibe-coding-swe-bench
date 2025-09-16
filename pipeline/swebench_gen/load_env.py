#!/usr/bin/env python3
"""
Helper script to load environment variables from .env file
and run the prompt injection tests.
"""

import os
import subprocess
from pathlib import Path

def load_env_file(env_path=".env"):
    """Load environment variables from .env file."""
    env_file = Path(env_path)
    if not env_file.exists():
        print(f"No .env file found at {env_path}")
        return False
    
    with open(env_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
                print(f"Loaded: {key}")
    
    return True

def test_injection_with_env(model="openai/gpt-4o-mini", injection_type="none", limit=5):
    """Test injection with environment variables loaded."""
    
    # Load .env file
    if not load_env_file():
        print("Please create a .env file with your OPENROUTER_API_KEY")
        return
    
    # Check if API key is loaded
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key or api_key == "your_openrouter_api_key_here":
        print("Please set a valid OPENROUTER_API_KEY in your .env file")
        return
    
    print(f"Testing {model} with injection: {injection_type}")
    print(f"API Key loaded: {api_key[:10]}...")
    
    # Run the test
    try:
        result = subprocess.run([
            "python", "test_injection.py", model, injection_type, str(limit)
        ], check=True, capture_output=True, text=True)
        
        print("✅ Test completed successfully!")
        print(result.stdout)
        
    except subprocess.CalledProcessError as e:
        print("❌ Test failed:")
        print(e.stderr)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) >= 2:
        model = sys.argv[1]
    else:
        model = "openai/gpt-4o-mini"
    
    if len(sys.argv) >= 3:
        injection_type = sys.argv[2]
    else:
        injection_type = "none"
    
    if len(sys.argv) >= 4:
        limit = int(sys.argv[3])
    else:
        limit = 5
    
    test_injection_with_env(model, injection_type, limit)
