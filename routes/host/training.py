"""AI training data (corrections) save and clear routes."""

import os
import json
import base64
import urllib.request
import urllib.error
from flask import jsonify

from config import logger, GITHUB_TOKEN, GITHUB_REPO, CORRECTIONS_FILE
from auth import host_required
from database import db_connect
from ai import load_corrections_history

from routes.host import host_bp


@host_bp.route('/host/save-training', methods=['POST'])
@host_required
def save_training():
    """Save AI corrections to GitHub repo for long-term persistence."""
    if not GITHUB_TOKEN:
        return jsonify({'success': False, 'error': 'GITHUB_TOKEN not configured. Set it in Render environment variables.'}), 400

    corrections = load_corrections_history()
    if not corrections:
        return jsonify({'success': False, 'error': 'No corrections to save.'}), 400

    try:
        file_path = 'corrections_history.json'
        api_url = f'https://api.github.com/repos/{GITHUB_REPO}/contents/{file_path}'

        # First, get the current file SHA (needed for updates)
        get_req = urllib.request.Request(api_url, headers={
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json'
        })

        existing_sha = None
        existing_data = []
        try:
            with urllib.request.urlopen(get_req) as resp:
                file_info = json.loads(resp.read().decode())
                existing_sha = file_info.get('sha')
                # Decode existing content and merge
                existing_content = base64.b64decode(file_info.get('content', '')).decode('utf-8')
                existing_data = json.loads(existing_content) if existing_content.strip() else []
        except urllib.error.HTTPError as e:
            if e.code == 404:
                existing_data = []  # File doesn't exist yet
            else:
                raise

        # Merge: add new corrections that aren't already in the file
        # Use a simple dedup by converting to comparable tuples
        existing_set = set()
        for c in existing_data:
            key = (c.get('team_answer', ''), c.get('survey_answer', ''), c.get('correction_type', ''), c.get('question', ''))
            existing_set.add(key)

        new_corrections = []
        for c in corrections:
            key = (c.get('team_answer', ''), c.get('survey_answer', ''), c.get('correction_type', ''), c.get('question', ''))
            if key not in existing_set:
                new_corrections.append(c)

        if not new_corrections:
            return jsonify({'success': True, 'message': f'All {len(corrections)} corrections already saved. No new data.'})

        merged = existing_data + new_corrections
        content_b64 = base64.b64encode(json.dumps(merged, indent=2).encode('utf-8')).decode('utf-8')

        # Commit to GitHub
        payload = json.dumps({
            'message': f'Update AI training data (+{len(new_corrections)} corrections, {len(merged)} total)',
            'content': content_b64,
            'sha': existing_sha  # None if new file
        }).encode('utf-8')

        # Remove sha key if None (new file)
        payload_dict = json.loads(payload)
        if payload_dict.get('sha') is None:
            del payload_dict['sha']
        payload = json.dumps(payload_dict).encode('utf-8')

        put_req = urllib.request.Request(api_url, data=payload, method='PUT', headers={
            'Authorization': f'token {GITHUB_TOKEN}',
            'Accept': 'application/vnd.github.v3+json',
            'Content-Type': 'application/json'
        })

        with urllib.request.urlopen(put_req) as resp:
            if resp.status in (200, 201):
                logger.info(f"[AI-CORRECTIONS] Saved {len(new_corrections)} new corrections to GitHub ({len(merged)} total)")
                return jsonify({'success': True, 'message': f'Saved {len(new_corrections)} new corrections to GitHub ({len(merged)} total)'})

        return jsonify({'success': False, 'error': 'Unexpected response from GitHub'}), 500

    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else str(e)
        logger.error(f"[AI-CORRECTIONS] GitHub API error: {e.code} - {error_body}")
        return jsonify({'success': False, 'error': f'GitHub API error ({e.code}). Check your token permissions.'}), 500
    except Exception as e:
        logger.error(f"[AI-CORRECTIONS] Failed to save to GitHub: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@host_bp.route('/host/clear-training', methods=['POST'])
@host_required
def clear_training():
    """Clear all AI training corrections from local file and database."""
    try:
        # Clear the local JSON file
        with open(CORRECTIONS_FILE, 'w') as f:
            json.dump([], f)
        logger.info("[AI-CORRECTIONS] Cleared corrections_history.json")

        # Clear the database table
        with db_connect() as conn:
            conn.execute("DELETE FROM ai_corrections")
            conn.commit()
        logger.info("[AI-CORRECTIONS] Cleared ai_corrections table")

        return jsonify({'success': True, 'message': 'All training data cleared.'})
    except Exception as e:
        logger.error(f"[AI-CORRECTIONS] Failed to clear training data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
