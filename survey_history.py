"""
Persistent survey history for AI-generated rounds.

Saves completed AI-generated surveys to survey_history.json so they
can be reused or referenced later. Survives server restarts.
"""

import json
import os
import subprocess
from datetime import datetime

from config import logger, SURVEY_HISTORY_FILE

MAX_SURVEYS = 80  # ~10 weeks of games (8 rounds each)


def load_survey_history():
    """Load all saved surveys from the history file."""
    try:
        if os.path.exists(SURVEY_HISTORY_FILE):
            with open(SURVEY_HISTORY_FILE, 'r') as f:
                data = json.load(f)
                logger.info(f"[SURVEY-HISTORY] Loaded {len(data)} surveys from history")
                return data
    except Exception as e:
        logger.warning(f"[SURVEY-HISTORY] Failed to load history: {e}")
    return []


def save_survey_history(rounds_rows):
    """Save a completed AI-generated game's surveys to history.

    Args:
        rounds_rows: list of sqlite3.Row objects from the rounds table
    """
    try:
        history = load_survey_history()

        survey = {
            "saved_at": datetime.now().isoformat(),
            "rounds": [],
        }

        for row in rounds_rows:
            round_data = {
                "round_number": row["round_number"],
                "question": row["question"],
                "num_answers": row["num_answers"],
                "answers": [],
            }
            for i in range(1, row["num_answers"] + 1):
                answer_text = row[f"answer{i}"]
                answer_count = row[f"answer{i}_count"]
                if answer_text:
                    round_data["answers"].append({
                        "text": answer_text,
                        "points": answer_count or 0,
                    })
            survey["rounds"].append(round_data)

        history.append(survey)

        # Trim to last MAX_SURVEYS to avoid unbounded growth
        if len(history) > MAX_SURVEYS:
            history = history[-MAX_SURVEYS:]

        with open(SURVEY_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)

        logger.info(f"[SURVEY-HISTORY] Saved survey with {len(survey['rounds'])} rounds (total in history: {len(history)})")

        # Commit to repo so history survives ephemeral filesystem restarts
        _commit_history()
    except Exception as e:
        logger.warning(f"[SURVEY-HISTORY] Failed to save survey: {e}")


def _commit_history():
    """Commit and push survey_history.json so it persists across deploys."""
    try:
        subprocess.run(
            ["git", "add", SURVEY_HISTORY_FILE],
            check=True, capture_output=True, timeout=10,
        )
        subprocess.run(
            ["git", "commit", "-m", "Update survey history"],
            check=True, capture_output=True, timeout=10,
        )
        subprocess.run(
            ["git", "push"],
            check=True, capture_output=True, timeout=30,
        )
        logger.info("[SURVEY-HISTORY] Committed and pushed survey history to repo")
    except subprocess.CalledProcessError as e:
        logger.warning(f"[SURVEY-HISTORY] Git commit/push failed: {e.stderr}")
    except Exception as e:
        logger.warning(f"[SURVEY-HISTORY] Git commit/push failed: {e}")


def build_past_questions_block():
    """Build a prompt block listing all previously used questions.

    Returns a string to inject into AI generation prompts so the AI
    avoids repeating questions from past games.
    """
    history = load_survey_history()
    if not history:
        return ''

    past_questions = []
    for survey in history:
        for rd in survey.get('rounds', []):
            q = rd.get('question', '').strip()
            if q:
                past_questions.append(q)

    if not past_questions:
        return ''

    # Deduplicate while preserving order
    seen = set()
    unique = []
    for q in past_questions:
        if q.lower() not in seen:
            seen.add(q.lower())
            unique.append(q)

    lines = [f'- {q}' for q in unique]
    block = (
        "IMPORTANT: Do NOT reuse any of these previously used questions:\n"
        + '\n'.join(lines)
    )
    logger.info(f"[SURVEY-HISTORY] Built past questions block with {len(unique)} questions")
    return block
