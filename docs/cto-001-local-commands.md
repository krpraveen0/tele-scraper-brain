# CTO-001 Local Command Guide

Run this only after pulling the CTO-001 branch.

```bash
git checkout feature/cto-001-cleanup-baseline
git pull
source .venv/bin/activate
python -m pytest -q
python -m app.main feedback-summary
python -m app.main assets --limit 5
python -m app.main feedback-profile --limit 50
streamlit run ui/streamlit_app.py
```

Manual Streamlit smoke flow:

1. Open the local Streamlit URL.
2. Confirm Dashboard loads.
3. Open Signals Inbox.
4. Select one signal.
5. Try one quick feedback action.
6. Try one quick asset generation action with `Save asset` enabled.
7. Open Asset Studio.
8. Open Briefings.
9. Open Feedback Profile.
10. Open Assets.

If any step fails, do not move to CTO-002. Create a bug ticket first.
