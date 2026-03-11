import re
import unicodedata

def normalize_for_search(text: str) -> str:
    if not text:
        return ""
    nfkd_form = unicodedata.normalize('NFKD', text)
    text = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s]', '', text) # Fixed typo 0-0 -> 0-9
    text = re.sub(r'\s+', ' ', text).strip()
    return text

target = "EM 1 TI GEOGRAFIA 10 03 26 INDUSTRIALIZACAO MUNDIAL II P2.mp4"
drive_file = "EM 1 TI GEOGRAFIA 10 03 26 INDUSTRIALIZAÇÃO MUNDIAL II P2.mp4"

target_norm = normalize_for_search(target.replace(".mp4", ""))
drive_norm = normalize_for_search(drive_file.replace(".mp4", ""))

print(f"Target: {target}")
print(f"Norm  : {target_norm}")
print(f"Drive : {drive_file}")
print(f"Norm  : {drive_norm}")
print(f"Match : {target_norm == drive_norm or target_norm in drive_norm or drive_norm in target_norm}")

# Check date extraction
match_data = re.search(r'(\d{2}\s\d{2}\s\d{2})', target)
print(f"Date Match: {match_data.group(1) if match_data else 'None'}")
