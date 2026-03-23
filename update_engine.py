import os

file_path = r'C:\Users\Akshith\Downloads\2026\MREM\SatyaSathi-Health-ID\backend\ml\analysis_engine.py'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace assignments fetching avg
text = text.replace('bp_avg = features.get("bp_systolic_avg")', 'bp_avg = features.get("bp_systolic_latest", features.get("bp_systolic_avg"))')
text = text.replace('sugar_avg = features.get("sugar_avg")', 'sugar_avg = features.get("sugar_latest", features.get("sugar_avg"))')

# Also handle default values
text = text.replace('bp_avg = features.get("bp_systolic_avg", 120)', 'bp_avg = features.get("bp_systolic_latest", features.get("bp_systolic_avg", 120))')
text = text.replace('sugar_avg = features.get("sugar_avg", 100)', 'sugar_avg = features.get("sugar_latest", features.get("sugar_avg", 100))')
text = text.replace('sugar_avg = features.get("sugar_avg", 90)', 'sugar_avg = features.get("sugar_latest", features.get("sugar_avg", 90))')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(text)

print('Updated analysis_engine.py to use latest vitals')
