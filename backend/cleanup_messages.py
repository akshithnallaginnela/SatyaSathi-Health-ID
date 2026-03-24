import os

filepath = r"c:\Users\Akshith\Downloads\2026\MREM\SatyaSathi-Health-ID\backend\ml\analysis_engine.py"

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace Sugar section
old_sugar = """                "current_status": f"Sugar slightly elevated — {sugar_val:.0f} mg/dL",
                "future_risk_message": (
                    f"Your sugar is slightly above the ideal range. "
                    "The fantastic news? Research shows that at this stage, "
                    "lifestyle changes can fully reverse the trend in 8-12 weeks. "
                    "You have complete control here."
                ),
                "prevention_steps": [
                    "Switch to brown rice or millets — they taste great and help a lot",
                    "A 10-min walk after meals reduces sugar spikes by 22%",
                    "Try nuts as snacks instead of biscuits — equally satisfying",
                    "You caught this early — that's the smartest health decision"
                ],
                "risk_horizon": "8-12 weeks of dietary changes can reverse this"
            })"""

new_sugar = """                "current_status": f"Sugar slightly elevated — {sugar_val:.0f} mg/dL",
                "future_risk_message": (
                    "You've caught this early! Small changes like walking 10 min "
                    "after lunch can reverse this in just 8-12 weeks."
                ),
                "prevention_steps": [
                    "Walk for 10 mins after meals — works like magic ✨",
                    "Switch to brown rice or millets instead of white rice",
                    "Try nuts as snacks instead of biscuits — equally satisfying"
                ],
                "risk_horizon": "8-12 weeks to fully reset"
            })"""

# Replace Hemoglobin section
old_hb = """                "current_status": f"Hemoglobin needs attention — {hb} g/dL",
                "future_risk_message": (
                    f"Your hemoglobin is {hb} g/dL, which is below ideal for your profile. "
                    "The good news? Increasing iron-rich foods like leafy greens, "
                    "legumes and seeds can bring this back to normal in a few weeks."
                ),
                "prevention_steps": [
                    "Incorporate more iron-rich foods into your daily meals",
                    "A follow-up test in 4 weeks will help track your progress",
                    "Consider a doctor-guided iron supplement if needed",
                    "You're taking charge of your energy levels — great work"
                ],
                "risk_horizon": "4 weeks of iron-rich focus"
            })"""

new_hb = """                "current_status": f"Hb needs focus — {hb} g/dL",
                "future_risk_message": (
                    "You caught this at the right time! Adding iron-rich foods like "
                    "spinach or dates can boost levels in 4-6 weeks."
                ),
                "prevention_steps": [
                    "Add iron-rich foods ( spinach, dates, dal ) to daily meals",
                    "A follow-up test in 30 days will show your progress",
                    "You're in control — small diet tweaks go a long way"
                ],
                "risk_horizon": "30 days of iron-focus = Results"
            })"""

# Replace Platelets section
old_plt = """                "current_status": f"Platelets need medical attention — {platelets:,}/cumm",
                "future_risk_message": (
                    "Your platelet count needs a doctor's attention. This could be "
                    "temporary and often resolves with treatment. A doctor visit "
                    "will help you understand the cause and get the right care."
                ),
                "prevention_steps": [
                    "See your doctor in the next few days for guidance",
                    "Retest CBC after 3-5 days of rest",
                    "Maintain hydration and minimize physical strain",
                    "You're tracking this carefully — that's great focus"
                ],
                "risk_horizon": "Doctor guidance + rest"
            })"""

new_plt = """                "current_status": f"Platelets need focus — {platelets:,}/cumm",
                "future_risk_message": (
                    "Focus on rest and quality nutrients this week. "
                    "A quick doctor consult will give you a clear action plan."
                ),
                "prevention_steps": [
                    "Visit your doctor this week for clear guidance",
                    "Add Anjeer and leafy greens to your daily diet",
                    "Prioritize quality sleep to help your body recover"
                ],
                "risk_horizon": "Rest + Precise nutrients = Results"
            })"""

if old_sugar in content:
    content = content.replace(old_sugar, new_sugar)
    print("Replaced Sugar")
if old_hb in content:
    content = content.replace(old_hb, new_hb)
    print("Replaced HB")
if old_plt in content:
    content = content.replace(old_plt, new_plt)
    print("Replaced PLT")

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(content)

print("Done.")
