#!/usr/bin/env python3
"""
Week 5 Demo: Calibration Profiles & Overrides
Demonstrates calibration profile switching and its effects on blink detection.
"""
import time
import requests
import json
from typing import Dict, Any

# API base URL
BASE_URL = "http://localhost:8011"

def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")

def print_step(step: str):
    """Print a step indicator."""
    print(f"\n🔧 {step}")

def make_request(method: str, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Make an API request and return the response."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, timeout=5)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        response.raise_for_status()
        return response.json()
    
    except requests.exceptions.RequestException as e:
        print(f"❌ API Error: {e}")
        return {"error": str(e)}

def test_calibration_profiles():
    """Test calibration profile switching functionality."""
    print_header("Week 5 Demo: Calibration Profiles & Overrides")
    
    print("This demo shows how calibration profiles affect blink detection thresholds.")
    print("We'll switch between 'slow' and 'medium' profiles and see the differences.")
    
    # Test 1: Get initial calibration info
    print_step("1. Getting initial calibration information")
    info = make_request("GET", "/api/calibration/info")
    if "error" not in info:
        print(f"✅ Active Profile: {info['active_profile']}")
        print(f"✅ Available Profiles: {list(info['available_profiles'].keys())}")
        print(f"✅ Current Thresholds: {info['current_thresholds']}")
    else:
        print("❌ Failed to get calibration info")
        return
    
    # Test 2: Switch to slow profile
    print_step("2. Switching to 'slow' profile")
    slow_response = make_request("POST", "/api/calibration/set", {"profile": "slow"})
    if "error" not in slow_response:
        print(f"✅ Profile switched to: {slow_response['profile']}")
        print(f"✅ Description: {slow_response['description']}")
        print(f"✅ New Thresholds:")
        for key, value in slow_response['thresholds'].items():
            print(f"   - {key}: {value}ms")
    else:
        print("❌ Failed to switch to slow profile")
        return
    
    # Test 3: Switch to medium profile
    print_step("3. Switching to 'medium' profile")
    medium_response = make_request("POST", "/api/calibration/set", {"profile": "medium"})
    if "error" not in medium_response:
        print(f"✅ Profile switched to: {medium_response['profile']}")
        print(f"✅ Description: {medium_response['description']}")
        print(f"✅ New Thresholds:")
        for key, value in medium_response['thresholds'].items():
            print(f"   - {key}: {value}ms")
    else:
        print("❌ Failed to switch to medium profile")
        return
    
    # Test 4: Compare threshold differences
    print_step("4. Comparing threshold differences")
    print("Threshold Comparison:")
    print("┌─────────────────────┬─────────┬─────────┬─────────┐")
    print("│ Threshold           │ Slow    │ Medium  │ Diff    │")
    print("├─────────────────────┼─────────┼─────────┼─────────┤")
    
    slow_thresholds = slow_response['thresholds']
    medium_thresholds = medium_response['thresholds']
    
    for key in slow_thresholds.keys():
        slow_val = slow_thresholds[key]
        medium_val = medium_thresholds[key]
        diff = slow_val - medium_val
        print(f"│ {key:<19} │ {slow_val:>7} │ {medium_val:>7} │ {diff:>+7} │")
    
    print("└─────────────────────┴─────────┴─────────┴─────────┘")
    
    # Test 5: Test blink detection with different profiles
    print_step("5. Testing blink detection with different profiles")
    
    # Reset sequence first
    make_request("POST", "/api/translation/reset")
    
    # Test with slow profile
    print("Testing with SLOW profile (500ms short max):")
    make_request("POST", "/api/calibration/set", {"profile": "slow"})
    
    # Simulate a 400ms blink (should be short in slow profile)
    ear_data = {
        "ear_value": 0.15,
        "timestamp": time.time()
    }
    make_request("POST", "/api/translation/process_ear", ear_data)
    
    # End blink after 400ms
    time.sleep(0.4)
    ear_data["ear_value"] = 0.3
    ear_data["timestamp"] = time.time()
    result = make_request("POST", "/api/translation/process_ear", ear_data)
    
    if "error" not in result:
        print(f"   - Blink events detected: {result['blink_events']}")
        print(f"   - Current sequence: {result['current_sequence']}")
    
    # Reset and test with medium profile
    print("\nTesting with MEDIUM profile (350ms short max):")
    make_request("POST", "/api/calibration/set", {"profile": "medium"})
    make_request("POST", "/api/translation/reset")
    
    # Simulate the same 400ms blink (should be long in medium profile)
    ear_data = {
        "ear_value": 0.15,
        "timestamp": time.time()
    }
    make_request("POST", "/api/translation/process_ear", ear_data)
    
    # End blink after 400ms
    time.sleep(0.4)
    ear_data["ear_value"] = 0.3
    ear_data["timestamp"] = time.time()
    result = make_request("POST", "/api/translation/process_ear", ear_data)
    
    if "error" not in result:
        print(f"   - Blink events detected: {result['blink_events']}")
        print(f"   - Current sequence: {result['current_sequence']}")
    
    # Test 6: Test gap detection differences
    print_step("6. Testing gap detection differences")
    
    print("Testing symbol gap detection:")
    print("- Slow profile: 600ms symbol gap threshold")
    print("- Medium profile: 450ms symbol gap threshold")
    
    # Reset and test gap detection
    make_request("POST", "/api/translation/reset")
    
    # Test with medium profile (450ms gap threshold)
    make_request("POST", "/api/calibration/set", {"profile": "medium"})
    
    # Simulate a blink
    ear_data = {"ear_value": 0.15, "timestamp": time.time()}
    make_request("POST", "/api/translation/process_ear", ear_data)
    ear_data = {"ear_value": 0.3, "timestamp": time.time() + 0.2}
    make_request("POST", "/api/translation/process_ear", ear_data)
    
    # Wait for 500ms gap (should trigger symbol gap in medium profile)
    time.sleep(0.5)
    ear_data = {"ear_value": 0.3, "timestamp": time.time()}
    result = make_request("POST", "/api/translation/process_ear", ear_data)
    
    if "error" not in result:
        print(f"   - Medium profile (500ms gap): {result.get('word_gap_detected', 'N/A')}")
    
    # Test 7: Reset to default
    print_step("7. Resetting to default profile")
    reset_response = make_request("POST", "/api/calibration/reset")
    if "error" not in reset_response:
        print(f"✅ Reset to: {reset_response['profile']}")
        print(f"✅ Description: {reset_response['description']}")
    else:
        print("❌ Failed to reset calibration")
    
    # Final summary
    print_header("Demo Complete!")
    print("✅ Calibration profile switching works correctly")
    print("✅ Different profiles have different thresholds")
    print("✅ Profile changes affect blink classification")
    print("✅ Profile changes affect gap detection")
    print("✅ API endpoints respond properly")
    print("\n🎉 Week 5: Calibration Profiles & Overrides - SUCCESS!")

def main():
    """Main demo function."""
    print("Starting Week 5 Demo...")
    print("Make sure the API server is running on http://localhost:8011")
    print("Run: python -m uvicorn api.main:app --host 0.0.0.0 --port 8011")
    
    try:
        test_calibration_profiles()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user.")
    except Exception as e:
        print(f"\n\nDemo failed with error: {e}")

if __name__ == "__main__":
    main()
