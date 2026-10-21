"""Learning models and scoring. No Streamlit, network, or filesystem writes."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta

ANALYSIS = ('company', 'competitors', 'customers', 'collaborators', 'climate')
STRATEGY = ('segmentation', 'targeting', 'positioning')
QUESTIONS = ANALYSIS + STRATEGY + ('concept_check',)
MASTER_THRESHOLD = 75
VERSION = 2


def default_progress():
    return {'version': VERSION, 'attempts': {}, 'reviews': {}}


def question(scenario, key):
    if key in ANALYSIS:
        return scenario['analysis_questions'][key]
    if key in STRATEGY:
        return scenario['steps'][key]
    return scenario['concept_check']


def score_attempt(scenario, draft):
    results = {}
    for key in QUESTIONS:
        q = question(scenario, key)
        selected = draft.get('answers', {}).get(key)
        correct = selected == q['correct_idx']
        results[key] = {'selected': selected, 'correct': correct,
                        'points': (4 if key in ANALYSIS else 20) if correct else 0}
    points = sum(r['points'] for r in results.values())
    supported = bool(draft.get('hints') or draft.get('revealed') or draft.get('revised'))
    return {'id': draft['id'], 'at': datetime.now(timezone.utc).isoformat(),
            'content_version': scenario.get('content_version', 1),
            'points': points, 'supported': supported, 'results': results,
            'answers': deepcopy(draft.get('answers', {})),
            'notes': deepcopy(draft.get('notes', {})),
            'explanation': draft.get('explanation', ''),
            'transfer': draft.get('transfer', ''),
            'hints': list(draft.get('hints', [])),
            'revealed': list(draft.get('revealed', [])),
            'revised': list(draft.get('revised', []))}


def record_attempt(progress, sid, attempt):
    """Idempotent submission: reruns cannot duplicate an attempt."""
    history = progress['attempts'].setdefault(str(sid), [])
    if not any(a['id'] == attempt['id'] for a in history):
        history.append(deepcopy(attempt))


def summary(progress, sid):
    history = progress['attempts'].get(str(sid), [])
    return {'count': len(history), 'first': history[0] if history else None,
            'latest': history[-1] if history else None,
            'best': max((a['points'] for a in history), default=0),
            'independent': any(a['points'] >= MASTER_THRESHOLD and not a['supported'] for a in history)}


def review_due(attempt, now=None):
    now = now or datetime.now(timezone.utc)
    return now >= datetime.fromisoformat(attempt['at']) + timedelta(days=2)


def strategy_brief(scenario, attempt):
    lines = [f"# {scenario['title']}", '', '## Evidence notebook']
    for key, note in attempt.get('notes', {}).items():
        lines += [f"### {key.title()}", note.get('evidence', ''), note.get('implication', ''), '']
    lines += ['## Decisions']
    for key in STRATEGY:
        idx = attempt.get('answers', {}).get(key)
        if idx is not None:
            lines += [f"**{key.title()}:** {question(scenario, key)['options'][idx]}", '']
    lines += ['## My reasoning', attempt.get('explanation', ''), '', '## Changed conditions', attempt.get('transfer', '')]
    return '\n'.join(lines)
