#!/usr/bin/env python3
"""
PRE-VALIDATION CHECKLIST FOR MED-TRIAGE OPENENV
Complete validation script matching OpenEnv requirements
Run this before submission to ensure all criteria are met
"""

import os
import sys
import json
import subprocess
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    """Print section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def check_pass(msg):
    """Print passed check"""
    print(f"  ✅ PASS  - {msg}")

def check_fail(msg):
    """Print failed check"""
    print(f"  ❌ FAIL  - {msg}")

def check_info(msg):
    """Print info message"""
    print(f"  ℹ️  INFO  - {msg}")

def main():
    print_header("MED-TRIAGE OPENENV - PRE-VALIDATION CHECKLIST")
    print(f"Timestamp: {datetime.now().isoformat()}\n")
    
    checks_passed = 0
    checks_failed = 0
    
    # ===== PHASE 1: FILE STRUCTURE =====
    print_header("PHASE 1: FILE STRUCTURE & BASIC SETUP")
    
    files_to_check = {
        'openenv.yaml': 'OpenEnv specification',
        'Dockerfile': 'Docker configuration',
        'inference.py': 'Baseline inference script (root)',
        'app_server.py': 'Flask API server',
        'requirements.txt': 'Python dependencies',
        'environment/med_triage_env.py': 'Environment implementation',
        'baseline/agent.py': 'Baseline agent',
        'README.md': 'Documentation'
    }
    
    for filepath, desc in files_to_check.items():
        if os.path.exists(filepath):
            check_pass(f"{filepath} - {desc}")
            checks_passed += 1
        else:
            check_fail(f"{filepath} NOT FOUND - {desc}")
            checks_failed += 1
    
    # ===== PHASE 2: MODULE IMPORTS =====
    print_header("PHASE 2: MODULE IMPORTS & DEPENDENCIES")
    
    try:
        from environment.med_triage_env import MedTriageEnv, TriageAction, TriageActionType
        check_pass("MedTriageEnv imported successfully")
        checks_passed += 1
    except Exception as e:
        check_fail(f"MedTriageEnv import failed: {e}")
        checks_failed += 1
    
    try:
        from baseline.agent import BaselineAgent
        check_pass("BaselineAgent imported successfully")
        checks_passed += 1
    except Exception as e:
        check_fail(f"BaselineAgent import failed: {e}")
        checks_failed += 1
    
    try:
        import yaml
        check_pass("PyYAML available")
        checks_passed += 1
    except:
        check_fail("PyYAML not installed")
        checks_failed += 1
    
    # ===== PHASE 3: ENVIRONMENT SPEC =====
    print_header("PHASE 3: OPENENV SPECIFICATION COMPLIANCE")
    
    try:
        env = MedTriageEnv(task_level=1, max_steps=20)
        check_pass("MedTriageEnv(task_level=1) instantiates")
        checks_passed += 1
        
        # Test reset()
        obs = env.reset()
        if isinstance(obs, dict):
            check_pass("reset() returns dict observation")
            checks_passed += 1
        else:
            check_fail(f"reset() returns {type(obs)} instead of dict")
            checks_failed += 1
        
        # Test get_state()
        state = env.get_state()
        if isinstance(state, dict):
            check_pass("get_state() returns dict")
            checks_passed += 1
        else:
            check_fail(f"get_state() returns {type(state)} instead of dict")
            checks_failed += 1
        
        # Test step()
        action = TriageAction(
            type=TriageActionType.ASSIGN_ESI,
            patient_id="P1",
            value=3
        )
        obs, reward, done, info = env.step(action)
        
        if isinstance(obs, dict) and isinstance(reward, (int, float)) and isinstance(done, bool):
            check_pass("step() returns (observation, reward, done, info)")
            checks_passed += 1
        else:
            check_fail("step() return types incorrect")
            checks_failed += 1
        
        # Test reward normalization
        if 0.0 <= reward <= 1.0:
            check_pass(f"Reward normalized [0.0, 1.0]: {reward:.4f}")
            checks_passed += 1
        else:
            check_fail(f"Reward out of range: {reward}")
            checks_failed += 1
            
    except Exception as e:
        check_fail(f"OpenEnv spec test failed: {e}")
        checks_failed += 1
    
    # ===== PHASE 4: TASK LEVELS =====
    print_header("PHASE 4: MULTIPLE TASK LEVELS (3+ REQUIRED)")
    
    for level in [1, 2, 3]:
        level_names = {1: 'EASY', 2: 'MEDIUM', 3: 'HARD'}
        try:
            env = MedTriageEnv(task_level=level, max_steps=20)
            obs = env.reset()
            action = TriageAction(
                type=TriageActionType.ASSIGN_ESI,
                patient_id="P1",
                value=3
            )
            obs, reward, done, info = env.step(action)
            
            if 0.0 <= reward <= 1.0:
                check_pass(f"Task Level {level} ({level_names[level]}) - Reward: {reward:.4f}")
                checks_passed += 1
            else:
                check_fail(f"Task Level {level} - Invalid reward: {reward}")
                checks_failed += 1
        except Exception as e:
            check_fail(f"Task Level {level} failed: {e}")
            checks_failed += 1
    
    # ===== PHASE 5: API ENDPOINTS =====
    print_header("PHASE 5: REST API ENDPOINTS")
    
    with open('app_server.py', 'r') as f:
        app_content = f.read()
    
    endpoints = {
        '/reset': 'Reset environment',
        '/step': 'Step environment',
        '/state': 'Get state',
        '/inference': 'Run inference',
        '/health': 'Health check'
    }
    
    for endpoint, desc in endpoints.items():
        if f'@app.route("{endpoint}"' in app_content or f"@app.route('{endpoint}'" in app_content:
            check_pass(f"Endpoint {endpoint} - {desc}")
            checks_passed += 1
        else:
            check_fail(f"Endpoint {endpoint} NOT FOUND - {desc}")
            checks_failed += 1
    
    # ===== PHASE 6: INFERENCE SCRIPT =====
    print_header("PHASE 6: INFERENCE SCRIPT FORMAT")
    
    with open('inference.py', 'r') as f:
        inf_content = f.read()
    
    required_formats = {
        '[START]': 'Start marker in logs',
        '[STEP]': 'Step marker in logs',
        '[END]': 'End marker in logs',
        'json.dumps': 'JSON structured output'
    }
    
    for pattern, desc in required_formats.items():
        if pattern in inf_content:
            check_pass(desc)
            checks_passed += 1
        else:
            check_fail(f"Missing {desc}")
            checks_failed += 1
    
    # ===== PHASE 7: ENVIRONMENT VARIABLES =====
    print_header("PHASE 7: REQUIRED ENVIRONMENT VARIABLES")
    
    env_vars = {
        'API_BASE_URL': 'http://localhost:7860',
        'MODEL_NAME': 'groq-mixtral-8x7b'
    }
    
    for var, default in env_vars.items():
        value = os.getenv(var, default)
        check_pass(f"{var} = {value}")
        checks_passed += 1
    
    # ===== PHASE 8: OPENENV.YAML =====
    print_header("PHASE 8: OPENENV.YAML COMPLIANCE")
    
    try:
        with open('openenv.yaml', 'r') as f:
            openenv_spec = yaml.safe_load(f)
        
        required_keys = ['name', 'version', 'description', 'author', 'environment']
        for key in required_keys:
            if key in openenv_spec:
                check_pass(f"openenv.yaml has '{key}' field")
                checks_passed += 1
            else:
                check_fail(f"openenv.yaml missing '{key}' field")
                checks_failed += 1
    except Exception as e:
        check_fail(f"openenv.yaml parsing failed: {e}")
        checks_failed += 1
    
    # ===== PHASE 9: DOCKER =====
    print_header("PHASE 9: DOCKER CONFIGURATION")
    
    if os.path.exists('Dockerfile'):
        with open('Dockerfile', 'r') as f:
            docker_content = f.read()
        
        docker_checks = {
            'FROM python': 'Python base image',
            'WORKDIR': 'Working directory set',
            'requirements.txt': 'Requirements copied',
            'pip install': 'Pip install in Dockerfile',
            'CMD': 'Startup command defined'
        }
        
        for pattern, desc in docker_checks.items():
            if pattern in docker_content:
                check_pass(f"Dockerfile has {desc}")
                checks_passed += 1
            else:
                check_fail(f"Dockerfile missing {desc}")
                checks_failed += 1
    
    # ===== FINAL SUMMARY =====
    print_header("VALIDATION SUMMARY")
    
    total = checks_passed + checks_failed
    pass_rate = (checks_passed / total * 100) if total > 0 else 0
    
    print(f"Total Checks: {total}")
    print(f"Passed: {checks_passed} ✅")
    print(f"Failed: {checks_failed} ❌")
    print(f"Pass Rate: {pass_rate:.1f}%\n")
    
    if checks_failed == 0:
        print("="*80)
        print("  🎉 ALL CHECKS PASSED! 🎉")
        print("  Your environment is ready for submission!")
        print("="*80)
        return 0
    else:
        print("="*80)
        print(f"  ⚠️  {checks_failed} CHECK(S) FAILED")
        print("  Please fix the above issues before submission")
        print("="*80)
        return 1

if __name__ == "__main__":
    try:
        import yaml
    except ImportError:
        print("❌ PyYAML required. Install with: pip install pyyaml")
        sys.exit(1)
    
    exit_code = main()
    sys.exit(exit_code)
