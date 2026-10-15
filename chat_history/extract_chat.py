import json
import os

transcript_path = "/Users/ibrahim/.gemini/antigravity/brain/c5996103-2ce3-4292-832f-af058b3ec3db/.system_generated/logs/transcript_full.jsonl"
out_path = "/Users/ibrahim/Desktop/Uni/Graduation/Code_and_Data/MCDM_System/MCDM(new)/chat_transcript.md"

if not os.path.exists(transcript_path):
    print("Transcript not found.")
    exit(1)

with open(transcript_path, 'r') as f:
    lines = f.readlines()

with open(out_path, 'w') as out:
    out.write("# Conversation Transcript\n\n")
    for line in lines:
        if not line.strip(): continue
        try:
            data = json.loads(line)
        except:
            continue
            
        source = data.get('source', 'UNKNOWN')
        step_type = data.get('type', '')
        content = data.get('content', '')
        created_at = data.get('created_at', '')
        
        if step_type == 'USER_INPUT':
            out.write(f"## 👤 User ({created_at})\n\n")
            out.write(f"{content}\n\n---\n\n")
        elif step_type == 'PLANNER_RESPONSE':
            out.write(f"## 🤖 Assistant ({created_at})\n\n")
            # Include thought process if requested, but let's just include the content
            out.write(f"{content}\n\n---\n\n")

print(f"Chat successfully extracted to {out_path}")
