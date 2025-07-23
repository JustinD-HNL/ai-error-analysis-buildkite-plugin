#!/usr/bin/env python3
"""
Test script to verify OpenAI integration
"""

import os
import sys
import json
from lib.analyze import AIAnalyzer

def test_openai_models():
    """Test OpenAI model configuration"""
    
    # Test context
    test_context = {
        "build_info": {
            "pipeline": "test-pipeline",
            "branch": "main",
            "command": "npm test",
            "exit_status": 1,
            "phase": "command"
        },
        "log_excerpt": """
> test@1.0.0 test
> jest

FAIL  src/app.test.js
  ● Test suite failed to run

    Cannot find module 'react' from 'src/app.js'

    Require stack:
      src/app.js
      src/app.test.js

      1 | import React from 'react';
        | ^
      2 | import './App.css';
      3 |

    at Resolver.resolveModule (node_modules/jest-resolve/build/index.js:306:11)
    at Object.<anonymous> (src/app.js:1:1)

Test Suites: 1 failed, 1 total
Tests:       0 total
Snapshots:   0 total
Time:        0.256 s
Ran all test suites.
npm ERR! Test failed.  See above for more details.
"""
    }
    
    # Models to test
    models_to_test = [
        ("gpt-4o-mini", "Most cost-effective"),
        ("gpt-4o", "Most capable"),
        ("o1-mini", "Best for technical reasoning")
    ]
    
    print("OpenAI Model Test")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in environment")
        print("\nTo test, set your OpenAI API key:")
        print("export OPENAI_API_KEY='sk-...'")
        return False
    
    print("✅ API key found")
    print()
    
    # Test each model
    for model, description in models_to_test:
        print(f"Testing {model} ({description})...")
        
        try:
            # Set up environment
            os.environ["AI_ERROR_ANALYSIS_API_KEY"] = os.getenv("OPENAI_API_KEY")
            
            # Initialize analyzer
            analyzer = AIAnalyzer("openai", model, max_tokens=500)
            print(f"  ✅ Model initialized: {analyzer.model}")
            
            # Perform analysis
            result = analyzer.analyze(test_context)
            
            print(f"  ✅ Analysis completed in {result.analysis_time:.2f}s")
            print(f"  📊 Confidence: {result.confidence}%")
            print(f"  🔍 Root cause: {result.root_cause[:100]}...")
            print(f"  💡 Fixes: {len(result.suggested_fixes)} suggestions")
            print(f"  🪙 Tokens used: {result.tokens_used}")
            print()
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)}")
            print()
            continue
    
    return True

if __name__ == "__main__":
    success = test_openai_models()
    sys.exit(0 if success else 1)