# Quick Reference: Expected Output Checklist

## When Yash M. Patel's Blood Report is Uploaded

### 📊 RISK ASSESSMENT
```
Expected Risk Level: MODERATE (not low, not high)
Expected Confidence: 0.70 (70%)
Expected Summary: "Some findings indicate health risks that should be monitored. 
                   Consider scheduling a follow-up with your physician."
```

### ✅ Checkboxes to Verify

#### Risk Detection
- [ ] Dashboard shows risk badge as "MODERATE" (orange/yellow indicator)
- [ ] Report linked to patient's health profile
- [ ] Risk history updated

#### Daily Tasks Generated (Should appear in Missions/Tasks section)
- [ ] Task 1: "Eat Iron-Rich Meal (Spinach/Lentils)"
  - [ ] Shows in afternoon time slot
  - [ ] Coin reward showing as 25
  - [ ] Status: Incomplete (not yet marked done)
  
- [ ] Task 2: "Take Vitamin C (Lemon/Orange)"
  - [ ] Shows in morning time slot
  - [ ] Coin reward showing as 15
  - [ ] Status: Incomplete

#### Precautions/Recommendations Section
The system should display a section with these 6 recommendations:

- [ ] "Plan a follow-up check in the next 2-4 weeks to monitor progress."
- [ ] "Increase dietary iron: focus on spinach, nuts, lentils, and jaggery."
- [ ] "Pair iron-rich foods with Vitamin C (like lemon/orange) for better absorption."
- [ ] "Avoid tea or coffee immediately after meals as they block iron absorption."
- [ ] "Drink enough water through the day and keep sleep consistent."
- [ ] "Track one small habit daily instead of changing everything at once."

#### Report Details Section
- [ ] Patient name: "Yash M. Patel"
- [ ] Test date: "02 Dec 2X"
- [ ] Doctor: "Dr. Hiren Shah"
- [ ] Lab: "DRLOGY PATHOLOGY LAB"
- [ ] Key finding: "Hemoglobin 12.5 g/dL (LOW)"

### 🎯 Interactive Tests

**Test 1: Complete Iron-Rich Meal Task**
```
1. Click on "Eat Iron-Rich Meal (Spinach/Lentils)" task
2. Expected: Pop-up or modal for task details
3. Should show examples: spinach, lentils, beans, nuts, jaggery
4. Click "Complete Task"
5. Expected: +25 coins awarded
6. Check coin balance increased by 25
```

**Test 2: Complete Vitamin C Task**
```
1. Click on "Take Vitamin C (Lemon/Orange)" task
2. Expected: Task details modal appears
3. Should show examples: lemon, orange, mosambi, tomato
4. Click "Complete Task"
5. Expected: +15 coins awarded (total 40 for both tasks)
6. Check streak counter updated
```

**Test 3: Check Task Dashboard**
```
1. Go to Missions/Tasks section
2. Expected: 7 total tasks visible (iron + vitamin C + 5 default)
3. Daily progress > 28% (2/7 important tasks)
4. Button says "Complete Today's Missions"
5. Coin tracker shows potential earnings: +40
```

### 📱 Mobile Responsive Checks

- [ ] Tasks display properly on 375px width (iPhone SE)
- [ ] Precautions text readable without horizontal scroll
- [ ] Coin icons visible on mobile
- [ ] Tap area for task completion is min 44px × 44px
- [ ] Risk level badge is color-coded (orange for MODERATE)

### 🗄️ Database Verification (Advanced)

If you have database access:

```sql
-- Should find 2 new tasks
SELECT task_type, task_name, coins_reward, task_date 
FROM daily_tasks 
WHERE user_id='<patient_id>' AND task_date=TODAY()
ORDER BY time_slot;

-- Expected Output:
-- IRON_DIET | Eat Iron-Rich Meal (Spinach/Lentils) | 25 | 2026-03-23
-- VITAMIN_C | Take Vitamin C (Lemon/Orange) | 15 | 2026-03-23
```

### 🔧 Troubleshooting If Tests Fail

| Issue | Cause | Solution |
|---|---|---|
| Tasks don't appear | OCR failed to extract hemoglobin value | Upload image again, ensure it's clear |
| Risk level shows as LOW instead of MODERATE | Keyword matching failed | Check if "anemia" or "hemoglobin" appears in OCR output |
| No precautions showing | Report not saved to database | Refresh dashboard, check backend logs |
| Wrong coins showing | Task configuration issue | Verify iron_diet=25 coins in ml.py line 298 |
| Tasks appear but completed immediately | Database state issue | Check daily_tasks.completed column in DB |

### 📈 Success Metrics

✅ **Test is SUCCESSFUL if**:
- [x] Risk level: MODERATE
- [x] 2 anemia-specific tasks generated
- [x] 6 precautions displayed
- [x] Total coins rewarded: 40 (25+15)
- [x] All recommendations are readable and actionable

### ⏱️ Timeline for This Patient's Recovery

```
Day 1:     Patient uploads report
           System shows MODERATE risk
           Tasks generated
           
Days 2-14: Patient completes iron + vitamin C tasks daily
           Earns 40 coins per day
           Potential total: 280 coins
           
Week 2:    Schedule doctor follow-up
           Blood test appointment booked
           
Week 3:    Follow-up doctor visit
           New blood work: Recheck hemoglobin
           
Week 4:    Results reviewed
           Expected improvement: Hb +0.5-1.0 g/dL
           System adjusts recommendations if needed
```

### 🚨 Critical Failure Points to Watch For

1. **OCR Extraction Fails**
   - Symbol: Report shows confidence < 0.50
   - Action: Retake photo, ensure all text visible
   - Fallback: System uses demo data (not ideal)

2. **Anemia Not Detected**
   - Symbol: Risk shows as LOW instead of MODERATE
   - Action: Check OCR output for "hemoglobin" or "anemia" keywords
   - Cause: Image quality or lab report format incompatibility

3. **Tasks Don't Save**
   - Symbol: Tasks generate but disappear on refresh
   - Action: Check database connection and Flush
   - Cause: Likely database transaction issue

4. **Recommendations Not Displaying**
   - Symbol: Precautions section empty
   - Action: Check if positive_precautions field populated in response
   - Cause: _build_positive_precautions() function may need debugging

### 📸 Screen Capture Checklist

Capture these screens for documentation:

- [ ] Dashboard after report upload (shows risk badge)
- [ ] Missions/Tasks screen (shows 2 new tasks)
- [ ] Task detail view (shows iron-rich meal examples)
- [ ] Precautions section (all 6 recommendations visible)
- [ ] Coins awarded notification (shows +25 after task)
- [ ] Task completed state (checkmark visible)
- [ ] Daily streak counter (updated)
- [ ] Report history (shows Yash M. Patel's report)

### 📝 Report for Stakeholders

Use this template when presenting test results:

```
TEST REPORT: Anemia Case (Yash M. Patel)

Patient Profile:
- 21-year-old male, low hemoglobin (12.5 g/dL vs normal 13-17)
- Suspected Anemia

System Analysis:
✓ Risk Level Correctly Identified: MODERATE
✓ Tasks Generated: Iron Diet + Vitamin C
✓ Recommendations Accuracy: 6/6 best practices included
✓ Coin Incentives: Properly configured (40 coins/day)

Patient Experience:
- Clear actionable tasks
- Personalized recommendations
- Gamified adherence through coins
- Appropriate follow-up timeline (2-4 weeks)

Recommendations:
✓ Application READY for anemia cases
✓ Good for other nutritional deficiency cases
⚠️ Needs enhancement: Medication tracking
⚠️ Needs enhancement: Lab booking integration
```

---

**Status**: Ready to Test  
**Expected Duration**: 2-3 minutes for manual test  
**Required**: Test user account + Active database connection
