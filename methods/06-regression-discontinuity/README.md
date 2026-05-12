# Regression Discontinuity Design (RDD)

## What It Is and When to Use It

RDD exploits a known cutoff in a continuous running variable. Units just above and just below the cutoff are essentially randomly assigned to treatment and control. Comparing their outcomes estimates the **local average treatment effect (LATE)** at the cutoff.

The core insight: if assignment to treatment is determined by whether a continuous score crosses a threshold, then units just on either side of that threshold are nearly identical in all respects — except for treatment status. This mimics a local randomized experiment.

**Use when:**
- Treatment is assigned by a sharp, known threshold on a continuous running variable
- You observe the running variable for all units
- Units cannot precisely manipulate the running variable to sort above/below the cutoff

**Do NOT use when:**
- No threshold exists → use PSM or DiD
- Treatment is voluntary and unrelated to a score → use PSM or IV
- The running variable is discrete with very few values (undermines the continuity assumption)
- Units can easily manipulate the running variable to land just above the cutoff

---

## Industry Use Cases

### Use Case 1: Airbnb — Superhost Status Threshold

| Component | Detail |
|---|---|
| **Running variable** | Overall review score (continuous, 1–5 stars) |
| **Cutoff** | 4.8 stars |
| **Treatment** | Superhost badge, priority search placement, and promotional benefits |
| **Outcome** | Monthly bookings |

**Why RDD:** The Superhost badge is deterministically assigned based on whether the host's average review score meets or exceeds 4.8. Hosts scoring 4.79 vs 4.81 are nearly identical in quality, experience, and listing characteristics — the only systematic difference is the badge. This makes the cutoff a source of quasi-random variation.

**Why not alternatives:**
- **PSM:** Can match on observables, but doesn't exploit the quasi-random assignment at the threshold. Superhosts differ from non-Superhosts on many unobservables.
- **DiD:** No clear before/after event for a cross-sectional analysis of threshold effects.
- **IV:** Could work if you had an instrument for Superhost status, but the threshold itself is more direct and transparent.

---

### Use Case 2: Xbox — Achievement Rewards Threshold

| Component | Detail |
|---|---|
| **Running variable** | Gamerscore points (cumulative) |
| **Cutoff** | 10,000 points |
| **Treatment** | Unlocking exclusive rewards tier (badges, discounts, early access) |
| **Outcome** | Next-month engagement (hours played, games purchased) |

**Why RDD:** The rewards tier is unlocked at exactly 10,000 Gamerscore points. Players at 9,950 vs 10,050 points have similar gaming histories and engagement patterns. The threshold creates a clean discontinuity in treatment assignment.

**Why not alternatives:**
- **PSM:** Doesn't leverage the quasi-experimental variation at the threshold — high-Gamerscore players are systematically different from low-Gamerscore players.
- **DiD:** Could complement RDD if the rewards tier was introduced at a specific time, but the primary identification comes from the score threshold.

---

### Use Case 3: Uber — Driver Rating Deactivation Threshold

| Component | Detail |
|---|---|
| **Running variable** | Driver average rating (continuous, 1–5 stars) |
| **Cutoff** | 4.6 stars |
| **Treatment** | Warning or deactivation notice |
| **Outcome** | Subsequent trip quality (ratings) and driver retention |

**Why RDD:** Uber sends deactivation warnings to drivers whose average rating falls below 4.6. Drivers at 4.58 vs 4.62 are comparable in driving quality and experience, but only those below the cutoff receive the warning. This allows estimation of how warnings affect driver behavior.

**Why not alternatives:**
- **PSM:** Cannot account for the unobserved motivation/quality differences that drive ratings.
- **DiD:** The warning is ongoing (not a single policy change), making a clean pre/post comparison difficult.

---

### Use Case 4: Netflix — "Top 10" List Threshold

| Component | Detail |
|---|---|
| **Running variable** | Viewership ranking (continuous underlying viewership metric) |
| **Cutoff** | 10th position |
| **Treatment** | Appearing in the "Top 10" list prominently displayed on the homepage |
| **Outcome** | Subsequent viewership (next-week streams) |

**Why RDD:** Only the top 10 titles are displayed in the prominent "Top 10" list. The title ranked 10th vs 11th have nearly identical underlying viewership, but rank 10 gets massive homepage visibility while rank 11 does not. This discontinuity in exposure enables causal estimation of the promotional effect.

**Why not alternatives:**
- **PSM:** Viewership is endogenous — titles in the Top 10 are popular for many unobservable reasons.
- **DiD:** The Top 10 list changes daily, so there's no clean policy shock to exploit.
- **IV:** Hard to find a valid instrument for Top 10 appearance that doesn't also affect viewership directly.

---

## Key Assumptions

1. **Continuity:** The potential outcomes (what would happen with and without treatment) are continuous functions of the running variable at the cutoff. There is no other discontinuity at the threshold.

2. **No manipulation:** Units cannot precisely manipulate the running variable to sort above or below the cutoff. Tested with the **McCrary density test** — if there's bunching at the cutoff, manipulation is likely.

3. **Local validity:** The causal effect is identified only at the cutoff. It may not generalize to units far from the threshold.

4. **SUTVA:** No interference between units — one unit's treatment doesn't affect another's outcome.

---

## Sharp vs Fuzzy RDD

| Feature | Sharp RDD | Fuzzy RDD |
|---|---|---|
| **Assignment** | Treatment is a deterministic function of the running variable | Probability of treatment jumps at the cutoff but isn't 0→1 |
| **Compliance** | Perfect: everyone above the cutoff is treated, everyone below is not | Imperfect: some above the cutoff don't take treatment, some below do |
| **Estimation** | Simple comparison of outcomes at the cutoff | Ratio of the jump in outcomes to the jump in treatment probability |
| **Connection to IV** | — | Fuzzy RDD is equivalent to IV where the instrument is "being above the cutoff" |

**Fuzzy RDD as IV:** In fuzzy designs, crossing the cutoff doesn't guarantee treatment but increases its probability. The cutoff indicator serves as an instrument:
- **First stage:** Being above the cutoff increases probability of treatment
- **Reduced form:** Being above the cutoff affects outcomes
- **IV estimate:** Ratio of reduced form to first stage = LATE for compliers at the cutoff

---

## Real-World Challenges and Practical Realities

### Challenge 1: Manipulation at the Cutoff
If people can control their running variable to be just above the threshold, the as-if-random assignment assumption breaks down. At Airbnb, hosts near 4.8 stars might ask friends for reviews to push above the Superhost threshold. At Uber, drivers near the deactivation cutoff might select only easy rides. This "bunching" above the cutoff invalidates RDD.

**What actually happens**: The team runs a McCrary density test and finds a small bump above the cutoff. Is it statistically significant? Maybe borderline. The team then argues about whether "mild bunching" is a problem or noise. In some cases, manipulation is obvious (academic grade cutoffs where teachers round up) but in many business settings it's ambiguous.

### Challenge 2: Local Treatment Effect Only
RDD estimates the effect ONLY at the cutoff. At Airbnb, the Superhost effect applies to hosts near 4.8 stars, not to hosts at 3.5 or 4.95. If the PM asks "what would happen if we lowered the threshold to 4.5?", RDD at 4.8 doesn't answer this -- the effect could be completely different at 4.5.

**What actually happens**: The team presents "Superhost status increases bookings by 3 per month" and the PM immediately asks "can we extrapolate this to ALL hosts?" The answer is "no, this is a local estimate" -- which limits its usefulness for policy decisions that affect the entire host population.

### Challenge 3: Bandwidth Selection Is Subjective
Too narrow a bandwidth gives high variance (few observations). Too wide introduces bias (units far from the cutoff are less comparable). The optimal bandwidth depends on unknown quantities. Different bandwidth selection methods (IK, CCT) can give different answers.

**What actually happens**: The team presents results with the "optimal" bandwidth, and a reviewer says "what if you use half that bandwidth?" The estimate changes by 40%. The team then shows a bandwidth sensitivity plot, which reveals that the estimate is unstable. This is an honest finding but makes the result less convincing.

### Challenge 4: Discrete Running Variables
Many real running variables aren't truly continuous. Airbnb ratings have granularity (4.78, 4.79, 4.80...). If the running variable has few distinct values near the cutoff, the "local" comparison has very few data points. Uber driver ratings rounded to one decimal place create even coarser bins.

**What actually happens**: With only 200 observations within 0.1 stars of the cutoff, the local linear regression has very little power. The CI is so wide that the result is uninformative. The team either has to use a wider bandwidth (more bias) or report an imprecise result.

### Challenge 5: Fuzzy RDD Complications
In practice, cutoffs are rarely perfectly enforced. At Uber, some drivers below 4.6 get deactivated and some above 4.6 don't (human review process). This requires Fuzzy RDD, which is essentially IV at the cutoff. All the problems of IV (weak first stage, LATE interpretation) now apply.

**What actually happens**: The first-stage "jump" in treatment probability at the cutoff is only 30% (from 10% deactivation below to 40% above). The Fuzzy RDD estimate inherits all the noise and LATE issues of IV, with an even smaller effective sample size.

---

## FAANG Interview Follow-Up Questions

### Q1: "You found a +3 booking effect at the Superhost threshold. Can we conclude that Superhost status is worth +3 bookings for all hosts?"
**What they're testing**: Do you understand the local nature of RDD?
**Strong answer**: "No -- the estimate is LOCAL to hosts near 4.8 stars. It tells us the effect of crossing the threshold for borderline hosts. Hosts at 4.2 stars are very different -- even if we could magically give them Superhost status, the effect might be different (probably larger, because the badge is more surprising relative to their actual quality). For policy decisions affecting all hosts, I'd need to combine RDD with other evidence: maybe HTE analysis from experiments or PSM at different quality levels."

### Q2: "The McCrary test shows a p-value of 0.08 for bunching above the cutoff. Do you proceed?"
**What they're testing**: How do you handle ambiguous evidence of manipulation?
**Strong answer**: "p = 0.08 is borderline. I'd investigate further: (1) plot the density histogram with small bins -- is the bunching visually obvious or subtle? (2) check if the bunching could be explained by natural rounding (e.g., hosts at 4.795 get rounded to 4.8), (3) test whether covariates (tenure, location) jump at the cutoff -- if they do, sorting is likely, (4) use a 'donut hole' approach: exclude observations very close to the cutoff (e.g., within 0.02) and re-estimate. If the effect persists, it's more robust to manipulation. I'd report all of this transparently."

### Q3: "Why not just run a regression of bookings on Superhost status with controls, instead of RDD?"
**What they're testing**: Do you understand selection bias vs. local randomization?
**Strong answer**: "OLS with controls gives a biased estimate because Superhosts are fundamentally better hosts -- they have higher response rates, cleaner listings, more experience. No amount of controls captures everything. RDD exploits the fact that hosts at 4.79 and 4.81 are essentially identical in quality -- the tiny difference that puts one above the threshold and one below is as-if random. This local comparison eliminates selection bias without needing to measure every confounder. The trade-off is that OLS uses the full sample (more power, more bias) while RDD uses only the local sample (less power, less bias)."

### Q4: "Your optimal bandwidth is 0.15 (4.65 to 4.95). That includes hosts from 4.65 who might be very different from hosts at 4.80. Isn't that too wide?"
**What they're testing**: Do you understand the bias-variance trade-off in bandwidth?
**Strong answer**: "Yes, wider bandwidths introduce bias because farther-away units are less comparable. But narrower bandwidths increase variance because fewer observations are used. The optimal bandwidth (e.g., from Imbens-Kalyanaraman or Calonico-Cattaneo-Titiunik) balances these. I'd address this by: (1) using a local LINEAR regression (not just comparing means), which models the relationship between score and outcome on each side, reducing bias, (2) using a triangular kernel that downweights observations far from the cutoff, (3) showing results across bandwidths [0.05, 0.10, 0.15, 0.20, 0.25] -- if the estimate is stable, the bandwidth choice isn't driving the result."

### Q5: "A colleague suggests using Superhost status as an A/B test -- randomly assign the badge to some eligible hosts and not others. Why is this better than RDD?"
**What they're testing**: Do you understand the hierarchy of causal methods?
**Strong answer**: "It's better in every way: (1) estimates the ATE, not just the local effect at the cutoff, (2) eliminates all confounding by construction, (3) higher statistical power because it uses the full experimental sample, (4) cleaner interpretation. The only downsides are practical: (1) ethical concerns about withholding a 'earned' badge from qualified hosts, (2) implementation cost, (3) potential host backlash. RDD is what we use when we CAN'T experiment. If we can, we should absolutely prefer the experiment."

### Q6: "Imagine the Superhost threshold was changed from 4.8 to 4.7 a year ago. How would you use BOTH cutoffs?"
**What they're testing**: Can you extend RDD to richer settings?
**Strong answer**: "This is a powerful setup. I can: (1) estimate RDD effects at BOTH cutoffs (4.7 and 4.8) to see if the Superhost effect differs at different quality levels, (2) use hosts who were Superhosts under the old threshold (4.8) but not the new (4.7) as a 'difference-in-discontinuities' design -- they lost Superhost status not because of their behavior but because the threshold moved, (3) the threshold CHANGE is essentially a natural experiment: before vs. after the change for hosts between 4.7 and 4.8. This combines RDD with DiD for a stronger identification strategy."
