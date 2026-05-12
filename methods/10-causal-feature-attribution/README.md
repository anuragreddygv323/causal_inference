# Causal Feature Attribution / Drivers Analysis

## What It Is and When to Use It

Identifies which features or behaviors *causally drive* an outcome (churn, revenue, engagement), as opposed to merely predicting it. Uses causal graphs + debiased ML to separate correlation from causation.

**Use when**: Product teams ask "what is driving churn/revenue?", you need actionable drivers (not just predictions), you want to prioritize interventions.

**Do NOT use when**: You just need prediction (use standard ML), you don't have domain knowledge for DAG construction.

> **Key distinction**: Prediction tells you WHAT will happen. Causal attribution tells you WHY it happens and WHAT TO DO about it.

---

## Industry Use Cases

### Use Case 1: Netflix — What Drives Subscriber Churn?

| Aspect | Detail |
|--------|--------|
| **Candidate drivers** | Watch hours, genre diversity, social features, account sharing, content freshness |
| **Why causal attribution** | "Days since last login" is the #1 predictor but is tautological. Need to find upstream actionable behaviors. |
| **Key insight** | ML importance says "support tickets predict churn" but causal analysis shows tickets are a *symptom*, not a cause. |

### Use Case 2: Xbox — What Drives Game Pass Engagement?

| Aspect | Detail |
|--------|--------|
| **Candidate drivers** | Multiplayer sessions, titles tried, achievements, social connections, store purchases |
| **Why causal attribution** | Need to know which behaviors to promote via product features. |
| **Alternatives considered** | SHAP (ruled out — measures predictive importance, not causal). Correlation (ruled out — confounded). |

### Use Case 3: Uber — What Drives Driver Churn?

| Aspect | Detail |
|--------|--------|
| **Candidate drivers** | Earnings per hour, surge participation, acceptance rate, cancellation rate, hours online |
| **Why causal attribution** | Need to identify which working conditions to improve. Low earnings predict churn but may be caused by market saturation (the real driver). |

### Use Case 4: Airbnb — What Drives Booking Conversion?

| Aspect | Detail |
|--------|--------|
| **Candidate drivers** | Photo quality, response time, pricing, reviews, amenities listed |
| **Why causal attribution** | Need to advise hosts on what to improve. Reviews predict bookings but might be a proxy for host quality (confounder). |

---

## Methods

| Method | Role in Causal Feature Attribution |
|--------|------------------------------------|
| **DAGs (Directed Acyclic Graphs)** | Encode domain assumptions about causal structure. Identify confounders, colliders, and mediators. Required for valid identification. |
| **Double/Debiased ML (DML)** | Estimate causal effects while flexibly controlling for high-dimensional confounders. Residualize outcome and treatment on confounders, then regress residuals. |
| **Causal Forests** | Estimate heterogeneous causal effects — the driver importance may vary across user segments. |
| **DoWhy + EconML** | DoWhy formalizes the causal assumptions (DAG → identification). EconML provides the DML/causal-forest estimators. |

---

## Connection: Prediction vs. Causation

| Dimension | Predictive Model (SHAP) | Causal Attribution (DML) |
|-----------|------------------------|--------------------------|
| **Question answered** | "Which features help predict Y?" | "Which features causally change Y?" |
| **Confounders** | Ignored — all associations exploited | Controlled for — only causal paths remain |
| **Colliders** | Can inflate importance (collider bias) | Correctly excluded via DAG |
| **Actionability** | No guarantee — acting on a predictor may do nothing | Direct — effect estimates are interventional |
| **Example** | "Support tickets predict churn" → suppress tickets? | "Watch hours reduce churn" → increase engagement |

### SHAP vs. Causal Attribution

- **SHAP** decomposes a model's prediction into feature contributions. It faithfully explains *the model*, but the model may exploit spurious correlations.
- **Causal attribution** estimates *interventional effects* — what happens to the outcome if we change a feature, holding the causal structure fixed.
- They diverge most when colliders or strong confounders are present. In those cases, SHAP ranks can actively mislead product decisions.

---

## Real-World Challenges and Practical Realities

### Challenge 1: DAG Construction Is Subjective
Causal feature attribution requires a DAG, which encodes assumptions about which variables cause which. Different domain experts draw different DAGs. At Netflix, does "content freshness cause watch hours" or does "watch hours cause perceived freshness (because active users see new content first)"? The causal direction determines what you control for, and getting it wrong reverses your conclusions.

**What actually happens**: The data scientist convenes a meeting with PMs, engineers, and researchers to draw the DAG. They disagree on 4 of 12 edges. There's no data-driven way to resolve these disagreements for observational data. The team proceeds with the "consensus" DAG, but everyone knows it's a compromise, not ground truth.

### Challenge 2: Prediction vs. Causation Conflicts Confuse Stakeholders
SHAP and causal attribution can give opposite rankings. "Support tickets" might be the #1 SHAP predictor but have zero causal effect (because it's a symptom, not a cause). Explaining this to a VP who just saw the SHAP plot and wants to "fix the ticket problem" is politically difficult.

**What actually happens**: The data scientist presents the causal analysis. The VP says "but your ML model says support tickets are the #1 driver of churn." The data scientist explains collider bias and confounding. The VP's eyes glaze over. The team ends up working on both support tickets (because the VP insisted) and the actual causal drivers (because the data scientist knows they matter). Resources are split and impact is diluted.

### Challenge 3: Observational Data Can't Establish Causation Without Strong Assumptions
DML and causal forests handle measured confounders but not unmeasured ones. At Uber, "driver earnings per hour" might be causally associated with driver retention, but there could be an unmeasured variable (driver motivation, family situation) that causes both. The causal estimate might be off.

**What actually happens**: The team estimates that "increasing earnings per hour by $1 reduces driver churn by 3pp." Leadership uses this to justify a $1/hour pay increase for all drivers. Three months later, churn doesn't drop by 3pp because the estimate was partially confounded by motivation (high-motivation drivers earn more AND churn less).

### Challenge 4: Actionability vs. Measurability
Some causal drivers are real but unactionable. "User enthusiasm" might causally drive retention, but you can't directly increase enthusiasm. Actionable proxies (features, promotions) might not be the same as the true causal drivers. The gap between "what causes churn" and "what we can actually change" is often large.

**What actually happens**: The causal analysis identifies "having 3+ friends on the platform" as a strong causal driver of retention. The product team builds a friend-suggestion feature, but the users who gained friends through suggestions don't show the same retention benefit as users who found friends organically. The causal effect of "having friends" doesn't transfer to "being given friends" because the mechanism matters.

### Challenge 5: Temporal Ordering Ambiguity
Causal inference requires that causes precede effects. But with behavioral data measured at the same frequency (e.g., monthly), it's unclear whether "more multiplayer this month" causes "lower churn this month" or whether "being about to churn" causes "less multiplayer." Temporal ordering is essential but often ambiguous.

**What actually happens**: The team uses monthly behavioral features to predict monthly churn. A reviewer asks "isn't this just reverse causation? Users who are about to churn naturally play less multiplayer." The team switches to lagged features (last month's behavior predicting this month's churn), which reduces the concern but also reduces the signal.

---

## FAANG Interview Follow-Up Questions

### Q1: "You found that watch_hours causally reduces churn by 5pp per hour. How do you know this isn't just reverse causation -- users who are about to churn watch less?"
**What they're testing**: Do you understand the temporal ordering requirement?
**Strong answer**: "I addressed this by using LAGGED features: watch hours from months t-1 and t-2 predict churn at month t. This ensures the cause precedes the effect temporally. Additionally, I controlled for prior engagement trajectory (was the user already declining?). The DML approach residualizes both treatment and outcome on confounders INCLUDING lagged outcome, so the estimate captures the effect of watch_hours BEYOND what's explained by the existing trend. However, I'd caveat that even with lags, there could be a slow-moving unmeasured confounder. The strongest validation would be an experiment that randomly encourages more watching."

### Q2: "Your SHAP analysis and causal analysis disagree on the top driver. How do you explain this to stakeholders and which should guide decisions?"
**What they're testing**: Can you navigate the prediction vs. causation distinction in practice?
**Strong answer**: "I'd use an analogy: 'A fire truck is the #1 predictor of fire (whenever you see a fire truck, there's likely a fire). But sending fewer fire trucks doesn't reduce fires. Fire trucks are predictive but not causal.' Similarly, support tickets predict churn but don't cause it -- they're a response to the same underlying dissatisfaction. SHAP is the right tool for prediction (churn scoring). Causal attribution is the right tool for intervention (what to change). We need both: SHAP tells us WHO will churn (for proactive outreach), causal analysis tells us WHAT TO DO about it (which behaviors to promote)."

### Q3: "You're using DML (Double Machine Learning) for causal estimation. Walk me through the cross-fitting procedure and why it's necessary."
**What they're testing**: Technical depth on modern causal ML.
**Strong answer**: "DML has three steps: (1) Predict the outcome Y from confounders W using ML (flexible model), get residuals Y_resid. (2) Predict the treatment T from confounders W using ML, get residuals T_resid. (3) Regress Y_resid on T_resid -- the coefficient is the causal effect. Cross-fitting is necessary because if I use the same data to fit the ML models and compute residuals, the residuals are biased (they're fitted values on training data). Cross-fitting splits data into K folds: fit models on K-1 folds, predict on the held-out fold. This ensures residuals are computed on out-of-sample data, removing the bias from overfitting. Without cross-fitting, the causal estimate is inconsistent."

### Q4: "You identified 'multiplayer sessions' as the top causal driver. The product team builds a feature that pushes users into multiplayer. How do you verify the causal claim?"
**What they're testing**: Do you understand the validation loop?
**Strong answer**: "The causal estimate from observational data is a hypothesis. To verify: (1) Run a randomized experiment: randomly show multiplayer recommendations to some users and not others. Measure churn difference. This gives the causal effect of ENCOURAGING multiplayer (which differs from the observational effect of NATURALLY playing multiplayer). (2) If the experimental effect is positive but smaller than the observational estimate, the difference is likely due to: (a) confounding in the observational analysis, or (b) the mechanism matters -- users who CHOOSE multiplayer benefit more than users who are NUDGED into it. (3) Iterate: use the experimental data to refine the causal model and identify which types of users respond to nudges."

### Q5: "What's the difference between DoWhy, EconML, and CausalML? When would you use each?"
**What they're testing**: Familiarity with the causal inference ecosystem.
**Strong answer**: "They're complementary: (1) DoWhy (Microsoft) is for causal MODEL SPECIFICATION and REFUTATION -- it helps you define the DAG, identify the estimand (what do you need to estimate?), and run sensitivity/refutation tests. It's the 'thinking' tool. (2) EconML (Microsoft) is for ESTIMATION -- it implements DML, causal forests, CATE estimation, and orthogonal ML methods. It's the 'computation' tool for flexible treatment effect estimation. (3) CausalML (Uber) is focused on UPLIFT MODELING and A/B test analysis -- it implements meta-learners (T/S/X-learner), uplift trees, and evaluation metrics (Qini curves). It's the 'deployment' tool for targeting. I'd typically use DoWhy for specification, EconML for estimation, and CausalML when the goal is targeting/uplift. They can be combined in a single pipeline."

### Q6: "The VP says 'just run a regression of churn on all behavioral features with controls.' Why is DML better than OLS?"
**What they're testing**: Do you understand why modern methods improve on classical regression?
**Strong answer**: "Three reasons: (1) OLS assumes the confounders relate linearly to both treatment and outcome. If the true relationship is nonlinear (e.g., the effect of age on watch hours is U-shaped), OLS doesn't fully remove confounding. DML uses flexible ML (GBM, RF) for the confounding adjustment, handling nonlinearity automatically. (2) OLS with many controls risks overfitting and gives inconsistent standard errors. DML's cross-fitting avoids this. (3) OLS gives you the coefficient of one variable holding others constant -- but 'holding constant' means different things for confounders vs. mediators. DML, guided by the DAG, explicitly chooses what to condition on and what not to. That said, if relationships are truly linear and you've correctly specified confounders, OLS and DML give similar answers. DML is insurance against misspecification."
