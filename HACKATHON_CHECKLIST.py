#!/usr/bin/env python3
"""
Hackathon Pre-Submission Validation Checklist
Run this to verify your submission meets all requirements
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def check_file_exists(filepath, description):
    """Check if required file exists"""
    if Path(filepath).exists():
        print(f"✅ {description}: {filepath}")
        return True
    else:
        print(f"❌ {description}: MISSING - {filepath}")
        return False

def check_docker_builds():
    """Check if Dockerfile exists and builds"""
    if not Path("Dockerfile").exists():
        print("❌ Dockerfile: MISSING")
        return False
    
    print("✅ Dockerfile: Present")
    print("   ℹ️  To verify build: docker build -t med-triage .")
    return True

def check_openenv_yaml():
    """Check openenv.yaml compliance"""
    if not Path("openenv.yaml").exists():
        print("❌ openenv.yaml: MISSING")
        return False
    
    with open("openenv.yaml") as f:
        content = f.read()
        required_fields = [
            "action_space",
            "observation_space",
            "tasks",
            "endpoints"
        ]
        
        missing = [f for f in required_fields if f not in content]
        if missing:
            print(f"❌ openenv.yaml: Missing fields - {missing}")
            return False
    
    print("✅ openenv.yaml: Compliant")
    return True

def check_environment_implementation():
    """Check if environment has required methods"""
    try:
        from environment.med_triage_env import MedTriageEnv
        env = MedTriageEnv()
        
        required_methods = ['reset', 'step', 'state']
        missing = []
        for method in required_methods:
            if not hasattr(env, method):
                missing.append(method)
        
        if missing:
            print(f"❌ Environment: Missing methods - {missing}")
            return False
        
        # Test reset
        obs = env.reset()
        print("✅ Environment: reset() works")
        
        # Test state
        state = env.state()
        print("✅ Environment: state() works")
        
        print("✅ Environment: All required methods present")
        return True
        
    except Exception as e:
        print(f"❌ Environment: Error - {e}")
        return False

def check_inference_script():
    """Check inference.py compliance"""
    if not Path("inference.py").exists():
        print("❌ inference.py: MISSING")
        return False
    
    print("✅ inference.py: Present")
    
    with open("inference.py") as f:
        content = f.read()
        required_markers = ["[START]", "[STEP]", "[END]"]
        missing = [m for m in required_markers if m not in content]
        if missing:
            print(f"   ⚠️  Warning: Missing logging markers - {missing}")
        else:
            print("✅ inference.py: Has required logging ([START]/[STEP]/[END])")
    
    return True

def check_tests():
    """Check if tests exist and pass"""
    test_file = Path("tests/test_env.py")
    if not test_file.exists():
        print("❌ Tests: test_env.py MISSING")
        return False
    
    print("✅ Tests: test_env.py present")
    
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/test_env.py", "-v", "--tb=short"],
            capture_output=True,
            timeout=60
        )
        
        if result.returncode == 0:
            print("✅ Tests: All tests passing")
            return True
        else:
            print("❌ Tests: Some tests failing")
            print(result.stdout.decode()[-500:])
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️  Tests: Timeout (>60s)")
        return False
    except Exception as e:
        print(f"⚠️  Tests: Error running - {e}")
        return False

def check_readme():
    """Check README quality"""
    if not Path("README.md").exists():
        print("❌ README: MISSING")
        return False
    
    with open("README.md") as f:
        content = f.read()
        
    required_sections = [
        "Problem Statement",
        "Solution",
        "Architecture",
        "Quick Start",
        "Requirements"
    ]
    
    missing = [s for s in required_sections if s not in content]
    
    if missing:
        print(f"⚠️  README: Missing sections - {missing}")
        print("   ℹ️  Note: These are recommended but not required")
        print("✅ README: Present (content check)")
    else:
        print("✅ README: All recommended sections present")
    
    # Check for HF Spaces header
    if content.startswith("---"):
        print("✅ README: Has HF Spaces YAML header")
    else:
        print("⚠️  README: Missing HF Spaces YAML header")
    
    return True

def check_requirements():
    """Check requirements.txt"""
    if not Path("requirements.txt").exists():
        print("❌ requirements.txt: MISSING")
        return False
    
    with open("requirements.txt") as f:
        content = f.read()
        required_packages = ["pydantic"]
        
        missing = [p for p in required_packages if p not in content]
        if missing:
            print(f"⚠️  requirements.txt: Missing {missing}")
        else:
            print("✅ requirements.txt: Has required packages")
    
    return True

def check_api_keys():
    """Check if API keys are configurable"""
    env_vars = ["GROQ", "GEMINI"]
    missing = [v for v in env_vars if v not in os.environ and f"${v}" not in open("inference.py").read()]
    
    if missing:
        print(f"⚠️  API Keys: Some not found in environment - {missing}")
        print("   ℹ️  Set them before running: export GROQ=your_key; export GEMINI=your_key")
    else:
        print("✅ API Keys: Properly configured")
    
    return True

def check_tasks_and_graders():
    """Check if 3+ tasks with graders exist"""
    try:
        from environment.med_triage_env import MedTriageEnv
        env = MedTriageEnv()
        
        # Try reset with different task levels
        task_levels = [1, 2, 3]
        success_count = 0
        
        for level in task_levels:
            try:
                env_task = MedTriageEnv(task_level=level)
                obs = env_task.reset()
                success_count += 1
                print(f"✅ Task level {level}: Works")
            except Exception as e:
                print(f"❌ Task level {level}: Error - {e}")
        
        if success_count >= 3:
            print(f"✅ All 3 tasks available and working")
            return True
        else:
            print(f"❌ Only {success_count}/3 tasks working")
            return False
            
    except Exception as e:
        print(f"❌ Tasks: Error checking - {e}")
        return False

def main():
    """Run all checks"""
    
    print("\n" + "="*80)
    print("🏆 HACKATHON PRE-SUBMISSION VALIDATION")
    print("="*80 + "\n")
    
    checks = [
        ("📁 Project Structure", [
            lambda: check_file_exists("README.md", "README.md"),
            lambda: check_file_exists("Dockerfile", "Dockerfile"),
            lambda: check_file_exists("requirements.txt", "requirements.txt"),
            lambda: check_file_exists("openenv.yaml", "openenv.yaml"),
            lambda: check_file_exists("inference.py", "inference.py"),
        ]),
        ("🔧 Implementation", [
            lambda: check_openenv_yaml(),
            lambda: check_environment_implementation(),
            lambda: check_tasks_and_graders(),
        ]),
        ("📜 Documentation & Config", [
            lambda: check_readme(),
            lambda: check_requirements(),
            lambda: check_inference_script(),
        ]),
        ("🧪 Testing", [
            lambda: check_tests(),
        ]),
    ]
    
    all_passed = True
    
    for category, category_checks in checks:
        print(f"\n{category}")
        print("-" * 80)
        for check in category_checks:
            passed = check()
            all_passed = all_passed and passed
    
    print("\n" + "="*80)
    if all_passed:
        print("✅ ALL CHECKS PASSED - Ready for submission!")
    else:
        print("⚠️  Some checks failed - Review above before submitting")
    print("="*80 + "\n")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
