## Summary

<!-- What does this change? One or two sentences. -->

## Motivation / related issue

<!-- Why is it needed? Link issues with "Fixes #123". -->

## Implementation notes

<!-- Anything a reviewer should know: approach, trade-offs, parts that are easy to get wrong. -->

## Testing performed

- [ ] `backend/.venv/bin/ruff check .`
- [ ] `python3 scripts/check_docs.py`
- [ ] `backend/.venv/bin/python -m pytest backend`
- [ ] `cd frontend && npm run lint && npm run typecheck && npm test && npm run build` (frontend changes)
- [ ] New behaviour has tests; no existing test was weakened or removed
- [ ] Tried it in the app (describe what you did, OS and AI mode):

## Screenshots (UI changes)

<!-- Light and dark theme if relevant. Remove personal data from screenshots. -->

## Breaking changes / upgrade notes

<!-- "None", or what users must change. Database changes must be additive migrations with an upgrade test. -->

## Checklist

- [ ] No new network calls in local mode; cloud use stays opt-in
- [ ] Documentation updated (README, `docs/`, `.env.example` for new settings)
- [ ] `CHANGELOG.md` updated under *Unreleased*
- [ ] I did not include secrets, resumes, interview answers or other personal data
