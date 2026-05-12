# Instrumental Variables (IV)

## What It Is and When to Use It

Instrumental Variables uses a third variable (the **instrument**) that affects treatment but has no direct effect on the outcome except through treatment. It solves the fundamental problem of **unmeasured confounding** — when you know there are variables you can't observe that influence both treatment and outcome simultaneously.

**Use when:**
- Unmeasured confounders exist between treatment and outcome
- A valid instrument is available (relevant, excludable, independent)
- The instrument strongly predicts treatment (first-stage F > 10)

**Do NOT use when:**
- All confounders are measured → use Propensity Score Matching
- A sharp cutoff determines treatment → use Regression Discontinuity
- You have panel data with a clear intervention point → consider Difference-in-Differences first
- You need ATE rather than LATE (IV estimates a local effect on compliers)

---

## Industry Use Cases

### Use Case 1: Uber — Effect of Surge Pricing on Ride Completions

| Component | Detail |
|-----------|--------|
| **Instrument** | Rainfall intensity (affects surge pricing but doesn't directly affect ride demand except through price) |
| **Treatment** | Surge multiplier (1.0x to 3.0x) |
| **Outcome** | Ride completion rate (requested rides that result in completed trips) |
| **Unmeasured Confounders** | Events, driver supply shifts, urgency of trips — all affect both price and demand |

**Why IV over alternatives:**
- **PSM ruled out**: Can't observe "urgency of trip" or "nearby event demand" — key confounders are unmeasured
- **DiD ruled out**: Surge is continuous and happens constantly, not a single policy intervention
- **RDD ruled out**: No sharp threshold that determines surge (it's algorithmic and continuous)

---

### Use Case 2: Xbox — Effect of Game Pass on Hardware Sales

| Component | Detail |
|-----------|--------|
| **Instrument** | Regional Game Pass advertising intensity (quasi-random budget allocation across DMAs) |
| **Treatment** | Game Pass adoption rate in a region |
| **Outcome** | Console hardware sales |
| **Unmeasured Confounders** | "Gaming enthusiasm" — users who adopt Game Pass are self-selected enthusiasts who would buy hardware anyway |

**Why IV over alternatives:**
- **PSM ruled out**: Can't observe "gaming enthusiasm" or "intent to purchase hardware regardless"
- **RDD ruled out**: No threshold that determines Game Pass adoption
- **DiD ruled out**: No single intervention point; Game Pass adoption is ongoing

---

### Use Case 3: Netflix — Effect of Autoplay on Binge-Watching

| Component | Detail |
|-----------|--------|
| **Instrument** | Random A/B assignment to autoplay variants (3-second vs 10-second countdown) |
| **Treatment** | Actually watching the next episode (autoplay fires vs manual click-through) |
| **Outcome** | Total watch session length (minutes) |
| **Unmeasured Confounders** | Viewer intent, show engagement, time of day — affect both compliance with autoplay and session length |

**Why IV over alternatives:**
- This is the classic **encouragement design**: assignment is random, but compliance varies
- Users assigned to 3s countdown are "encouraged" to watch next episode, but some cancel; users in 10s group sometimes click manually
- IV estimates the LATE: effect of actually watching next episode *for compliers* (those whose behavior is changed by the countdown)
- Simple ITT (comparing groups) underestimates the effect on actual behavior change

---

### Use Case 4: Airbnb — Effect of Professional Photography on Bookings

| Component | Detail |
|-----------|--------|
| **Instrument** | Distance to nearest Airbnb photographer (affects likelihood of getting professional photos but not bookings directly) |
| **Treatment** | Having professional listing photos |
| **Outcome** | Monthly booking count |
| **Unmeasured Confounders** | Host motivation, property quality, listing effort — hosts who get professional photos are already more professional |

**Why IV over alternatives:**
- **PSM ruled out**: Can't fully observe "host professionalism" or "property appeal in person"
- **RDD ruled out**: No sharp distance cutoff that determines photo adoption
- **DiD ruled out**: Photo adoption is staggered and individual, not a single policy change

---

## Key Assumptions

### 1. Relevance (Instrument → Treatment)
The instrument must actually predict treatment. Test with first-stage F-statistic > 10 (Staiger & Stock rule of thumb). A weak instrument biases IV toward OLS.

**How to check:** Run first-stage regression, report F-statistic. Use Stock-Yogo critical values for formal weak instrument tests.

### 2. Exclusion Restriction (Instrument → Outcome ONLY through Treatment)
The instrument affects the outcome *only* through its effect on treatment — no direct path or back-door paths.

**How to check:** Cannot be tested statistically — must be argued substantively. Ask: "Is there any way the instrument could affect the outcome other than through treatment?" If overidentified (multiple instruments), use Sargan/Hansen J-test.

### 3. Independence (Instrument ⊥ Unmeasured Confounders)
The instrument is "as-if random" — uncorrelated with the unmeasured confounders between treatment and outcome.

**How to check:** Cannot be tested directly. Check balance of observed covariates across instrument levels (like checking randomization). Argue that assignment mechanism is plausibly exogenous.

---

## Connection to Other Methods

| Connection | Explanation |
|-----------|-------------|
| **CACE/LATE** | IV estimates the Complier Average Causal Effect — the effect for units whose treatment is changed by the instrument. This is a *local* effect, not ATE. |
| **Fuzzy RDD** | Fuzzy RDD *is* IV: the running variable crossing the cutoff is the instrument for treatment uptake. 2SLS is the standard estimator. |
| **Panel IV** | Combine instruments with panel data for panel IV (e.g., fixed effects + IV). Addresses both time-invariant confounders and time-varying ones. |
| **Encouragement Designs** | Randomized encouragement (like Netflix autoplay) creates a perfect instrument. ITT / IV decomposition separates assignment effect from treatment effect. |
| **Control Function** | Alternative to 2SLS that uses first-stage residuals as a control for endogeneity. More efficient under heteroskedasticity. |

---

## Real-World Challenges and Practical Realities

### Challenge 1: Finding Valid Instruments Is Extremely Hard
The exclusion restriction (instrument affects outcome ONLY through treatment) is untestable and almost always debatable. At Uber, "rain" as an instrument for surge pricing sounds clever, but does rain affect ride completions only through price? Rain also affects traffic (longer rides), demand patterns (more short trips), and driver supply (some drivers avoid bad weather). Each of these violates exclusion.

**What actually happens**: Every IV paper/analysis generates heated debate about whether the instrument is truly valid. At FAANG companies, IV proposals are frequently shot down in peer review because the exclusion restriction can't be defended convincingly. The method is theoretically powerful but practically hard to use credibly.

### Challenge 2: Weak Instruments
If the first-stage F-statistic is below 10, the IV estimate is biased toward OLS and has massive variance. In practice, many proposed instruments are weak. At Netflix, using "random variation in autoplay countdown timer" as an instrument for binge-watching might have a first-stage F of 3 -- the timer slightly affects behavior, but not enough to serve as a strong instrument.

**What actually happens**: The team finds an instrument, runs the first stage, sees F = 7, and is in the "gray zone." They proceed anyway because they don't have a better instrument, but the resulting IV estimate has such wide confidence intervals that it's uninformative. Sometimes the CI includes both "treatment helps" and "treatment hurts."

### Challenge 3: LATE vs. ATE Interpretation
IV estimates the Local Average Treatment Effect -- the effect for COMPLIERS only. But who are the compliers? They're a latent (unobserved) subpopulation. At Uber, the LATE of surge pricing via the rain instrument applies to "rides that happen because of rain-induced surge changes" -- a weird subpopulation that may not represent typical rides.

**What actually happens**: The team reports "surge pricing reduces completion rates by 15%" but this is the LATE, not the ATE. The PM asks "does this apply to all surge situations?" and the honest answer is "only to rain-induced surge." This limits the policy relevance.

### Challenge 4: Multiple Instruments and Overidentification
When multiple instruments are available, overidentification tests (Hansen J) can partly test instrument validity. But in practice, having even ONE good instrument is rare. Having multiple is a luxury.

**What actually happens**: The team has one borderline instrument and spends more time defending it than actually doing the analysis.

### Challenge 5: Sample Size Requirements
IV is notoriously data-hungry. The variance of the IV estimator scales inversely with the compliance rate squared. With 20% compliance, you need 25x the sample size of a standard experiment to achieve the same precision.

**What actually happens**: The team runs 2SLS and gets a point estimate of $18.50 with a 95% CI of [-$5, $42]. The CI is so wide that the PM says "so we don't actually know anything?" and the team has to agree.

---

## FAANG Interview Follow-Up Questions

### Q1: "You're using rain as an instrument for surge pricing. How do you defend the exclusion restriction?"
**What they're testing**: Can you think critically about instrument validity?
**Strong answer**: "The exclusion restriction requires that rain affects ride completions only through surge pricing. Threats: (1) rain affects traffic speeds (longer rides), but I can control for ride duration, (2) rain changes demand composition (more short trips), but I can control for trip distance, (3) rain affects driver supply, which affects wait times independently of price -- this is the hardest to defend. I'd argue that in a well-supplied market, rain's primary effect on ride AVAILABILITY is through the price mechanism (surge incentivizes drivers to come online), not through some other channel. I'd also test overidentification: if I have a second instrument (e.g., temperature), the Hansen J test can flag whether both instruments give the same answer."

### Q2: "Your first-stage F-statistic is 8. Is this a problem?"
**What they're testing**: Do you understand weak instruments?
**Strong answer**: "Yes, F < 10 is the Stock-Yogo threshold for weak instruments. With F = 8: (1) the IV estimate is biased toward OLS (the bias doesn't vanish asymptotically unless F grows with sample size), (2) confidence intervals have poor coverage, (3) the Wald test over-rejects. I'd use weak-instrument-robust inference: the Anderson-Rubin confidence set, which has correct coverage regardless of instrument strength. If the AR confidence set is very wide or includes zero, I'd be transparent that the instrument is too weak for reliable inference and look for a stronger instrument."

### Q3: "Your IV estimate is 3x larger than your OLS estimate. Is this suspicious?"
**What they're testing**: Do you understand why IV and OLS diverge?
**Strong answer**: "Not necessarily suspicious -- there are three legitimate reasons: (1) LATE vs. ATE: IV estimates the effect for compliers, who might be a selected subgroup with larger effects, (2) OLS is biased toward zero if the endogenous variable has measurement error (attenuation bias) -- IV corrects this, (3) OLS is biased in a specific direction depending on the confounder. However, if the IV estimate is implausibly large (e.g., surge pricing eliminates ALL rides), I'd suspect either a weak instrument (inflates estimates) or a violation of the exclusion restriction (rain directly affects the outcome, biasing IV upward). I'd run the weak instrument diagnostics and think harder about exclusion."

### Q4: "Can you explain what a 'complier' is in the context of your surge pricing analysis? Who are they?"
**What they're testing**: Do you understand the LATE interpretation?
**Strong answer**: "In this context, compliers are rides whose surge pricing level CHANGED because of rain. Specifically: on rainy days, surge goes up, and some rides face higher prices than they would have on dry days -- these are the compliers. Always-takers are rides that would complete regardless of surge level. Never-takers are rides that wouldn't happen regardless. The IV estimate of -0.15 applies to the complier group: 'among rides where rain-induced surge made the price higher, a 1x increase in surge multiplier reduces completion probability by 15%.' This may differ from the effect of non-rain-related surge."

### Q5: "If you had unlimited resources, how would you estimate the surge pricing effect without IV?"
**What they're testing**: Do you understand IV's role as a second-best approach?
**Strong answer**: "I'd run a randomized experiment: randomly assign surge multipliers across similar ride requests. Some riders see 1.5x, others see 2.0x, for equivalent trip characteristics. This directly estimates the ATE (not just LATE), eliminates confounders, and is the gold standard. At Uber, this was actually done -- they ran controlled pricing experiments in specific markets. The challenge is ethical (charging different prices for the same ride) and legal (price discrimination concerns). IV is what we use when experimentation is infeasible or hasn't been done."

### Q6: "Walk me through the difference between IV, control function, and Heckman correction. When would you use each?"
**What they're testing**: Breadth of knowledge in endogeneity-correction methods.
**Strong answer**: "All three address endogeneity but differ in approach: (1) IV/2SLS is the most general -- it uses an external instrument and doesn't require distributional assumptions. Best when you have a strong, valid instrument. (2) The control function approach includes the first-stage residual as a control variable in the second-stage regression. It's equivalent to 2SLS in linear models but extends more naturally to nonlinear models (probit, logit). Best for nonlinear outcomes. (3) Heckman correction is specifically for sample selection bias -- when the outcome is observed only for a non-random subset (e.g., wages observed only for employed people). It models the selection process and corrects for it. Best for missing-data-due-to-selection problems. For surge pricing (continuous endogenous variable, linear outcome), IV/2SLS is the standard choice."
