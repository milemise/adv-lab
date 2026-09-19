def review_submission(title: str, description: str) -> dict:
    text = f'{title} {description}'.strip().lower()
    score = 0.9 if text else 0.2
    return {'approved_suggestion': score >= 0.75, 'score': score, 'reason': 'Revisión preliminar local'}
