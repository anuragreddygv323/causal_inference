# Uplift Modeling

## What It Is and When to Use It

Uplift modeling predicts the **incremental impact** of treatment on each individual. It answers: *"What is the right offer for the right person?"* It operationalizes heterogeneous treatment effects for targeting.

**Use when:**
- You have experimental data with multiple treatment variants
- You want to optimize targeting/allocation
- You need to maximize ROI of interventions

**Do NOT use when:**
- You just need an average effect (use standard A/B analysis)
- You don't have experimental data (get causal estimates first)

### Four User Types

| Type | Description | Action |
|------|-------------|--------|
| **Persuadables** | Treatment causes positive outcome change | **Target these** |
| **Sure Things** | Positive outcome regardless of treatment | Don't waste resources |
| **Lost Causes** | Negative outcome regardless of treatment | Don't waste resources |
| **Sleeping Dogs** | Treatment actually *hurts* — causes negative outcome change | **Avoid treating** |

---

## Industry Use Cases

### Use Case 1: Uber — Promotional Ride Credit Targeting

- **Business question:** Which riders should receive $5 / $10 / free ride credits to maximize reactivation?
- **Treatment:** Multiple promo levels. **Outcome:** 30-day reactivation.
- **Why Uplift:** A standard churn model predicts *who will churn*, not *who is persuadable*. Need to identify persuadables — riders whose behavior changes because of the promo, not riders who would return anyway.
- **Alternatives considered:**
  - Standard churn model → ruled out: predicts P(outcome), not treatment lift
  - Blanket discounts → ruled out: wasteful, many "sure things" get unnecessary discounts

### Use Case 2: Netflix — Personalized Retention Offers

- **Treatment:** Email reminder, discounted month, free premium upgrade. **Outcome:** Renewal.
- **Why Uplift:** Identify which offer works for which user. Some users renew anyway (sure things). Some are persuadable with just an email. Others need a discount.

### Use Case 3: Xbox — Game Pass Upsell Targeting

- **Treatment:** Upgrade offer (Game Pass Core → Ultimate). **Outcome:** Upgrade conversion.
- **Why Uplift:** Many Core users would upgrade anyway at renewal. Target the persuadable marginal users who wouldn't convert without the nudge.

### Use Case 4: Airbnb — Host Activation Campaign

- **Treatment:** Onboarding assistance (photography, listing optimization). **Outcome:** First booking within 30 days.
- **Why Uplift:** Not all new hosts need help. Target those where assistance makes the difference between an active listing and an abandoned one.

---

## Methods

- **T-learner:** Train separate outcome models per treatment arm, compute uplift as difference in predicted outcomes
- **Two-Model approach:** One model for treated, one for control; uplift = P(Y|T=1) - P(Y|T=0)
- **Direct uplift trees:** Split on the feature that maximizes uplift difference, not prediction accuracy
- **Qini curves:** Evaluation metric — area under the uplift curve, analogous to AUC for uplift models

## Connection to HTE

Uplift modeling is the **operationalization of heterogeneous treatment effects**. HTE estimates how effects vary across subgroups; uplift modeling takes those estimates and builds a targeting policy — deciding who gets treated and with what.

---

## Real-World Challenges and Practical Realities

### Challenge 1: You Need Experimental Data (And Lots of It)
Uplift modeling requires randomized treatment/control data to estimate individual-level treatment effects. Many companies don't have this, or their experiments are too small. At Uber, the promo experiment might have 50K users but split across 4 treatment arms (12.5K each), which is often insufficient for reliable uplift estimates across dozens of user features.

**What actually happens**: The uplift model is trained on limited experimental data and produces noisy uplift predictions. When deployed, the targeting barely outperforms random assignment. The team then argues about whether the model is bad or the data is insufficient.

### Challenge 2: "Sleeping Dogs" Are Real and Dangerous
Some users are genuinely harmed by treatment. At Netflix, sending a "we miss you" email to lapsed users can remind them to cancel their forgotten subscription. At Uber, sending promo codes to a user who just had a bad experience can feel tone-deaf and accelerate churn. These sleeping dogs can cost more than the persuadables gain.

**What actually happens**: The marketing team runs a campaign targeting all at-risk users. Post-campaign analysis shows that 5% of contacted users churned FASTER than the control group. The uplift model would have flagged these, but the team didn't build one and used a churn prediction model instead.

### Challenge 3: The Churn Model Trap
Most companies have a churn prediction model and use it for targeting: "send discounts to users most likely to churn." This is wrong. The most likely churners include both persuadables (who benefit from the discount) and lost causes (who will churn regardless). Worse, sure things (who will stay anyway) might get predicted as "at risk" and receive unnecessary discounts.

**What actually happens**: The marketing team targets the top-20% churn risk with 20% discounts. Post-analysis shows: 60% of recipients would have stayed anyway (wasted money), 25% were going to churn regardless (wasted money), only 15% were actually persuaded. The uplift model would have targeted very differently.

### Challenge 4: Model Evaluation Is Tricky
Standard ML metrics (AUC, precision, recall) don't apply to uplift. You can't directly observe the uplift for any individual. Evaluation requires Qini curves, uplift curves, or AUUC (Area Under the Uplift Curve), which most stakeholders have never seen and don't trust.

**What actually happens**: The team presents Qini curves and the PM says "what's the accuracy?" There is no simple accuracy number for uplift models. The conversation detours into a 20-minute explanation of why uplift evaluation is different from classification evaluation.

### Challenge 5: Treatment Costs and Budget Constraints
Real campaigns have constraints: limited budget, limited inventory of premium offers, channel capacity (can't email everyone on the same day). The uplift-optimal policy might say "give everyone the most expensive offer" -- which is budget-infeasible. Incorporating constraints turns the problem from ML into optimization, which requires different skills and tools.

**What actually happens**: The data scientist builds a beautiful uplift model, then the marketing team says "we can only send 10K emails and we have budget for 5K discounts." The deployment requires a constraint-optimization layer that wasn't planned for.

---

## FAANG Interview Follow-Up Questions

### Q1: "You have a churn prediction model with 0.85 AUC. Why can't you just use it for targeting?"
**What they're testing**: Do you understand the fundamental difference between prediction and uplift?
**Strong answer**: "Because churn PREDICTION and churn PREVENTION are different problems. The model predicts P(churn). But for targeting, we need P(churn | no treatment) - P(churn | treatment) -- the INCREMENTAL effect of treatment. A user with P(churn) = 0.90 might churn regardless of our intervention (lost cause, uplift ≈ 0) or might be saved with a discount (persuadable, uplift = 0.30). The churn model can't distinguish them. Worse, it might rank 'sure things' as moderate risk and waste resources on users who'd stay anyway. The uplift model directly estimates the lift, not the level."

### Q2: "How would you explain 'sleeping dogs' to a non-technical VP who wants to contact all at-risk users?"
**What they're testing**: Can you communicate unintuitive concepts to stakeholders?
**Strong answer**: "I'd say: 'Imagine you have a streaming subscription you forgot about. You're happily paying $15/month without watching. Then we send you a "we miss you" email. Now you remember you have this subscription, log in, realize you haven't watched anything in months, and cancel. Our email CAUSED you to churn. These are sleeping dogs -- users who are technically at risk but better left alone. Our data shows about 5% of at-risk users fall into this category. An uplift model identifies them and keeps us from poking the bear.' I'd show the historical evidence: control vs treated outcomes for the bottom decile of predicted uplift."

### Q3: "You built a multi-treatment uplift model. The model says to give User A a $10 credit and User B a free ride. But the $10 credit costs us $10 and the free ride costs us $25. How do you incorporate costs?"
**What they're testing**: Can you combine causal inference with economics/optimization?
**Strong answer**: "For each user-treatment pair, I compute: net_value = uplift(user, treatment) × LTV(user) - cost(treatment). User A: if uplift = 0.15 and LTV = $200, net_value = 0.15 × $200 - $10 = $20. User B: if uplift = 0.08 and LTV = $300, net_value = 0.08 × $300 - $25 = -$1. So User B should NOT get the free ride despite the model suggesting it -- the cost exceeds the expected benefit. I'd rank all user-treatment pairs by net_value and allocate top-down until the budget is exhausted. This is a constrained optimization problem (potentially a linear program if budget is the only constraint)."

### Q4: "Your Qini curve shows the uplift model outperforms random targeting. But the improvement is only 3%. Is it worth the complexity?"
**What they're testing**: Practical judgment about when ML adds value.
**Strong answer**: "It depends on scale. If the campaign reaches 1M users and each percentage point of targeting efficiency saves $50K, then 3% = $150K annual savings. Compare that to the cost of building and maintaining the uplift model (data scientist time, infrastructure, monitoring). At Uber's scale, even 1% improvement in targeting efficiency on promo spend could be worth millions. But at a smaller company, the complexity might not justify the gain. I'd also ask: can we get more than 3% by collecting more experimental data, adding features, or trying different model architectures?"

### Q5: "You trained the uplift model on last quarter's experiment. How do you know it's still valid this quarter?"
**What they're testing**: Do you understand model drift in causal settings?
**Strong answer**: "Treatment effect heterogeneity can change due to: (1) user base composition shift (more/fewer new users), (2) competitive environment changes, (3) product changes that alter the baseline, (4) seasonal effects. I'd: (1) continuously run a small random holdout (5-10% of budget on random assignment) to monitor real-time uplift calibration, (2) compare the predicted uplift distribution to the holdout-estimated uplift by decile -- if they diverge, retrain, (3) set up an automated retraining pipeline triggered by drift detection. The holdout is critical -- without it, you have no way to detect when the model becomes stale."

### Q6: "Design an end-to-end system for uplift-based targeting at a company like Uber with 100M users."
**What they're testing**: Can you think at system level, not just model level?
**Strong answer**: "Components: (1) Experimentation platform that runs ongoing randomized holdouts across all campaigns, (2) Feature store serving real-time user features, (3) Uplift model training pipeline (weekly retrain on rolling 90-day experimental data), (4) Scoring service that computes uplift × LTV - cost for each user × treatment combination in real-time, (5) Budget optimizer (LP solver) that allocates the treatment portfolio subject to constraints, (6) Campaign execution system that delivers the personalized treatment, (7) Monitoring dashboard tracking: actual vs predicted uplift by decile, holdout performance, sleeping dog detection, total ROI. Key design choice: the random holdout must be PERMANENT -- you never stop randomizing a small fraction, because that's your ground truth."
