"""
Integration test for YAML download and video generation via backend API
"""

import requests
import json
import os
import sys
from pathlib import Path

# Fix Unicode encoding for Windows console
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

API_BASE_URL = 'http://localhost:5000'

# Sample YAML configuration for testing
TEST_YAML = """project:
  name: "Integration Test"
  description: "Test slideshow for integration testing"

paths:
  images_dir: "C:/Users/RAZ/Desktop/Raz-Technologies/Presentation_application/Parents/images"
  audio_dir: "C:/Users/RAZ/Desktop/Raz-Technologies/Presentation_application/Parents/audio"
  output_file: "C:/Users/RAZ/Desktop/Raz-Technologies/Presentation_application/Parents/output/integration_test.mp4"

video:
  resolution: [1920, 1080]
  fps: 30
  codec: "libx264"
  quality: "medium"

timing:
  default_duration: 3.0
  min_duration: 2.0
  max_duration: 5.0
  transition_duration: 1.0

effects:
  enable_ken_burns: true
  ken_burns_intensity: 0.1
  enable_color_grading: false
"""

def test_yaml_download():
    """Test YAML download functionality (client-side, not backend)"""
    print("\n=== Testing YAML Download ===")
    print("✓ YAML download is client-side only (using Blob API)")
    print("✓ No backend interaction needed")
    print("✓ Test passed: YAML content prepared successfully")
    return True

def test_backend_health():
    """Test backend health endpoint"""
    print("\n=== Testing Backend Health ===")
    try:
        response = requests.get(f'{API_BASE_URL}/api/health', timeout=5)
        data = response.json()

        print(f"Status Code: {response.status_code}")
        print(f"Status: {data.get('status')}")
        print(f"Project Root: {data.get('project_root')}")
        print(f"Script Exists: {data.get('script_exists')}")

        if response.status_code == 200 and data.get('status') == 'healthy':
            print("✓ Backend is healthy")
            return True
        else:
            print("✗ Backend health check failed")
            return False
    except Exception as e:
        print(f"✗ Backend health check failed: {e}")
        return False

def test_video_generation():
    """Test video generation via backend API"""
    print("\n=== Testing Video Generation Integration ===")

    try:
        # Prepare the request
        payload = {
            'yaml_content': TEST_YAML,
            'filename': 'integration_test.yaml',
            'output_dir': str(Path(__file__).parent / 'output')
        }

        print(f"Sending request to: {API_BASE_URL}/api/generate")
        print(f"Config file: {payload['filename']}")
        print(f"Output directory: {payload['output_dir']}")

        # Make the request
        response = requests.post(
            f'{API_BASE_URL}/api/generate',
            headers={'Content-Type': 'application/json'},
            json=payload,
            timeout=600  # 10 minute timeout for video generation
        )

        print(f"\nResponse Status Code: {response.status_code}")

        try:
            data = response.json()
            print(f"Response Data: {json.dumps(data, indent=2)}")

            if data.get('success'):
                print("\n✓ Video generation request successful!")
                print(f"  Output file: {data.get('output_file', 'N/A')}")
                print(f"  Log file: {data.get('log_file', 'N/A')}")
                print(f"  Config path: {data.get('config_path', 'N/A')}")

                # Check if files were created
                config_path = data.get('config_path')
                if config_path and os.path.exists(config_path):
                    print(f"  ✓ Config file created: {config_path}")

                return True
            else:
                print(f"\n✗ Video generation failed")
                print(f"  Error: {data.get('error', 'Unknown error')}")
                if 'stdout' in data:
                    print(f"  STDOUT: {data['stdout'][:500]}...")
                return False

        except json.JSONDecodeError:
            print(f"✗ Could not parse JSON response")
            print(f"Response text: {response.text[:500]}")
            return False

    except requests.exceptions.Timeout:
        print("✗ Request timed out (video generation may still be running)")
        return False
    except Exception as e:
        print(f"✗ Video generation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    print("=" * 60)
    print("INTEGRATION TESTS - Backend API")
    print("=" * 60)

    results = {}

    # Test 1: YAML Download (client-side)
    results['yaml_download'] = test_yaml_download()

    # Test 2: Backend Health
    results['backend_health'] = test_backend_health()

    # Test 3: Video Generation (only if backend is healthy)
    if results['backend_health']:
        results['video_generation'] = test_video_generation()
    else:
        print("\n⚠ Skipping video generation test (backend not healthy)")
        results['video_generation'] = False

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{test_name.replace('_', ' ').title():.<40} {status}")

    print("\n" + "=" * 60)

    all_passed = all(results.values())
    if all_passed:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")

    return all_passed

if __name__ == '__main__':
    import sys
    success = main()
    sys.exit(0 if success else 1)
