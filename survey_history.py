"""
Persistent survey history for AI-generated rounds.

Saves completed AI-generated surveys to survey_history.json so they
can be reused or referenced later. Survives server restarts.
"""

import base64
import json
import os
import urllib.error
import urllib.request
from datetime import datetime

from config import logger, SURVEY_HISTORY_FILE, GITHUB_TOKEN, GITHUB_REPO

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

        # Push to GitHub so history survives ephemeral filesystem restarts
        _push_to_github(history)
    except Exception as e:
        logger.warning(f"[SURVEY-HISTORY] Failed to save survey: {e}")


def _push_to_github(history):
    """Push survey_history.json to GitHub via the Contents API."""
    if not GITHUB_TOKEN:
        logger.info("[SURVEY-HISTORY] GITHUB_TOKEN not set, skipping GitHub push")
        return

    try:
        file_path = 'survey_history.json'
        api_url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}'

        # Get current file SHA (needed for updates)
        get_req = urllib.request.Request(api_url, headers={
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json',
        })

        existing_sha = None
        try:
            with urllib.request.urlopen(get_req) as resp:
                file_info = json.loads(resp.read().decode())
                existing_sha = file_info.get('sha')
        except urllib.error.HTTPError as e:
            if e.code != 404:
                raise

        # PUT updated content
        content_b64 = base64.b64encode(json.dumps(history, indent=2).encode('utf-8')).decode('utf-8')
        payload = {
            'message': f'Update survey history ({len(history)} surveys)',
            'content': content_b64,
        }
        if existing_sha:
            payload['sha'] = existing_sha

        put_req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode('utf-8'),
            method='PUT',
            headers={
                'Authorization': f'token {GITHUB_TOKEN}',
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json',
            },
        )

        with urllib.request.urlopen(put_req) as resp:
            if resp.status in (200, 201):
                logger.info(f"[SURVEY-HISTORY] Pushed survey history to GitHub ({len(history)} surveys)")

    except Exception as e:
        logger.warning(f"[SURVEY-HISTORY] GitHub push failed: {e}")


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
