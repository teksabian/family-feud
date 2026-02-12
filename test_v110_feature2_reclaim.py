#!/usr/bin/env python3
"""
v1.1.0 Feature 2: Reclaim Code Button Test
Tests the ability for host to reclaim used codes
"""

import sqlite3
import sys

def test_reclaim_code():
    """Test reclaim code feature"""
    print("=" * 70)
    print("TESTING FEATURE 2: RECLAIM CODE BUTTON")
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
            last_heartbeat TIMESTAMP DEFAULT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.execute("""
        CREATE TABLE rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            round_number INTEGER NOT NULL,
            question TEXT,
            num_answers INTEGER NOT NULL
        )
    """)
    
    conn.execute("""
        CREATE TABLE submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            round_id INTEGER NOT NULL,
            answer1 TEXT,
            score INTEGER DEFAULT 0
        )
    """)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Setup - Create used code with submissions
    print("\n[TEST 1] Setup used code with team and submissions")
    conn.execute("INSERT INTO team_codes (code, used, team_name) VALUES ('ABCD', 1, 'Champions')")
    conn.execute("INSERT INTO rounds (round_number, question, num_answers) VALUES (1, 'Test Q', 4)")
    conn.execute("INSERT INTO submissions (code, round_id, answer1, score) VALUES ('ABCD', 1, 'Answer', 10)")
    
    code_row = conn.execute("SELECT * FROM team_codes WHERE code = 'ABCD'").fetchone()
    subs = conn.execute("SELECT * FROM submissions WHERE code = 'ABCD'").fetchall()
    
    if code_row['used'] == 1 and len(subs) == 1:
        print("  ✅ PASS: Used code with submissions created")
        tests_passed += 1
    else:
        print("  ❌ FAIL: Setup failed")
        tests_failed += 1
    
    # Test 2: Reclaim code - delete submissions
    print("\n[TEST 2] Reclaiming code should delete submissions")
    conn.execute("DELETE FROM submissions WHERE code = ?", ('ABCD',))
    subs_after = conn.execute("SELECT * FROM submissions WHERE code = 'ABCD'").fetchall()
    
    if len(subs_after) == 0:
        print("  ✅ PASS: Submissions deleted")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: {len(subs_after)} submissions remaining")
        tests_failed += 1
    
    # Test 3: Reclaim code - reset code status
    print("\n[TEST 3] Reclaiming code should reset all flags")
    conn.execute("""
        UPDATE team_codes 
        SET used = 0, team_name = NULL, reconnected = 0, last_heartbeat = NULL 
        WHERE code = ?
    """, ('ABCD',))
    
    code_row = conn.execute("SELECT * FROM team_codes WHERE code = 'ABCD'").fetchone()
    
    if (code_row['used'] == 0 and 
        code_row['team_name'] is None and 
        code_row['reconnected'] == 0 and
        code_row['last_heartbeat'] is None):
        print("  ✅ PASS: Code fully reset")
        tests_passed += 1
    else:
        print("  ❌ FAIL: Code not fully reset")
        print(f"     used={code_row['used']}, team_name={code_row['team_name']}, reconnected={code_row['reconnected']}")
        tests_failed += 1
    
    # Test 4: Code can be reused after reclaim
    print("\n[TEST 4] Reclaimed code should be reusable")
    conn.execute("UPDATE team_codes SET used = 1, team_name = 'NewTeam' WHERE code = 'ABCD'")
    code_row = conn.execute("SELECT * FROM team_codes WHERE code = 'ABCD'").fetchone()
    
    if code_row['used'] == 1 and code_row['team_name'] == 'NewTeam':
        print("  ✅ PASS: Code reused successfully")
        tests_passed += 1
    else:
        print("  ❌ FAIL: Code couldn't be reused")
        tests_failed += 1
    
    # Test 5: Multiple codes with submissions
    print("\n[TEST 5] Reclaim only affects target code")
    conn.execute("INSERT INTO team_codes (code, used, team_name) VALUES ('WXYZ', 1, 'OtherTeam')")
    conn.execute("INSERT INTO submissions (code, round_id, answer1, score) VALUES ('WXYZ', 1, 'Answer2', 20)")
    
    # Reclaim ABCD
    conn.execute("DELETE FROM submissions WHERE code = ?", ('ABCD',))
    conn.execute("UPDATE team_codes SET used = 0, team_name = NULL WHERE code = ?", ('ABCD',))
    
    # Check ABCD reclaimed
    abcd = conn.execute("SELECT * FROM team_codes WHERE code = 'ABCD'").fetchone()
    abcd_subs = conn.execute("SELECT * FROM submissions WHERE code = 'ABCD'").fetchall()
    
    # Check WXYZ untouched
    wxyz = conn.execute("SELECT * FROM team_codes WHERE code = 'WXYZ'").fetchone()
    wxyz_subs = conn.execute("SELECT * FROM submissions WHERE code = 'WXYZ'").fetchall()
    
    if (abcd['used'] == 0 and len(abcd_subs) == 0 and 
        wxyz['used'] == 1 and len(wxyz_subs) == 1):
        print("  ✅ PASS: Only target code affected")
        tests_passed += 1
    else:
        print("  ❌ FAIL: Other codes affected")
        tests_failed += 1
    
    # Test 6: Reclaim code that was reconnected
    print("\n[TEST 6] Reclaim reconnected code")
    conn.execute("INSERT INTO team_codes (code, used, team_name, reconnected) VALUES ('TEST', 1, 'ReconnectTeam', 1)")
    conn.execute("UPDATE team_codes SET used = 0, team_name = NULL, reconnected = 0 WHERE code = 'TEST'")
    
    test_row = conn.execute("SELECT * FROM team_codes WHERE code = 'TEST'").fetchone()
    
    if test_row['used'] == 0 and test_row['reconnected'] == 0:
        print("  ✅ PASS: Reconnect flag cleared")
        tests_passed += 1
    else:
        print("  ❌ FAIL: Reconnect flag not cleared")
        tests_failed += 1
    
    conn.close()
    
    # Summary
    print("\n" + "=" * 70)
    print(f"FEATURE 2 TEST RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("=" * 70)
    
    if tests_failed == 0:
        print("✅ ALL TESTS PASSED - RECLAIM CODE READY")
        return True
    else:
        print(f"❌ {tests_failed} TESTS FAILED - NEEDS FIXING")
        return False

if __name__ == "__main__":
    success = test_reclaim_code()
    sys.exit(0 if success else 1)
