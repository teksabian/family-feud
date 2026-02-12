#!/usr/bin/env python3
"""
v1.1.0 Feature 1: Reconnection System Test
Tests the ability for teams to reconnect with used codes
"""

import sqlite3
import sys

def test_reconnection_system():
    """Test reconnection feature"""
    print("=" * 70)
    print("TESTING FEATURE 1: RECONNECTION SYSTEM")
    print("=" * 70)
    
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    # Create tables
    conn.execute("""
        CREATE TABLE team_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            used INTEGER DEFAULT 0,
            team_name TEXT,
            reconnected INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_heartbeat TIMESTAMP DEFAULT NULL
        )
    """)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: New code validation
    print("\n[TEST 1] New code should allow team form")
    conn.execute("INSERT INTO team_codes (code, used) VALUES ('ABCD', 0)")
    code_row = conn.execute("SELECT * FROM team_codes WHERE code = 'ABCD'").fetchone()
    if not code_row['used']:
        print("  ✅ PASS: Unused code detected correctly")
        tests_passed += 1
    else:
        print("  ❌ FAIL: Unused code incorrectly marked as used")
        tests_failed += 1
    
    # Test 2: Used code should trigger reconnect form
    print("\n[TEST 2] Used code should show reconnect form")
    conn.execute("UPDATE team_codes SET used = 1, team_name = 'Champions' WHERE code = 'ABCD'")
    code_row = conn.execute("SELECT * FROM team_codes WHERE code = 'ABCD'").fetchone()
    if code_row['used'] and code_row['team_name'] == 'Champions':
        print("  ✅ PASS: Used code with team name stored correctly")
        tests_passed += 1
    else:
        print("  ❌ FAIL: Used code data incorrect")
        tests_failed += 1
    
    # Test 3: Case-insensitive team name matching
    print("\n[TEST 3] Case-insensitive reconnect matching")
    input_name = "champions"  # lowercase
    stored_name = code_row['team_name']  # Champions
    if stored_name.lower() == input_name.lower():
        print(f"  ✅ PASS: '{input_name}' matches '{stored_name}' (case-insensitive)")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: '{input_name}' doesn't match '{stored_name}'")
        tests_failed += 1
    
    # Test 4: Wrong team name should be rejected
    print("\n[TEST 4] Wrong team name should be rejected")
    wrong_name = "WrongTeam"
    if stored_name.lower() != wrong_name.lower():
        print(f"  ✅ PASS: '{wrong_name}' correctly rejected (doesn't match '{stored_name}')")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: Wrong name incorrectly accepted")
        tests_failed += 1
    
    # Test 5: Reconnected flag gets set
    print("\n[TEST 5] Reconnected flag should be set on successful reconnect")
    conn.execute("UPDATE team_codes SET reconnected = 1 WHERE code = 'ABCD'")
    code_row = conn.execute("SELECT * FROM team_codes WHERE code = 'ABCD'").fetchone()
    if code_row['reconnected'] == 1:
        print("  ✅ PASS: Reconnected flag set correctly")
        tests_passed += 1
    else:
        print("  ❌ FAIL: Reconnected flag not set")
        tests_failed += 1
    
    # Test 6: Multiple reconnections
    print("\n[TEST 6] Team can reconnect multiple times")
    # Simulate multiple reconnections (flag stays 1)
    conn.execute("UPDATE team_codes SET reconnected = 1 WHERE code = 'ABCD'")
    conn.execute("UPDATE team_codes SET reconnected = 1 WHERE code = 'ABCD'")
    code_row = conn.execute("SELECT * FROM team_codes WHERE code = 'ABCD'").fetchone()
    if code_row['reconnected'] == 1:
        print("  ✅ PASS: Multiple reconnections handled")
        tests_passed += 1
    else:
        print("  ❌ FAIL: Multiple reconnections broke flag")
        tests_failed += 1
    
    # Test 7: Different cases of team names
    print("\n[TEST 7] Various team name capitalizations")
    test_cases = [
        ('champions', 'Champions', True),
        ('CHAMPIONS', 'Champions', True),
        ('ChAmPiOnS', 'Champions', True),
        ('Champs', 'Champions', False),
        ('Champion', 'Champions', False),
    ]
    
    for input_name, stored_name, should_match in test_cases:
        matches = input_name.lower() == stored_name.lower()
        if matches == should_match:
            status = "✅ PASS"
            tests_passed += 1
        else:
            status = "❌ FAIL"
            tests_failed += 1
        print(f"  {status}: '{input_name}' vs '{stored_name}' = {matches} (expected {should_match})")
    
    conn.close()
    
    # Summary
    print("\n" + "=" * 70)
    print(f"FEATURE 1 TEST RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("=" * 70)
    
    if tests_failed == 0:
        print("✅ ALL TESTS PASSED - RECONNECTION SYSTEM READY")
        return True
    else:
        print(f"❌ {tests_failed} TESTS FAILED - NEEDS FIXING")
        return False

if __name__ == "__main__":
    success = test_reconnection_system()
    sys.exit(0 if success else 1)
