# Fresh-clone dry run (do this before submitting)

This copies exactly what the teaching staff will do. If it breaks here, it will break for them.
Use a **brand-new folder** and follow **only the README**, not memory.

1. ☐ Push your latest code to GitHub, then confirm the repo is **public** (or `zlisto` is a collaborator:
   repo **Settings → Collaborators → Add people**).
2. ☐ Make a new test folder that mimics theirs, with a `.env` one level above the repo:
   ```bash
   mkdir -p ~/Desktop/dryrun && cd ~/Desktop/dryrun
   cp "/Users/marydimitrov/AI Foundations/.env" .env     # your key, one level ABOVE the repo
   git clone https://github.com/<your-username>/<repo-name>.git lead-finder
   cd lead-finder
   ```
3. ☐ Start a timer. Run the one command from the README: `bash setup_and_run.sh`
4. ☐ The browser opens at http://localhost:8501 (or open it yourself). Note the time: ______ (must be well under 10 minutes)
5. ☐ Press **▶ Run the example**. A progress bar appears and lead cards show up within ~2 minutes.
6. ☐ Click every tab: **Leads**, **Dismissed**, **Run trace**, **Tokens & cost**. Nothing errors.
7. ☐ In a second terminal in the same folder: `.venv/bin/python -m pytest -q` → all tests pass.
8. ☐ Confirm no secret got in: `ls -a` shows **no** `.env` inside `lead-finder/`, and
   `git log --all -p | grep -i "PORTKEY_API_KEY=."` prints nothing.
9. ☐ Stop the app with `Ctrl+C`. Delete `~/Desktop/dryrun`.

If any step fails: write down the exact error message and fix it in the real repo, push, and repeat
from step 2 in a new folder.
