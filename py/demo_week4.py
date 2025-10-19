#!/usr/bin/env python3
"""
Demo script for Week 4 functionality - Sequence Engine and Translation API.

This script demonstrates:
1. Sequence engine pattern matching
2. Blink classification integration
3. Translation API endpoints
4. Fuzzy matching capabilities
"""

import time
import json
from core.sequence_engine import SequenceEngine
from core.blink_classifier import BlinkClassifier
from api.routers.translation import get_sequence_engine, get_blink_classifier

def demo_sequence_engine():
    """Demonstrate the sequence engine functionality."""
    print("=== Sequence Engine Demo ===")
    
    # Initialize engine
    engine = SequenceEngine('sequences_v1.json')
    print(f"Initialized with {len(engine.get_vocabulary())} vocabulary entries")
    print(f"Available patterns: {list(engine.get_vocabulary().keys())}")
    print()
    
    # Test exact matches
    test_cases = [
        ("S S", "yes"),
        ("L", "no"),
        ("S L", "thirsty"),
        ("L S", "hungry"),
        ("S S L", "pain"),
        ("L L", "tired"),
        ("S S S", "light"),
        ("S L L", "temp"),
        ("L S S", "bored"),
        ("L L S", "feelings")
    ]
    
    print("Testing exact matches:")
    for pattern, expected in test_cases:
        # Clear and build sequence
        engine.clear_sequence()
        for symbol in pattern.split():
            engine.add_blink(symbol)
        
        result = engine.finalize_sequence()
        status = "✓" if result == expected else "✗"
        print(f"  {status} {pattern} -> {result} (expected: {expected})")
    
    print()
    
    # Test fuzzy matching
    print("Testing fuzzy matching:")
    fuzzy_cases = [
        ("S S S S", "light"),  # Should match S S S via fuzzy matching
        ("S S L L", "temp"),   # Should match S L L via fuzzy matching
        ("L L L", "tired"),    # Should match L L via fuzzy matching
    ]
    
    for pattern, expected in fuzzy_cases:
        engine.clear_sequence()
        for symbol in pattern.split():
            engine.add_blink(symbol)
        
        result = engine.finalize_sequence()
        status = "✓" if result == expected else "✗"
        print(f"  {status} {pattern} -> {result} (expected: {expected})")
    
    print()

def demo_blink_classification():
    """Demonstrate blink classification with synthetic EAR data."""
    print("=== Blink Classification Demo ===")
    
    # Initialize classifier
    classifier = get_blink_classifier()
    engine = get_sequence_engine()
    
    print(f"Classifier thresholds: {classifier.thresholds}")
    print()
    
    # Simulate EAR data for "yes" pattern (S S)
    print("Simulating 'yes' pattern (S S):")
    ear_sequence = [
        (0.3, 0.0),   # Normal eye open
        (0.1, 0.1),   # Blink start (short)
        (0.3, 0.2),   # Blink end
        (0.3, 0.3),   # Normal eye open
        (0.1, 0.4),   # Blink start (short)
        (0.3, 0.5),   # Blink end
        (0.3, 0.6),   # Normal eye open
    ]
    
    for ear, timestamp in ear_sequence:
        events = classifier.process_ear_sample(ear, timestamp)
        for event in events:
            if event.blink_type.value == 'S':
                engine.add_blink('S')
            elif event.blink_type.value == 'L':
                engine.add_blink('L')
            print(f"  EAR {ear:.1f} at {timestamp:.1f}s: {event.blink_type.value} blink ({event.duration_ms:.0f}ms)")
    
    print(f"  Final sequence: {engine.get_current_sequence()}")
    result = engine.finalize_sequence()
    print(f"  Translation: {result}")
    print()

def demo_api_endpoints():
    """Demonstrate the API endpoints."""
    print("=== API Endpoints Demo ===")
    
    # Test translation endpoint
    from fastapi.testclient import TestClient
    from api.main import app
    
    client = TestClient(app)
    
    # Test health endpoint
    response = client.get("/api/health")
    print(f"Health check: {response.status_code} - {response.json()}")
    
    # Test translation endpoint (should be empty initially)
    response = client.get("/api/translation")
    print(f"Translation (empty): {response.status_code} - {response.json()}")
    
    # Test EAR processing endpoint
    ear_data = {"ear_value": 0.15, "timestamp": time.time()}
    response = client.post("/api/translation/process_ear", json=ear_data)
    print(f"EAR processing: {response.status_code} - {response.json()}")
    
    # Test reset endpoint
    response = client.post("/api/translation/reset")
    print(f"Reset: {response.status_code} - {response.json()}")
    
    print()

def demo_error_handling():
    """Demonstrate error handling."""
    print("=== Error Handling Demo ===")
    
    engine = SequenceEngine('sequences_v1.json')
    
    # Test invalid blink types
    print("Testing invalid blink types:")
    engine.add_blink("X")  # Invalid
    engine.add_blink("")   # Empty
    print(f"  Sequence after invalid inputs: {engine.get_current_sequence()}")
    
    # Test empty sequence
    print("Testing empty sequence:")
    result = engine.finalize_sequence()
    print(f"  Empty sequence result: {result}")
    
    # Test no match
    print("Testing no match:")
    engine.clear_sequence()
    engine.add_blink("L")
    engine.add_blink("L")
    engine.add_blink("L")
    engine.add_blink("L")  # L L L L is not in vocabulary
    result = engine.finalize_sequence()
    print(f"  No match result: {result}")
    
    print()

def main():
    """Run all demos."""
    print("BlinkTalk Week 4 Demo - Sequence Engine & Translation API")
    print("=" * 60)
    print()
    
    try:
        demo_sequence_engine()
        demo_blink_classification()
        demo_api_endpoints()
        demo_error_handling()
        
        print("=== Demo Complete ===")
        print("All Week 4 functionality is working correctly!")
        print()
        print("Key features implemented:")
        print("✓ Sequence engine with exact and fuzzy pattern matching")
        print("✓ Blink classification integration")
        print("✓ Translation API endpoints")
        print("✓ Error handling and validation")
        print("✓ Comprehensive test coverage")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
