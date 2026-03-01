#!/usr/bin/env python3
"""
Test script to verify the YouTube Timestamp Finder setup.
"""

import os
import sys
import subprocess

def check_python_version():
    """Check if Python version is 3.8+"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print("✅ Python version:", f"{version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print("❌ Python 3.8+ required. Current:", f"{version.major}.{version.minor}")
        return False

def check_ffmpeg():
    """Check if ffmpeg is installed"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, 
                              text=True, 
                              timeout=5)
        if result.returncode == 0:
            print("✅ ffmpeg is installed")
            return True
        else:
            print("❌ ffmpeg not working properly")
            return False
    except FileNotFoundError:
        print("❌ ffmpeg not found. Install it:")
        print("   Ubuntu: sudo apt-get install ffmpeg")
        print("   macOS: brew install ffmpeg")
        return False
    except Exception as e:
        print(f"❌ Error checking ffmpeg: {e}")
        return False

def check_dependencies():
    """Check if Python packages are installed"""
    required = ['fastapi', 'uvicorn', 'yt_dlp', 'google.generativeai', 'pydantic']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} not installed")
            missing.append(package)
    
    if missing:
        print("\nInstall missing packages:")
        print("pip install -r requirements.txt")
        return False
    return True

def check_api_key():
    """Check if GOOGLE_API_KEY is set"""
    api_key = os.environ.get("GOOGLE_API_KEY")
    if api_key:
        print(f"✅ GOOGLE_API_KEY is set ({len(api_key)} characters)")
        return True
    else:
        print("❌ GOOGLE_API_KEY not set")
        print("   Set it with: export GOOGLE_API_KEY='your_key'")
        print("   Get key from: https://aistudio.google.com/app/apikey")
        return False

def main():
    print("🔍 Checking YouTube Timestamp Finder Setup...\n")
    
    checks = [
        ("Python Version", check_python_version()),
        ("ffmpeg", check_ffmpeg()),
        ("Python Packages", check_dependencies()),
        ("Gemini API Key", check_api_key()),
    ]
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print("="*50)
    
    all_passed = True
    for name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")
        if not passed:
            all_passed = False
    
    print("="*50)
    
    if all_passed:
        print("\n🎉 All checks passed! You're ready to run:")
        print("   python main.py")
        print("\nThen test with:")
        print('   curl -X POST "http://localhost:8000/ask" \\')
        print('     -H "Content-Type: application/json" \\')
        print('     -d \'{"video_url": "https://youtu.be/dQw4w9WgXcQ", "topic": "intro"}\'')
    else:
        print("\n⚠️ Some checks failed. Fix the issues above and try again.")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
