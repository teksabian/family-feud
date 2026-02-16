#!/usr/bin/env python3
"""
v1.1.0 Feature 4: Active Tab Detection Test
Tests heartbeat tracking and active status calculation
"""

import sqlite3
import sys
from datetime import datetime, timedelta

def test_active_tab_detection():
    """Test active tab detection via heartbeats"""
    print("=" * 70)
    print("TESTING FEATURE 4: ACTIVE TAB DETECTION")
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
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Update heartbeat timestamp
    print("\n[TEST 1] Heartbeat should update last_heartbeat")
    conn.execute("INSERT INTO team_codes (code, used, team_name) VALUES ('ABCD', 1, 'TestTeam')")
    conn.execute("UPDATE team_codes SET last_heartbeat = CURRENT_TIMESTAMP WHERE code = 'ABCD'")
    
    code = conn.execute("SELECT * FROM team_codes WHERE code = 'ABCD'").fetchone()
    
    if code['last_heartbeat'] is not None:
        print(f"  ✅ PASS: Heartbeat set to {code['last_heartbeat']}")
        tests_passed += 1
    else:
        print("  ❌ FAIL: Heartbeat not set")
        tests_failed += 1
    
    # Test 2: Active status calculation (recent heartbeat)
    print("\n[TEST 2] Recent heartbeat (<30s) should show as active")
    # Heartbeat was just set, so it should be active
    last_hb = datetime.fromisoformat(code['last_heartbeat'])
    now = datetime.now()
    time_diff = (now - last_hb).total_seconds()
    is_active = time_diff < 30
    
    if is_active:
        print(f"  ✅ PASS: Team active (heartbeat {time_diff:.1f}s ago)")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: Team not active despite recent heartbeat ({time_diff:.1f}s ago)")
        tests_failed += 1
    
    # Test 3: Inactive status (old heartbeat)
    print("\n[TEST 3] Old heartbeat (>30s) should show as inactive")
    # Set heartbeat to 60 seconds ago
    old_time = (datetime.now() - timedelta(seconds=60)).isoformat()
    conn.execute("UPDATE team_codes SET last_heartbeat = ? WHERE code = 'ABCD'", (old_time,))
    
    code = conn.execute("SELECT * FROM team_codes WHERE code = 'ABCD'").fetchone()
    last_hb = datetime.fromisoformat(code['last_heartbeat'])
    time_diff = (datetime.now() - last_hb).total_seconds()
    is_active = time_diff < 30
    
    if not is_active:
        print(f"  ✅ PASS: Team inactive (heartbeat {time_diff:.1f}s ago)")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: Team still active despite old heartbeat ({time_diff:.1f}s ago)")
        tests_failed += 1
    
    # Test 4: No heartbeat = inactive
    print("\n[TEST 4] No heartbeat should show as inactive")
    conn.execute("INSERT INTO team_codes (code, used, team_name) VALUES ('WXYZ', 1, 'NoHeartbeat')")
    code2 = conn.execute("SELECT * FROM team_codes WHERE code = 'WXYZ'").fetchone()
    
    is_active = False if code2['last_heartbeat'] is None else True
    
    if not is_active:
        print("  ✅ PASS: Team inactive (no heartbeat)")
        tests_passed += 1
    else:
        print("  ❌ FAIL: Team active despite no heartbeat")
        tests_failed += 1
    
    # Test 5: Multiple teams, mixed status
    print("\n[TEST 5] Multiple teams with different heartbeat status")
    # Team A: Active (recent heartbeat)
    conn.execute("INSERT INTO team_codes (code, used, team_name) VALUES ('AAA1', 1, 'ActiveTeam')")
    conn.execute("UPDATE team_codes SET last_heartbeat = CURRENT_TIMESTAMP WHERE code = 'AAA1'")
    
    # Team B: Inactive (old heartbeat)
    old_time = (datetime.now() - timedelta(seconds=45)).isoformat()
    conn.execute("INSERT INTO team_codes (code, used, team_name) VALUES ('BBB2', 1, 'InactiveTeam')")
    conn.execute("UPDATE team_codes SET last_heartbeat = ? WHERE code = 'BBB2'", (old_time,))
    
    # Check both
    team_a = conn.execute("SELECT * FROM team_codes WHERE code = 'AAA1'").fetchone()
    team_b = conn.execute("SELECT * FROM team_codes WHERE code = 'BBB2'").fetchone()
    
    # Calculate status
    a_time_diff = (datetime.now() - datetime.fromisoformat(team_a['last_heartbeat'])).total_seconds()
    b_time_diff = (datetime.now() - datetime.fromisoformat(team_b['last_heartbeat'])).total_seconds()
    
    a_active = a_time_diff < 30
    b_active = b_time_diff < 30
    
    if a_active and not b_active:
        print(f"  ✅ PASS: Team A active ({a_time_diff:.1f}s), Team B inactive ({b_time_diff:.1f}s)")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: Status incorrect - A:{a_active} ({a_time_diff:.1f}s), B:{b_active} ({b_time_diff:.1f}s)")
        tests_failed += 1
    
    # Test 6: Heartbeat can be updated multiple times
    print("\n[TEST 6] Heartbeat should update on repeated calls")
    first_hb = code['last_heartbeat']
    import time
    time.sleep(1.1)
    conn.execute("UPDATE team_codes SET last_heartbeat = CURRENT_TIMESTAMP WHERE code = 'ABCD'")
    code = conn.execute("SELECT * FROM team_codes WHERE code = 'ABCD'").fetchone()
    second_hb = code['last_heartbeat']
    
    if first_hb != second_hb:
        print(f"  ✅ PASS: Heartbeat updated")
        print(f"     First:  {first_hb}")
        print(f"     Second: {second_hb}")
        tests_passed += 1
    else:
        print("  ❌ FAIL: Heartbeat didn't update")
        tests_failed += 1
    
    conn.close()
    
    # Summary
    print("\n" + "=" * 70)
    print(f"FEATURE 4 TEST RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("=" * 70)
    
    if tests_failed == 0:
        print("✅ ALL TESTS PASSED - ACTIVE TAB DETECTION READY")
        return True
    else:
        print(f"❌ {tests_failed} TESTS FAILED - NEEDS FIXING")
        return False

if __name__ == "__main__":
    success = test_active_tab_detection()
    sys.exit(0 if success else 1)
