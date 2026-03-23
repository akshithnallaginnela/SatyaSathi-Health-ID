def generate_preventive_care(features: dict, signals: dict) -> list[dict]:
    care_items = []

    # ── BP PREVENTIVE CARE ────────────────────────────────────
    sys_avg   = features.get("systolic_avg_7d", 0)
    sys_trend = features.get("systolic_trend", 0)
    days_130  = features.get("days_above_130", 0)

    if sys_avg > 0:

        if sys_avg < 120 and sys_trend <= 0.3:
            care_items.append({
                "category": "blood_pressure",
                "urgency": "maintain",
                "current_status": f"Normal ({sys_avg:.0f} avg this week)",
                "future_risk_message": (
                    "Your BP is in a healthy range right now. "
                    "People with your profile have a chance of "
                    "developing elevated BP in their 40s if "
                    "current lifestyle continues."
                ),
                "prevention_steps": [
                    "Keep daily sodium intake below 2300mg",
                    "Maintain at least 4 days of walking per week",
                    "Keep stress managed — it is the #1 hidden BP driver",
                    "Stay hydrated — 8 glasses minimum daily"
                ],
                "risk_horizon": "5–10 years if lifestyle unchanged"
            })

        elif 120 <= sys_avg < 130 and sys_trend < 0.5:
            care_items.append({
                "category": "blood_pressure",
                "urgency": "watch",
                "current_status": f"Slightly elevated ({sys_avg:.0f} avg)",
                "future_risk_message": (
                    "Your BP is in the 'elevated' zone this week. "
                    "If this continues for 4–6 more weeks without "
                    "change, it may move into the high-normal range. "
                    "The good news — this is completely reversible "
                    "with small consistent habits."
                ),
                "prevention_steps": [
                    "Cut added salt from your meals this week",
                    "Walk 30 minutes daily — reduces BP by 5–8 mmHg",
                    "Reduce caffeine to 1 cup per day",
                    "Practice 5-minute deep breathing every evening",
                    "Avoid late-night heavy meals"
                ],
                "risk_horizon": "4–6 weeks if no action taken"
            })

        elif sys_avg >= 130 or (sys_avg >= 120 and sys_trend > 0.8):
            care_items.append({
                "category": "blood_pressure",
                "urgency": "act_now",
                "current_status": f"Trending high ({sys_avg:.0f} avg, {'rising' if sys_trend > 0 else 'stable'})",
                "future_risk_message": (
                    f"Your BP has been consistently above 130 for "
                    f"{days_130} of the last 7 days and is trending "
                    "upward. If this continues for 2–3 more weeks, "
                    "a doctor visit will be strongly recommended. "
                    "Acting now can reverse this trend completely."
                ),
                "prevention_steps": [
                    "Stop added salt completely for 2 weeks",
                    "Walk 10,000 steps daily — start today",
                    "No alcohol this week",
                    "Sleep before 10:30 PM — poor sleep raises BP",
                    "Log your BP every morning to track progress",
                    "Book a routine checkup if no improvement in 10 days"
                ],
                "risk_horizon": "2–3 weeks if trend continues"
            })

    # ── SUGAR PREVENTIVE CARE ─────────────────────────────────
    sg_avg   = features.get("fasting_sugar_avg", 0)
    sg_above = features.get("sugar_readings_above_100", 0)
    sg_trend = features.get("sugar_trend_slope", 0)

    if sg_avg > 0:

        if sg_avg < 100 and sg_trend <= 0.5:
            care_items.append({
                "category": "blood_sugar",
                "urgency": "maintain",
                "current_status": f"Normal ({sg_avg:.0f} mg/dL avg)",
                "future_risk_message": (
                    "Your fasting sugar is healthy right now. "
                    "With your profile, maintaining this requires "
                    "watching carbohydrate intake as you age. "
                    "Prevention now is far easier than treatment later."
                ),
                "prevention_steps": [
                    "Avoid sugary drinks — even fruit juice",
                    "Walk 10 minutes after every major meal",
                    "Include protein in every meal to slow sugar absorption",
                    "Get your sugar checked every 3 months"
                ],
                "risk_horizon": "Long-term maintenance"
            })

        elif 100 <= sg_avg < 126 or sg_above >= 2:
            care_items.append({
                "category": "blood_sugar",
                "urgency": "watch",
                "current_status": f"Pre-diabetic range ({sg_avg:.0f} mg/dL avg, {sg_above} readings above 100)",
                "future_risk_message": (
                    f"Your fasting sugar has been above 100 mg/dL "
                    f"in {sg_above} of your recent readings. "
                    "This is the pre-diabetic range — not diabetes, "
                    "but a clear signal to act. Research shows that "
                    "lifestyle changes at this stage can fully "
                    "reverse the trend in 8–12 weeks."
                ),
                "prevention_steps": [
                    "Replace white rice with brown rice or millets",
                    "Eliminate sugar from tea and coffee",
                    "Walk 30 minutes every morning before breakfast",
                    "Eat dinner before 7:30 PM",
                    "Avoid fruit juices — eat whole fruits instead",
                    "Get HbA1c tested — gives 3-month sugar picture"
                ],
                "risk_horizon": "8–12 weeks to reverse with lifestyle changes"
            })

        elif sg_avg >= 126:
            care_items.append({
                "category": "blood_sugar",
                "urgency": "act_now",
                "current_status": f"Consistently elevated ({sg_avg:.0f} mg/dL avg)",
                "future_risk_message": (
                    "Your average fasting sugar has been above "
                    "126 mg/dL. This pattern needs medical evaluation. "
                    "A single high reading is not concerning — but a "
                    "consistent pattern like this warrants a proper "
                    "doctor visit and HbA1c test."
                ),
                "prevention_steps": [
                    "Visit a doctor for HbA1c test this week",
                    "Stop all sugary foods completely",
                    "Walk 45 minutes daily — morning is best",
                    "Log your sugar every day this week",
                    "Eat small meals every 3 hours"
                ],
                "risk_horizon": "Immediate — doctor visit recommended"
            })

    # ── PLATELET PREVENTIVE CARE ──────────────────────────────
    platelets = features.get("platelet_count", 0)
    if platelets > 0:

        if platelets < 100000:
            care_items.append({
                "category": "platelets",
                "urgency": "act_now",
                "current_status": f"Low platelets ({platelets:,} /cumm)",
                "future_risk_message": (
                    "Your platelet count is significantly below "
                    "the normal range (150,000–410,000). "
                    "This increases bleeding risk and needs "
                    "medical evaluation. This cannot be reversed "
                    "through lifestyle alone."
                ),
                "prevention_steps": [
                    "See a doctor within the next few days",
                    "Avoid aspirin and ibuprofen completely",
                    "Avoid activities with injury risk",
                    "Eat papaya and pomegranate — may help mildly",
                    "Stay hydrated — 10+ glasses daily",
                    "Report any unusual bruising immediately"
                ],
                "risk_horizon": "Immediate medical evaluation needed"
            })

        elif 100000 <= platelets < 150000:
            care_items.append({
                "category": "platelets",
                "urgency": "watch",
                "current_status": f"Borderline low platelets ({platelets:,})",
                "future_risk_message": (
                    "Your platelet count is in the borderline-low "
                    "range. This alone is often not serious but "
                    "warrants monitoring. A retest in 2–3 weeks "
                    "will confirm whether this is a temporary "
                    "fluctuation or a persistent pattern."
                ),
                "prevention_steps": [
                    "Retest CBC in 2–3 weeks",
                    "Eat papaya leaf extract — traditional remedy",
                    "Include pomegranate and green leafy vegetables",
                    "Avoid alcohol completely",
                    "Stay well hydrated",
                    "Mention to your doctor at next visit"
                ],
                "risk_horizon": "Retest in 2–3 weeks"
            })

    # ── HEMOGLOBIN PREVENTIVE CARE ────────────────────────────
    hb     = features.get("hemoglobin", 0)
    gender = "male" if features.get("gender_enc", 1) == 1 else "female"
    hb_lo  = 13.5 if gender == "male" else 12.0

    if hb > 0:
        if hb < hb_lo - 1.5:
            care_items.append({
                "category": "hemoglobin",
                "urgency": "act_now",
                "current_status": f"Low hemoglobin ({hb} g/dL)",
                "future_risk_message": (
                    "Your hemoglobin is significantly below normal. "
                    "This causes fatigue, breathlessness, and reduced "
                    "immunity. If untreated, it worsens over time and "
                    "can affect heart function. Iron deficiency anemia "
                    "is the most common cause — very treatable."
                ),
                "prevention_steps": [
                    "See a doctor to confirm cause of anemia",
                    "Eat iron-rich foods: spinach, lentils, red meat, dates, jaggery",
                    "Take iron supplement if advised by doctor",
                    "Eat vitamin C with iron foods — aids absorption",
                    "Avoid tea/coffee 1 hour after iron-rich meals",
                    "Retest CBC in 6 weeks after dietary changes"
                ],
                "risk_horizon": "6 weeks to see improvement with diet"
            })

        elif hb < hb_lo:
            care_items.append({
                "category": "hemoglobin",
                "urgency": "watch",
                "current_status": f"Slightly low hemoglobin ({hb} g/dL)",
                "future_risk_message": (
                    "Your hemoglobin is slightly below the normal "
                    "range for your gender. You may be experiencing "
                    "mild fatigue or tiredness. If dietary habits "
                    "do not change, this could worsen gradually "
                    "over the next few months."
                ),
                "prevention_steps": [
                    "Increase iron-rich foods daily: spinach, dal, chicken, eggs",
                    "Add jaggery or dates as snacks",
                    "Eat citrus fruit daily — boosts iron absorption",
                    "Reduce tea/coffee — blocks iron absorption",
                    "Retest in 8 weeks"
                ],
                "risk_horizon": "8 weeks dietary window"
            })

    return care_items
