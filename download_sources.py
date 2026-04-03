import json
import subprocess
import os

with open('nlm_sources.txt', 'r') as f:
    sources = json.load(f)

# The user has existing local sources in `sources/`, we use a dedicated folder for these NotebookLM extractions to prevent destruction.
folder = 'notebooklm_research_extracts'
os.makedirs(folder, exist_ok=True)

for index, source in enumerate(sources):
    source_id = source['id']
    # Create safe filename from the title
    title = source.get('title', 'Unknown_Source')
    safe_name = "".join([c if c.isalnum() else "_" for c in title])[:80]
    output_path = os.path.join(folder, f"{index:02d}_{safe_name}.txt")
    
    print(f"Downloading [{index+1}/{len(sources)}]: {title}")
    cmd = [".venv-nlm/bin/nlm", "source", "content", source_id, "-o", output_path]
    
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Failed to download {title}: {e}")

print("Extraction script complete.")
