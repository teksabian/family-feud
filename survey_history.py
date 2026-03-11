"""
Persistent survey history for AI-generated rounds.

Saves completed AI-generated surveys to survey_history.json so they
can be reused or referenced later. Survives server restarts.
"""

import json
import os
from datetime import datetime

from config import logger, SURVEY_HISTORY_FILE


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

        with open(SURVEY_HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)

        logger.info(f"[SURVEY-HISTORY] Saved survey with {len(survey['rounds'])} rounds (total in history: {len(history)})")
    except Exception as e:
        logger.warning(f"[SURVEY-HISTORY] Failed to save survey: {e}")
