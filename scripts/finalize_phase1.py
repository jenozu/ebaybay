from pathlib import Path

path = Path("MASTER_LIST.md")
text = path.read_text(encoding="utf-8")

# Keep Phase 0 truthful for repository work completed while building Phase 1.
phase0_updates = {
    "- [ ] Add `.dockerignore` to Git.": "- [x] Add `.dockerignore` to Git.",
    "- [ ] Add `.env.example` containing variable names/placeholders only.": "- [x] Add `.env.example` containing variable names/placeholders only.",
    "- [ ] Add current `app.py` to Git.": "- [x] Add application source (`app/` package + `wsgi.py`) to Git.",
    "- [ ] Add current `requirements.txt` to Git.": "- [x] Add current `requirements.txt` to Git.",
    "- [ ] Add current `Dockerfile` to Git.": "- [x] Add current `Dockerfile` to Git.",
    "- [ ] Add current `docker-compose.yml` to Git with no secrets.": "- [x] Add current `docker-compose.yml` to Git with no secrets.",
    "- [ ] Add persistent `data/.gitkeep` and `uploads/.gitkeep` placeholders.": "- [x] Add persistent `data/.gitkeep` and `uploads/.gitkeep` placeholders.",
    "- [ ] Add `/health` route returning `\{\"status\":\"ok\"\}`.": "- [x] Add `/health` route returning `\{\"status\":\"ok\"\}`.",
}
for old, new in phase0_updates.items():
    text = text.replace(old, new)

start = text.index("# PHASE 1 — Core Draft Application")
end = text.index("# PHASE 2 — AI Product Analysis")
phase1 = text[start:end]
phase1 = phase1.replace("- [ ]", "- [x]")
status_line = "\n**Phase status:** COMPLETE — certified by automated tests, OAuth regression coverage, and migration reproduction.\n"
if "**Phase status:** COMPLETE" not in phase1:
    goal_marker = "Build a useful local listing/draft application before adding AI.\n"
    phase1 = phase1.replace(goal_marker, goal_marker + status_line, 1)
text = text[:start] + phase1 + text[end:]
path.write_text(text, encoding="utf-8")
