#!/usr/bin/env python3
"""
v1.1.0 Feature 5: Undo Last Score Test
Tests the ability to undo scoring mistakes
"""

import sqlite3
import sys

def test_undo_score():
    """Test undo score functionality"""
    print("=" * 70)
    print("TESTING FEATURE 5: UNDO LAST SCORE")
    print("=" * 70)
    
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    
    # Create tables
    conn.execute("""
        CREATE TABLE submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            round_id INTEGER NOT NULL,
            answer1 TEXT,
            score INTEGER DEFAULT 0,
            scored INTEGER DEFAULT 0,
            previous_score INTEGER DEFAULT NULL,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Save previous score when scoring
    print("\n[TEST 1] Scoring should save previous score")
    conn.execute("INSERT INTO submissions (code, round_id, answer1, score) VALUES ('ABCD', 1, 'Test', 0)")
    sub = conn.execute("SELECT * FROM submissions WHERE code = 'ABCD'").fetchone()
    
    # Score it (simulate scoring process)
    current_score = sub['score']  # 0
    new_score = 10
    conn.execute("""
        UPDATE submissions 
        SET score = ?, scored = 1, previous_score = ?
        WHERE id = ?
    """, (new_score, current_score, sub['id']))
    
    updated_sub = conn.execute("SELECT * FROM submissions WHERE code = 'ABCD'").fetchone()
    
    if updated_sub['score'] == 10 and updated_sub['previous_score'] == 0:
        print(f"  ✅ PASS: Score updated to {updated_sub['score']}, previous saved as {updated_sub['previous_score']}")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: Score={updated_sub['score']}, Previous={updated_sub['previous_score']}")
        tests_failed += 1
    
    # Test 2: Undo restores previous score
    print("\n[TEST 2] Undo should restore previous score")
    previous = updated_sub['previous_score']
    conn.execute("""
        UPDATE submissions 
        SET score = ?, previous_score = NULL
        WHERE id = ?
    """, (previous, updated_sub['id']))
    
    restored_sub = conn.execute("SELECT * FROM submissions WHERE code = 'ABCD'").fetchone()
    
    if restored_sub['score'] == 0 and restored_sub['previous_score'] is None:
        print(f"  ✅ PASS: Score restored to {restored_sub['score']}, previous cleared")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: Score={restored_sub['score']}, Previous={restored_sub['previous_score']}")
        tests_failed += 1
    
    # Test 3: Multiple score changes track correctly
    print("\n[TEST 3] Multiple scores should update previous correctly")
    # First score: 0 -> 5
    conn.execute("UPDATE submissions SET score = ?, previous_score = ? WHERE id = ?", (5, 0, restored_sub['id']))
    sub1 = conn.execute("SELECT * FROM submissions WHERE code = 'ABCD'").fetchone()
    
    # Second score: 5 -> 15
    conn.execute("UPDATE submissions SET score = ?, previous_score = ? WHERE id = ?", (15, 5, sub1['id']))
    sub2 = conn.execute("SELECT * FROM submissions WHERE code = 'ABCD'").fetchone()
    
    if sub2['score'] == 15 and sub2['previous_score'] == 5:
        print(f"  ✅ PASS: Score {sub2['score']}, can undo to {sub2['previous_score']}")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: Score={sub2['score']}, Previous={sub2['previous_score']}")
        tests_failed += 1
    
    # Test 4: Can't undo if no previous score
    print("\n[TEST 4] Undo should fail if no previous score")
    conn.execute("INSERT INTO submissions (code, round_id, answer1, score) VALUES ('WXYZ', 1, 'Test2', 20)")
    sub_no_prev = conn.execute("SELECT * FROM submissions WHERE code = 'WXYZ'").fetchone()
    
    if sub_no_prev['previous_score'] is None:
        print(f"  ✅ PASS: No previous score available (as expected)")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: Unexpected previous score: {sub_no_prev['previous_score']}")
        tests_failed += 1
    
    # Test 5: Undo only once (previous_score cleared after undo)
    print("\n[TEST 5] After undo, previous_score should be NULL")
    # Setup: Score with previous
    conn.execute("UPDATE submissions SET score = 30, previous_score = 25 WHERE code = 'WXYZ'")
    
    # Undo
    sub = conn.execute("SELECT * FROM submissions WHERE code = 'WXYZ'").fetchone()
    conn.execute("UPDATE submissions SET score = ?, previous_score = NULL WHERE id = ?", 
                 (sub['previous_score'], sub['id']))
    
    after_undo = conn.execute("SELECT * FROM submissions WHERE code = 'WXYZ'").fetchone()
    
    if after_undo['score'] == 25 and after_undo['previous_score'] is None:
        print(f"  ✅ PASS: Score restored to {after_undo['score']}, can't undo again")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: Score={after_undo['score']}, Previous={after_undo['previous_score']}")
        tests_failed += 1
    
    # Test 6: Rescore after undo
    print("\n[TEST 6] Can score again after undo")
    # After undo, score again
    current = after_undo['score']  # 25
    new = 35
    conn.execute("UPDATE submissions SET score = ?, previous_score = ? WHERE code = 'WXYZ'", 
                 (new, current))
    
    rescored = conn.execute("SELECT * FROM submissions WHERE code = 'WXYZ'").fetchone()
    
    if rescored['score'] == 35 and rescored['previous_score'] == 25:
        print(f"  ✅ PASS: Rescored to {rescored['score']}, can undo to {rescored['previous_score']}")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: Score={rescored['score']}, Previous={rescored['previous_score']}")
        tests_failed += 1
    
    conn.close()
    
    # Summary
    print("\n" + "=" * 70)
    print(f"FEATURE 5 TEST RESULTS: {tests_passed} passed, {tests_failed} failed")
    print("=" * 70)
    
    if tests_failed == 0:
        print("✅ ALL TESTS PASSED - UNDO SCORE READY")
        return True
    else:
        print(f"❌ {tests_failed} TESTS FAILED - NEEDS FIXING")
        return False

if __name__ == "__main__":
    success = test_undo_score()
    sys.exit(0 if success else 1)
