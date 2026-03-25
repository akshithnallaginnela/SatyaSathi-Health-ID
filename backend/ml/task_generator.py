def generate_daily_tasks(features: dict, signals: dict, user) -> list[dict]:
    """
    Returns list of tasks for TODAY.
    Always includes base tasks + signal-based tasks.
    Tasks update every time data changes.
    """
    tasks = []

    # ── ALWAYS INCLUDE (every user, every day) ────────────────

    tasks.append({
        "task_type": "WATER_INTAKE",
        "task_name": "Drink 8 glasses of water",
        "description": "Stay hydrated throughout the day",
        "why_this_task": (
            "Hydration supports kidney function, "
            "blood pressure, and overall health"
        ),
        "category": "wellness",
        "time_of_day": "all_day",
        "duration_or_quantity": "8 glasses (250ml each)",
        "coins_reward": 8
    })

    tasks.append({
        "task_type": "LOG_BP",
        "task_name": "Log your morning BP",
        "description": "Take and record your blood pressure",
        "why_this_task": (
            "Tracking your BP trend is how we "
            "spot problems before they develop"
        ),
        "category": "vitals",
        "time_of_day": "morning",
        "duration_or_quantity": "2 minute task",
        "coins_reward": 15
    })

    # ── BP-BASED TASKS ────────────────────────────────────────
    sys_avg   = features.get("systolic_avg_7d", 0)
    sys_trend = features.get("systolic_trend", 0)

    if sys_avg > 0:
        if sys_avg >= 120 or sys_trend > 0.3:
            tasks.append({
                "task_type": "MORNING_WALK",
                "task_name": "Walk 10,000 steps today",
                "description": "Brisk walking for at least 30 minutes",
                "why_this_task": (
                    "Walking reduces systolic BP by 5–8 mmHg "
                    "within 2 weeks of regular practice"
                ),
                "category": "exercise",
                "time_of_day": "morning",
                "duration_or_quantity": "30 min / 10,000 steps",
                "coins_reward": 0
            })

            tasks.append({
                "task_type": "DEEP_BREATHING",
                "task_name": "5-minute deep breathing",
                "description": "Slow belly breathing exercise",
                "why_this_task": (
                    "Activates the parasympathetic nervous system "
                    "and lowers BP within minutes"
                ),
                "category": "wellness",
                "time_of_day": "evening",
                "duration_or_quantity": "5 minutes",
                "coins_reward": 5
            })

            tasks.append({
                "task_type": "LOW_SALT_MEAL",
                "task_name": "Eat a low-salt meal today",
                "description": "Avoid pickles, packaged food, extra salt",
                "why_this_task": (
                    "Excess sodium is the #1 dietary cause of "
                    "elevated blood pressure"
                ),
                "category": "diet",
                "time_of_day": "afternoon",
                "duration_or_quantity": "All meals today",
                "coins_reward": 0
            })

        else:
            tasks.append({
                "task_type": "MORNING_WALK",
                "task_name": "Walk 7,000 steps today",
                "description": "Moderate daily walking",
                "why_this_task": (
                    "Maintaining an active lifestyle keeps "
                    "your BP in the healthy zone long-term"
                ),
                "category": "exercise",
                "time_of_day": "morning",
                "duration_or_quantity": "25 min / 7,000 steps",
                "coins_reward": 0
            })

    # ── SUGAR-BASED TASKS ─────────────────────────────────────
    sg_avg   = features.get("fasting_sugar_avg", 0)
    sg_above = features.get("sugar_readings_above_100", 0)

    if sg_avg > 0:
        tasks.append({
            "task_type": "LOG_SUGAR",
            "task_name": "Log your fasting sugar",
            "description": "Measure and record before breakfast",
            "why_this_task": (
                "Weekly tracking shows us your sugar trend "
                "and powers the preventive care engine"
            ),
            "category": "vitals",
            "time_of_day": "morning",
            "duration_or_quantity": "Before breakfast",
            "coins_reward": 15
        })

        if sg_avg >= 100 or sg_above >= 2:
            tasks.append({
                "task_type": "POST_MEAL_WALK",
                "task_name": "Walk 10 min after lunch",
                "description": "Short walk immediately after eating",
                "why_this_task": (
                    "Post-meal walking reduces blood sugar spike "
                    "by 22% compared to resting after meals"
                ),
                "category": "exercise",
                "time_of_day": "afternoon",
                "duration_or_quantity": "10 minutes",
                "coins_reward": 0
            })

            tasks.append({
                "task_type": "NO_SUGAR_DAY",
                "task_name": "No added sugar today",
                "description": "Skip sugar in tea, coffee, and snacks",
                "why_this_task": (
                    "Reducing daily sugar intake by 25g "
                    "can lower fasting glucose by 8–12 mg/dL "
                    "within 3 weeks"
                ),
                "category": "diet",
                "time_of_day": "all_day",
                "duration_or_quantity": "All day",
                "coins_reward": 0
            })

    # ── PLATELET-BASED TASKS ──────────────────────────────────
    platelets = features.get("platelet_count", 0)
    if 0 < platelets < 150000:
        tasks.append({
            "task_type": "HYDRATION_PLUS",
            "task_name": "Drink 10 glasses of water",
            "description": "Extra hydration target for today",
            "why_this_task": (
                "Good hydration supports healthy platelet "
                "function and circulation"
            ),
            "category": "wellness",
            "time_of_day": "all_day",
            "duration_or_quantity": "10 glasses minimum",
            "coins_reward": 10
        })

        tasks.append({
            "task_type": "EAT_PAPAYA",
            "task_name": "Eat papaya today",
            "description": "Include fresh papaya in your diet",
            "why_this_task": (
                "Papaya and its leaf extract are traditionally "
                "associated with supporting platelet levels"
            ),
            "category": "diet",
            "time_of_day": "afternoon",
            "duration_or_quantity": "1 bowl fresh papaya",
            "coins_reward": 0
        })

    # ── HEMOGLOBIN-BASED TASKS ────────────────────────────────
    hb = features.get("hemoglobin", 0)
    gender_enc = features.get("gender_enc", 1)
    hb_lo = 13.5 if gender_enc == 1 else 12.0

    if 0 < hb < hb_lo:
        tasks.append({
            "task_type": "IRON_RICH_MEAL",
            "task_name": "Eat an iron-rich meal today",
            "description": "Spinach dal, chicken curry, or egg bhurji",
            "why_this_task": (
                "Your hemoglobin is below normal. "
                "Daily iron-rich foods are the first step "
                "to improving it naturally"
            ),
            "category": "diet",
            "time_of_day": "lunch",
            "duration_or_quantity": "At least 1 iron-rich meal",
            "coins_reward": 0
        })

        tasks.append({
            "task_type": "VITAMIN_C_BOOST",
            "task_name": "Eat citrus fruit today",
            "description": "Orange, amla, lemon, or guava",
            "why_this_task": (
                "Vitamin C increases iron absorption "
                "by up to 3x when eaten alongside iron-rich foods"
            ),
            "category": "diet",
            "time_of_day": "morning",
            "duration_or_quantity": "1 serving",
            "coins_reward": 0
        })

    # ── BMI-BASED TASKS ───────────────────────────────────────
    bmi = features.get("bmi", 0)
    if bmi > 27:
        tasks.append({
            "task_type": "LIGHT_EXERCISE",
            "task_name": "30-min light exercise",
            "description": "Walk, yoga, or stretching",
            "why_this_task": (
                "Reducing BMI by even 1 point improves BP, "
                "sugar, and cholesterol simultaneously"
            ),
            "category": "exercise",
            "time_of_day": "morning",
            "duration_or_quantity": "30 minutes",
            "coins_reward": 0
        })

    # ── STRESS-BASED TASKS ────────────────────────────────────
    stress = features.get("stress_level", 5)
    if stress >= 7:
        tasks.append({
            "task_type": "SLEEP_EARLY",
            "task_name": "Sleep by 10:30 PM tonight",
            "description": "No screens after 10 PM",
            "why_this_task": (
                "Poor sleep raises cortisol which directly "
                "increases BP and blood sugar. 7+ hours is "
                "non-negotiable for metabolic health"
            ),
            "category": "wellness",
            "time_of_day": "evening",
            "duration_or_quantity": "7–8 hours",
            "coins_reward": 0
        })

    # ── MEDICATION TASKS (from user profile) ──────────────────
    if hasattr(user, 'medications') and user.medications:
        # If user.medications is stored as a JSON list in text column
        import json
        try:
            meds = json.loads(user.medications) if isinstance(user.medications, str) else user.medications
            for med in meds:
                tasks.append({
                    "task_type": "MEDICATION",
                    "task_name": f"Take {med}",
                    "description": "As prescribed by your doctor",
                    "why_this_task": (
                        "Consistent medication timing ensures "
                        "maximum effectiveness"
                    ),
                    "category": "medication",
                    "time_of_day": "morning",
                    "duration_or_quantity": "As prescribed",
                    "coins_reward": 10
                })
        except:
            pass

    return tasks
