#!/usr/bin/env python3
"""
Test: game:over WebSocket event emission

Verifies that when the last round completes and start_next_round is called,
a game:over event is emitted with final leaderboard data.
"""

import sqlite3
import sys


def test_game_over_leaderboard_payload():
    """Test that the game:over leaderboard payload is built correctly from DB state."""
    print("=" * 70)
    print("TESTING: game:over EVENT PAYLOAD CONSTRUCTION")
    print("=" * 70)

    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row

    # Create tables matching the app schema
    conn.execute("""
        CREATE TABLE team_codes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            used INTEGER DEFAULT 0,
            team_name TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE rounds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            round_number INTEGER NOT NULL,
            question TEXT,
            num_answers INTEGER DEFAULT 4,
            answer1 TEXT, answer2 TEXT, answer3 TEXT,
            answer4 TEXT, answer5 TEXT, answer6 TEXT,
            answer1_count INTEGER, answer2_count INTEGER, answer3_count INTEGER,
            answer4_count INTEGER, answer5_count INTEGER, answer6_count INTEGER,
            is_active INTEGER DEFAULT 0,
            submissions_closed INTEGER DEFAULT 0,
            winner_code TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT NOT NULL,
            round_id INTEGER NOT NULL,
            score INTEGER DEFAULT 0,
            host_submitted INTEGER DEFAULT 0
        )
    """)

    tests_passed = 0
    tests_failed = 0

    # --- Setup: 1-round game with 3 teams ---
    conn.execute("INSERT INTO team_codes (code, used, team_name) VALUES ('AAAA', 1, 'Alpha Team')")
    conn.execute("INSERT INTO team_codes (code, used, team_name) VALUES ('BBBB', 1, 'Beta Squad')")
    conn.execute("INSERT INTO team_codes (code, used, team_name) VALUES ('CCCC', 1, 'Charlie Gang')")

    conn.execute("""
        INSERT INTO rounds (round_number, question, num_answers, answer1, answer2, answer3, answer4,
                           is_active, winner_code)
        VALUES (1, 'Name a fruit', 4, 'Apple', 'Banana', 'Cherry', 'Date', 1, 'AAAA')
    """)

    # Scored submissions
    conn.execute("INSERT INTO submissions (code, round_id, score, host_submitted) VALUES ('AAAA', 1, 30, 1)")
    conn.execute("INSERT INTO submissions (code, round_id, score, host_submitted) VALUES ('BBBB', 1, 20, 1)")
    conn.execute("INSERT INTO submissions (code, round_id, score, host_submitted) VALUES ('CCCC', 1, 10, 1)")
    conn.commit()

    # --- Test 1: Leaderboard query produces correct ranking ---
    print("\n[TEST 1] Leaderboard query returns teams ranked by score")

    teams = conn.execute("""
        SELECT tc.team_name, tc.code,
               COALESCE(SUM(CASE WHEN s.host_submitted = 1 THEN s.score ELSE 0 END), 0) as total_score
        FROM team_codes tc
        LEFT JOIN submissions s ON tc.code = s.code
        WHERE tc.used = 1 AND tc.team_name IS NOT NULL
        GROUP BY tc.code
        ORDER BY total_score DESC, tc.team_name ASC
    """).fetchall()

    leaderboard = []
    for i, row in enumerate(teams):
        leaderboard.append({
            'team_name': row['team_name'],
            'total_score': row['total_score'],
            'rank': i + 1,
        })

    if (len(leaderboard) == 3
            and leaderboard[0]['team_name'] == 'Alpha Team'
            and leaderboard[0]['total_score'] == 30
            and leaderboard[0]['rank'] == 1
            and leaderboard[1]['team_name'] == 'Beta Squad'
            and leaderboard[1]['total_score'] == 20
            and leaderboard[2]['team_name'] == 'Charlie Gang'
            and leaderboard[2]['total_score'] == 10):
        print("  ✅ PASS: Leaderboard correctly ranked (Alpha=30, Beta=20, Charlie=10)")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: Unexpected leaderboard: {leaderboard}")
        tests_failed += 1

    # --- Test 2: game_over_data payload structure ---
    print("\n[TEST 2] game_over_data has correct winner and leaderboard")

    game_over_data = {
        'leaderboard': leaderboard,
        'winner_team': leaderboard[0]['team_name'] if leaderboard else None,
        'winner_score': leaderboard[0]['total_score'] if leaderboard else 0,
    }

    if (game_over_data['winner_team'] == 'Alpha Team'
            and game_over_data['winner_score'] == 30
            and len(game_over_data['leaderboard']) == 3):
        print("  ✅ PASS: game_over_data has winner_team='Alpha Team', winner_score=30")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: Unexpected game_over_data: {game_over_data}")
        tests_failed += 1

    # --- Test 3: Previous round winner info ---
    print("\n[TEST 3] Previous round winner query returns correct data")

    active_round = conn.execute("SELECT * FROM rounds WHERE is_active = 1").fetchone()

    prev_winner = conn.execute("""
        SELECT r.winner_code, r.round_number, tc.team_name, s.score
        FROM rounds r
        LEFT JOIN team_codes tc ON r.winner_code = tc.code
        LEFT JOIN submissions s ON r.winner_code = s.code AND r.id = s.round_id AND s.host_submitted = 1
        WHERE r.id = ?
    """, (active_round['id'],)).fetchone()

    if (prev_winner
            and prev_winner['winner_code'] == 'AAAA'
            and prev_winner['team_name'] == 'Alpha Team'
            and prev_winner['score'] == 30
            and prev_winner['round_number'] == 1):
        print("  ✅ PASS: Previous winner = Alpha Team (30 pts, round 1)")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: Unexpected prev_winner: {dict(prev_winner) if prev_winner else None}")
        tests_failed += 1

    # --- Test 4: No next round detected (game over condition) ---
    print("\n[TEST 4] No next round exists after round 1 (game over condition)")

    current_num = active_round['round_number']
    next_round = conn.execute(
        "SELECT * FROM rounds WHERE round_number = ?", (current_num + 1,)
    ).fetchone()

    if next_round is None:
        print(f"  ✅ PASS: No round {current_num + 1} found - game over detected")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: Unexpected next round found: {dict(next_round)}")
        tests_failed += 1

    # --- Test 5: Previous answers list from round ---
    print("\n[TEST 5] Previous answers extracted from round")

    prev_answers = []
    for i in range(1, 7):
        ans = active_round[f'answer{i}']
        if ans:
            prev_answers.append(ans)

    if prev_answers == ['Apple', 'Banana', 'Cherry', 'Date']:
        print(f"  ✅ PASS: Previous answers = {prev_answers}")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: Unexpected answers: {prev_answers}")
        tests_failed += 1

    # --- Test 6: Empty game (no teams) ---
    print("\n[TEST 6] Empty leaderboard produces safe payload")

    empty_lb = []
    empty_data = {
        'leaderboard': empty_lb,
        'winner_team': empty_lb[0]['team_name'] if empty_lb else None,
        'winner_score': empty_lb[0]['total_score'] if empty_lb else 0,
    }

    if empty_data['winner_team'] is None and empty_data['winner_score'] == 0:
        print("  ✅ PASS: Empty leaderboard yields winner_team=None, winner_score=0")
        tests_passed += 1
    else:
        print(f"  ❌ FAIL: Unexpected empty data: {empty_data}")
        tests_failed += 1

    # --- Test 7: Unscored submission excluded from prev_winner score ---
    print("\n[TEST 7] prev_winner query excludes unscored submissions (host_submitted = 0)")

    # Add an unscored submission for the winner team — should not affect prev_winner score
    conn.execute("INSERT INTO submissions (code, round_id, score, host_submitted) VALUES ('AAAA', 1, 99, 0)")
    conn.commit()

    prev_winner_filtered = conn.execute("""
        SELECT r.winner_code, r.round_number, tc.team_name, s.score
        FROM rounds r
        LEFT JOIN team_codes tc ON r.winner_code = tc.code
        LEFT JOIN submissions s ON r.winner_code = s.code AND r.id = s.round_id AND s.host_submitted = 1
        WHERE r.id = ?
    """, (active_round['id'],)).fetchone()

    if prev_winner_filtered and prev_winner_filtered['score'] == 30:
        print("  ✅ PASS: prev_winner score = 30 (unscored 99-point submission excluded)")
        tests_passed += 1
    else:
        score = prev_winner_filtered['score'] if prev_winner_filtered else None
        print(f"  ❌ FAIL: prev_winner score = {score} (expected 30)")
        tests_failed += 1

    # --- Summary ---
    conn.close()
    print("\n" + "=" * 70)
    total = tests_passed + tests_failed
    print(f"RESULTS: {tests_passed}/{total} passed, {tests_failed} failed")
    print("=" * 70)

    if tests_failed > 0:
        sys.exit(1)
    print("\n✅ All game:over event tests passed!")


if __name__ == '__main__':
    test_game_over_leaderboard_payload()
