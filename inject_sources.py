import json
import os

with open('nlm_sources.txt', 'r') as f:
    sources = json.load(f)

input_folder = 'notebooklm_research_extracts'
output_folder = 'sources/shared'

os.makedirs(output_folder, exist_ok=True)

for index, source in enumerate(sources):
    title = source.get('title', 'Unknown_Source')
    url = source.get('url', 'No URL provided (PDF/Generated Text)')
    
    # Needs to strictly match the exact logic we used to generate the filenames
    safe_name = "".join([c if c.isalnum() else "_" for c in title])[:80]
    input_txt = os.path.join(input_folder, f"{index:02d}_{safe_name}.txt")
    output_txt = os.path.join(output_folder, f"{index:02d}_{safe_name}.txt")
    
    if os.path.exists(input_txt):
        with open(input_txt, 'r', encoding='utf-8') as f:
            content = f.read()
            
        referenced_content = f"Title: {title}\nSource URL: {url}\n\n" + ("="*80) + "\n\n" + content
        
        with open(output_txt, 'w', encoding='utf-8') as out_f:
            out_f.write(referenced_content)
        print(f"Propagated: {output_txt}")
    else:
        print(f"Skipped (Not Found): {input_txt}")

print("Successfully injected links and copied to /sources/shared/")
