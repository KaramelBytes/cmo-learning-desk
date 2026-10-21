"""Opt-in browser storage and strict, bounded backup validation."""
import json
from pathlib import Path
import streamlit.components.v1 as components
from learning import default_progress, QUESTIONS, question

browser_store = components.declare_component('cmo_browser_store', path=str(Path(__file__).resolve().parents[1] / 'components' / 'browser_store'))
MAX_BYTES = 2_000_000


def make_payload(progress, draft):
    return {'version': 2, 'progress': progress, 'draft': draft}


def validate_payload(raw, scenarios):
    """Rebuild trusted structures instead of merging arbitrary imported state."""
    if isinstance(raw, (str, bytes)):
        if len(raw) > MAX_BYTES:
            raise ValueError('Backup is too large (maximum 2 MB).')
        raw = json.loads(raw)
    if len(json.dumps(raw)) > MAX_BYTES:
        raise ValueError('Backup is too large (maximum 2 MB).')
    if not isinstance(raw, dict) or raw.get('version') != 2:
        raise ValueError('Choose a CMO Desk version 2 backup.')
    catalog = {str(s['scenario_id']): s for s in scenarios}

    def text(value, limit=4000):
        if not isinstance(value, str) or len(value) > limit:
            raise ValueError('Invalid or oversized text in backup.')
        return value

    def answers(value, scenario):
        if not isinstance(value, dict):
            raise ValueError('Invalid answers.')
        clean = {}
        for key, idx in value.items():
            if key not in QUESTIONS or type(idx) is not int or not 0 <= idx < len(question(scenario, key)['options']):
                raise ValueError('Backup contains an invalid answer.')
            clean[key] = idx
        return clean

    def draft(value, scenario):
        if not isinstance(value, dict):
            raise ValueError('Invalid activity.')
        if value.get('content_version', 2) != scenario.get('content_version', 2):
            raise ValueError('This backup uses a different case content version.')
        clean = {'id': text(value['id'], 100), 'scenario_id': scenario['scenario_id'],
                 'content_version': scenario.get('content_version', 2),
                 'step': value.get('step', 0), 'answers': answers(value.get('answers', {}), scenario),
                 'notes': {}, 'checked': {}, 'hints': [], 'revealed': [], 'revised': []}
        if type(clean['step']) is not int or not 0 <= clean['step'] <= 11:
            raise ValueError('Invalid activity step.')
        for field in ('hints', 'revealed', 'revised'):
            if not isinstance(value.get(field, []), list) or any(k not in QUESTIONS for k in value.get(field, [])):
                raise ValueError('Invalid help history.')
            clean[field] = list(set(value.get(field, [])))
        for key, note in value.get('notes', {}).items():
            if key not in QUESTIONS[:5] or not isinstance(note, dict):
                raise ValueError('Invalid notebook.')
            clean['notes'][key] = {k: text(note.get(k, '')) for k in ('evidence', 'implication')}
        for key, idx in value.get('checked', {}).items():
            if key not in clean['answers'] or idx != clean['answers'][key]:
                raise ValueError('Invalid checked answer.')
            clean['checked'][key] = idx
        for field in ('explanation', 'transfer'):
            clean[field] = text(value.get(field, ''))
        return clean

    progress_raw = raw.get('progress')
    if not isinstance(progress_raw, dict) or not isinstance(progress_raw.get('attempts'), dict):
        raise ValueError('Invalid learning history.')
    progress = default_progress()
    from datetime import datetime
    from learning import score_attempt
    for sid, history in progress_raw['attempts'].items():
        if sid not in catalog or not isinstance(history, list) or len(history) > 200:
            raise ValueError('Unknown case or too many attempts.')
        progress['attempts'][sid] = []
        ids = set()
        for attempt in history:
            clean = draft(attempt, catalog[sid])
            if set(clean['answers']) != set(QUESTIONS) or clean['id'] in ids:
                raise ValueError('Incomplete or duplicate attempt.')
            ids.add(clean['id'])
            scored = score_attempt(catalog[sid], clean)
            at = text(attempt['at'], 100)
            if datetime.fromisoformat(at).tzinfo is None:
                raise ValueError('Invalid attempt date.')
            scored['at'] = at
            progress['attempts'][sid].append(scored)
    # Review answers are re-evaluated by the app; import only valid question keys.
    for key, value in progress_raw.get('reviews', {}).items():
        sid, qkey = key.split(':')
        if sid not in catalog or qkey not in QUESTIONS or not isinstance(value, dict):
            raise ValueError('Invalid review history.')
        idx = answers({qkey: value['answer']}, catalog[sid])[qkey]
        at = text(value['at'], 100)
        if datetime.fromisoformat(at).tzinfo is None:
            raise ValueError('Invalid review date.')
        progress['reviews'][key] = {'answer': idx, 'at': at}
    active = raw.get('draft')
    if active is not None:
        sid = str(active['scenario_id'])
        if sid not in catalog:
            raise ValueError('Unknown active case.')
        active = draft(active, catalog[sid])
    return make_payload(progress, active)
