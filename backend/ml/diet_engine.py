DIET_PLANS = {
    "low_sodium": {
        "reason": "Your BP trend needs sodium reduction",
        "eat_more": [
            "Banana (natural potassium — counters sodium)",
            "Sweet potato (potassium + fibre)",
            "Spinach and leafy greens",
            "Garlic (natural BP lowering effect)",
            "Oats (reduces BP over time)",
            "Coconut water (electrolyte balance)"
        ],
        "reduce": [
            "Salt in cooking — use lemon instead",
            "Chai and coffee to 1 cup daily",
            "Heavy oily meals"
        ],
        "avoid": [
            "Pickles, papad, chutneys",
            "Packaged chips, namkeen, biscuits",
            "Instant noodles and packaged food",
            "Extra salt added at table"
        ],
        "hydration_goal": 10
    },
    "diabetic_friendly": {
        "reason": "Your sugar trend needs dietary support",
        "eat_more": [
            "Brown rice or millet (ragi, jowar, bajra)",
            "Bitter gourd (karela) — natural sugar reducer",
            "Methi seeds — soak overnight, eat morning",
            "Whole dals and legumes",
            "Green vegetables with every meal",
            "Nuts as snacks (almonds, walnuts)"
        ],
        "reduce": [
            "White rice portion to half a cup",
            "Chapati to 2 per meal",
            "Fruit intake to low-GI fruits only"
        ],
        "avoid": [
            "Sugar in tea, coffee, milk",
            "Fruit juices (even fresh)",
            "Maida products: bread, biscuits, cake",
            "Fried snacks and sweets",
            "Sweetened yogurt or flavoured drinks"
        ],
        "hydration_goal": 8
    },
    "iron_rich": {
        "reason": "Your hemoglobin needs dietary iron support",
        "eat_more": [
            "Spinach, palak, methi daily",
            "Rajma, chana, masoor dal",
            "Chicken, eggs (especially yolk)",
            "Jaggery (gud) instead of sugar",
            "Dates and raisins as snacks",
            "Pomegranate and beetroot"
        ],
        "reduce": [
            "Tea and coffee — blocks iron absorption",
            "Calcium-rich foods right after iron foods"
        ],
        "avoid": [
            "Tea within 1 hour of iron-rich meals",
            "Excessive dairy with iron meals",
            "Highly processed food"
        ],
        "hydration_goal": 9
    },
    "platelet_support": {
        "reason": "Your platelet count needs nutritional support",
        "eat_more": [
            "Fresh papaya (whole fruit)",
            "Pomegranate seeds and juice",
            "Pumpkin and pumpkin seeds",
            "Lean protein: eggs, chicken, fish",
            "Vitamin K foods: spinach, broccoli",
            "Folate foods: lentils, chickpeas"
        ],
        "reduce": [
            "Alcohol completely — damages platelets",
            "Tonic water (contains quinine)"
        ],
        "avoid": [
            "Alcohol",
            "Aspirin and ibuprofen without doctor advice",
            "Excessive garlic supplements"
        ],
        "hydration_goal": 10
    },
    "balanced": {
        "reason": "Your vitals are healthy — maintain this",
        "eat_more": [
            "Seasonal vegetables with every meal",
            "2–3 fruits daily",
            "Whole grains instead of refined",
            "Lean protein with every meal",
            "Nuts and seeds as snacks"
        ],
        "reduce": [
            "Fried foods to twice a week",
            "Packaged and processed food"
        ],
        "avoid": [
            "Sugary drinks",
            "Trans fats in fried foods"
        ],
        "hydration_goal": 8
    }
}

def generate_diet_plan(features: dict, signals: dict) -> dict:
    hb       = features.get("hemoglobin", 0)
    platelets= features.get("platelet_count", 0)
    sg_avg   = features.get("fasting_sugar_avg", 0)
    sys_avg  = features.get("systolic_avg_7d", 0)
    gender_enc= features.get("gender_enc", 1)
    hb_lo    = 13.5 if gender_enc == 1 else 12.0

    # Priority order: platelets > hb > sugar > bp > balanced
    if 0 < platelets < 150000:
        focus = "platelet_support"
    elif hb > 0 and hb < hb_lo:
        focus = "iron_rich"
    elif sg_avg > 0 and sg_avg >= 100:
        focus = "diabetic_friendly"
    elif sys_avg > 0 and sys_avg >= 120:
        focus = "low_sodium"
    else:
        focus = "balanced"

    plan = DIET_PLANS[focus].copy()
    plan["focus_type"] = focus
    return plan
