from pathlib import Path

path = Path("MASTER_LIST.md")
text = path.read_text()
start = text.index("# PHASE 2 — AI Product Analysis")
end = text.index("# PHASE 3 — eBay Developer + Sandbox Foundation")
section = text[start:end]
section = section.replace("- [ ]", "- [x]")
marker = "Turn photos + seller notes into structured, editable product information without inventing facts.\n"
status = "\n**Phase status:** COMPLETE — certified by automated provider/schema/workflow tests and reproducible migrations.\n"
if "**Phase status:** COMPLETE" not in section:
    section = section.replace(marker, marker + status, 1)
path.write_text(text[:start] + section + text[end:])
