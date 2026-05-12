# Causal Inference -- Detailed Notes

## Table of Contents

1. [Core Problem Framing](#1-core-problem-framing)
2. [Causal Inference Methods](#2-causal-inference-methods)
   - 2.1 [Propensity Score Matching (PSM)](#21-propensity-score-matching-psm)
   - 2.2 [Difference-in-Differences (DiD)](#22-difference-in-differences-did)
   - 2.3 [Synthetic Control](#23-synthetic-control)
   - 2.4 [Interrupted Time Series (ITS)](#24-interrupted-time-series-its)
   - 2.5 [Instrumental Variables (IV)](#25-instrumental-variables-iv)
   - 2.6 [Regression Discontinuity Design (RDD)](#26-regression-discontinuity-design-rdd)
   - 2.7 [Heterogeneous Treatment Effects (HTE)](#27-heterogeneous-treatment-effects-hte)
   - 2.8 [Uplift Modeling](#28-uplift-modeling)
   - 2.9 [Complier Average Causal Effect (CACE / LATE)](#29-complier-average-causal-effect-cace--late)
3. [Causal Feature Attribution / Drivers Analysis](#3-causal-feature-attribution--drivers-analysis)
4. [Method Selection Decision Framework](#4-method-selection-decision-framework)
5. [Industry References](#5-industry-references)
6. [Key Pitfalls and Practical Advice](#6-key-pitfalls-and-practical-advice)
7. [Cross-Reference with Companion Notebooks](#7-cross-reference-with-companion-notebooks)

---

## 1. Core Problem Framing

### 1.1 The Fundamental Problem of Causal Inference

The central challenge in causal inference is that we can **never observe both outcomes** (treated and untreated) for the same unit at the same time. This is known as the **fundamental problem of causal inference** (Holland, 1986).

- **Potential Outcomes Framework (Rubin Causal Model)**: For each unit *i*, there are two potential outcomes:
  - Y_i(1) = outcome if treated
  - Y_i(0) = outcome if not treated
  - The **individual treatment effect** is: tau_i = Y_i(1) - Y_i(0)
  - We only ever observe one of these. The other is the **counterfactual**.

- **The goal**: Estimate the **Average Treatment Effect (ATE)**:
  - ATE = E[Y(1) - Y(0)]
  - Since we can't observe both for the same person, we need methods to construct credible counterfactuals.

### 1.2 Confounders and Directed Acyclic Graphs (DAGs)

A **confounder** is a variable that influences both the treatment assignment and the outcome. If confounders are not accounted for, the estimated treatment effect will be **biased**.

```
Confounder (X)
    |         \
    v          v
Treatment (T) --> Outcome (Y)
```

- X causes both T and Y. If we ignore X and simply compare treated vs. untreated outcomes, the difference reflects both the true causal effect of T on Y **and** the effect of X.
- **DAGs** (Directed Acyclic Graphs) are the formal tool for mapping out these causal relationships. They help identify:
  - Which variables are confounders (must be controlled for)
  - Which variables are mediators (should NOT be controlled for)
  - Which variables are colliders (controlling for them introduces bias)

### 1.3 Pre-Period vs. Post-Period

Many causal inference designs rely on a temporal structure:

- **Pre-period**: The time before the treatment/intervention is introduced. Used to establish baseline behavior and verify that treated and control groups were comparable.
- **Post-period**: The time after treatment. Outcomes here are compared across groups to estimate the causal effect.

The quality of pre-period matching or parallel trends is critical to the credibility of most observational causal designs.

### 1.4 Treatment Definition

Precise definition of what constitutes "treatment" matters enormously:

- **Binary treatment**: Did the user subscribe or not? Did they receive the discount or not?
- **Dosage/intensity**: How much did they engage? How large was the discount?
- **Timing**: When did they enter treatment? The "treatment period" must be clearly defined.

For example, in a Game Pass study: a user must both claim access AND engage with titles within the first 30 days to be classified as "treated." Simply having access without engagement may not constitute meaningful treatment.

---

## 2. Causal Inference Methods

### 2.1 Propensity Score Matching (PSM)

**What it is**: A method for reducing selection bias in observational studies by matching treated and untreated units that have a similar probability (propensity) of receiving treatment.

**Core idea**: Instead of matching on many individual covariates (which becomes computationally prohibitive in high dimensions -- the "curse of dimensionality"), collapse all covariates into a single number:

```
e(X) = P(Treatment = 1 | X)
```

This is the **propensity score** -- the probability that a unit receives treatment given its observed characteristics.

**How it works**:

1. **Estimate the propensity score**: Fit a logistic regression (or other classifier) predicting treatment assignment from pre-treatment covariates (age, engagement level, platform usage, demographics, behavioral features).
2. **Match treated and control units**: For each treated unit, find one or more control units with the closest propensity score.
3. **Check balance**: Verify that after matching, the distributions of covariates are similar across treated and control groups. Standardized mean differences should be small (< 0.1).
4. **Estimate the treatment effect**: Compare outcomes between matched treated and control units.

**Matching variants**:
- **Nearest-neighbor matching**: Match each treated unit to the closest control unit on propensity score
- **Caliper matching**: Only match if the propensity score difference is within a threshold
- **Exact matching**: Require exact match on certain key variables (expensive, often infeasible)
- **Fuzzy matching**: Allow approximate matches when exact matching is too restrictive

**Critical issues**:

- **Calibration**: The propensity score model must produce well-calibrated probabilities. A highly accurate classifier that produces uncalibrated scores (e.g., all predictions near 0 or 1) will fail at matching. Calibration should be verified before proceeding.
- **Common support / overlap**: There must be substantial overlap in the propensity score distributions of treated and control groups. If treated units have propensity scores in a range where no control units exist, those units cannot be matched and must be dropped.
- **Sample size loss**: Matching inevitably reduces the sample. Starting with 10,000 units, you may end up with only 6,000 after matching. This is expected but must be accounted for in power calculations.
- **Unobserved confounders**: PSM only handles observed confounders. If there are important unmeasured variables influencing both treatment and outcome, the estimate will still be biased.

**Use case -- Subscription impact on revenue (Xbox Game Pass)**:
- Treatment: User subscribes to Game Pass
- Outcome: Revenue contribution over the next 6 months
- Covariates for propensity score: Pre-subscription engagement (hours played, titles played, purchase history), demographics (age, region), platform tenure
- Match subscribers to non-subscribers with similar propensity scores
- Compare post-subscription revenue between matched groups to estimate the incremental revenue effect of Game Pass

**Companion notebook**: [05-Propensity-Score.ipynb](causal-inference-in-python-code-main/causal-inference-in-python/05-Propensity-Score.ipynb)

---

### 2.2 Difference-in-Differences (DiD)

**What it is**: A quasi-experimental design that estimates causal effects by comparing the change in outcomes over time between a group that receives treatment and a group that does not.

**Core idea**: Even if treated and control groups differ in their baseline levels, as long as they would have followed **parallel trends** in the absence of treatment, we can attribute any divergence after treatment to the causal effect.

```
Treatment Effect = (Y_treated_post - Y_treated_pre) - (Y_control_post - Y_control_pre)
```

**The parallel trends assumption**: In the absence of treatment, the treated group's outcome would have changed at the same rate as the control group's. This is the key identifying assumption and **cannot be directly tested** (since we never observe the treated group's counterfactual). However, we can check whether pre-treatment trends were parallel as supporting evidence.

**How it works**:

1. **Define groups**: Identify treated and control groups
2. **Define periods**: Clearly specify pre-treatment and post-treatment time periods
3. **Verify parallel trends**: Plot pre-treatment outcomes for both groups and check they move in parallel
4. **Estimate the DiD**: Use regression with interaction terms:
   - Y = beta_0 + beta_1 * Treatment + beta_2 * Post + beta_3 * (Treatment x Post) + epsilon
   - beta_3 is the DiD estimate (the causal effect)

**Extensions**:
- **Staggered DiD**: When different units receive treatment at different times. Requires more careful econometric treatment (Callaway & Sant'Anna, Sun & Abraham).
- **Multiple time periods**: Average effects across many pre/post comparisons for robustness.
- **Event study design**: Estimate the treatment effect at each time period relative to the treatment date to visualize the dynamic effect and verify pre-trends.

**Use case -- Feature launch impact on MAU**:
- A product team launches a new feature (e.g., personalized recommendations)
- Treated group: Users who were exposed to the feature
- Control group: Users who were not yet exposed
- Compare monthly active usage before and after the launch for both groups
- The DiD estimate captures the incremental impact of the feature on engagement

**Use case -- Game title release into Game Pass**:
- When a major title is added to Game Pass, measure its incremental revenue effect
- Treated: Users who engaged with the new title
- Control: Users who did not engage with it
- Compare revenue changes pre/post title release for both groups
- Must account for self-selection (users who engage may already be more active) -- combine with matching if needed

**Companion notebook**: [08-Difference-in-Differences.ipynb](causal-inference-in-python-code-main/causal-inference-in-python/08-Difference-in-Differences.ipynb)

---

### 2.3 Synthetic Control

**What it is**: A method that constructs a "synthetic" version of the treated unit by finding an optimal weighted combination of untreated units. Primarily used when the treatment occurs at an aggregate level (a country, a region, a store) and there are multiple untreated units available as donors.

**Core idea**: Instead of finding one perfect control, create an artificial control by blending multiple untreated units so that the blend closely tracks the treated unit's pre-treatment outcomes.

**How it works**:

1. **Pre-treatment period**: Find weights W for the donor (untreated) units such that the weighted combination of their outcomes closely matches the treated unit's outcomes during the pre-period.
2. **Post-treatment period**: Apply the same weights to the donor units' post-treatment outcomes to estimate what the treated unit's outcome would have been without treatment.
3. **Treatment effect**: The difference between the treated unit's actual post-treatment outcome and the synthetic control's outcome.

**Key requirements**:
- A pool of untreated units that were NOT affected by the treatment
- A sufficiently long pre-treatment period to achieve good fit
- The treated unit's pre-treatment outcomes must lie within the "convex hull" of the donor units (i.e., the synthetic control cannot extrapolate)

**Why it's powerful**:
- Transparency: The weights are explicit, so you can see exactly which units contribute to the counterfactual
- Visual: The pre-treatment fit and post-treatment gap are easy to interpret on a time-series plot
- Inference: Permutation-based inference (placebo tests) by applying the method to each donor unit and checking whether the treated unit's effect is unusually large

**Use case -- Geo-level personalization launch**:
- A company like Xbox operates in many countries. Personalization is launched in one country (e.g., Brazil).
- Build a synthetic Brazil from weighted combination of other countries (e.g., 40% Mexico + 30% Argentina + 20% Colombia + 10% Chile) that matched Brazil's pre-launch engagement patterns.
- Post-launch, the gap between actual Brazil and synthetic Brazil is the estimated causal effect of personalization.

**Use case -- Regional pricing change**:
- Change subscription pricing in one region.
- Use other regions (that did not receive the price change) to build a synthetic control.
- Estimate the causal effect of the price change on subscriber growth and revenue.

**Companion notebook**: [09-Synthetic-Control.ipynb](causal-inference-in-python-code-main/causal-inference-in-python/09-Synthetic-Control.ipynb)

---

### 2.4 Interrupted Time Series (ITS)

**What it is**: A design for estimating the effect of an intervention when you have many repeated observations of the outcome over time for a single unit, and the intervention occurs at a known point.

**Core idea**: Model the pre-intervention trend and extrapolate it forward. The difference between the extrapolated trend and the actual post-intervention outcomes is the estimated causal effect.

**How it works**:

1. **Collect time-series data**: Many data points before and after the intervention
2. **Model the pre-intervention trend**: Fit a regression (often segmented regression) to the pre-intervention data:
   - Y_t = beta_0 + beta_1 * time + epsilon (pre-intervention trend)
3. **Model the post-intervention outcome**:
   - Y_t = beta_0 + beta_1 * time + beta_2 * intervention + beta_3 * (time_since_intervention) + epsilon
   - beta_2 captures the **immediate level change** at the point of intervention
   - beta_3 captures the **change in slope** (trend change) after intervention
4. **Inference**: Test whether beta_2 and/or beta_3 are statistically significant

**Requirements**:
- Many observations before and after the intervention (rule of thumb: at least 8-10 in each period, ideally many more)
- A clearly defined intervention point
- No other major events co-occurring with the intervention (threatens internal validity)

**Strengths and limitations**:
- Strength: Only needs a single unit (no control group required)
- Limitation: Vulnerable to co-occurring events that could explain the change
- Limitation: Relies on correct specification of the pre-trend model

**Use case -- Marketing campaign impact**:
- A company runs a major marketing campaign starting on a specific date
- Daily revenue is tracked for 60 days before and 60 days after
- Model the pre-campaign revenue trend and check whether the campaign caused a structural break (level shift and/or trend change) in daily revenue

---

### 2.5 Instrumental Variables (IV)

**What it is**: A method for estimating causal effects when there are unmeasured confounders, by exploiting a third variable (the "instrument") that affects treatment but has no direct effect on the outcome except through treatment.

**Core idea**: If you can't remove confounding directly, find a variable Z such that:
1. Z is correlated with the treatment T (**relevance**)
2. Z affects the outcome Y only through T (**exclusion restriction**)
3. Z is not correlated with the unmeasured confounders (**independence**)

```
Instrument (Z) --> Treatment (T) --> Outcome (Y)
                                       ^
                                       |
                              Unmeasured Confounder (U)
```

Z has no direct arrow to Y and no connection to U.

**How it works (Two-Stage Least Squares / 2SLS)**:

1. **First stage**: Regress treatment on the instrument:
   - T = alpha_0 + alpha_1 * Z + epsilon
   - Get predicted treatment values T_hat
2. **Second stage**: Regress outcome on predicted treatment:
   - Y = gamma_0 + gamma_1 * T_hat + eta
   - gamma_1 is the causal effect estimate (specifically, the LATE)

**Classic examples of instruments**:
- Random assignment as an instrument for actual treatment (when there is non-compliance)
- Distance to a facility as an instrument for facility usage
- Weather as an instrument for outdoor activities

**Use case -- Non-compliance in experiments**:
- Users are randomly assigned to receive a discount offer (Z = assignment)
- Some users don't redeem the discount (T = actual redemption)
- Outcome is subsequent spending (Y)
- Assignment (Z) is random, so it's independent of confounders
- Use assignment as an instrument for actual discount usage
- The IV estimate tells us the causal effect of actually using the discount among those who would comply with their assignment

**Companion notebook**: [11-Non-Compliance-and-Instruments.ipynb](causal-inference-in-python-code-main/causal-inference-in-python/11-Non-Compliance-and-Instruments.ipynb)

---

### 2.6 Regression Discontinuity Design (RDD)

**What it is**: A quasi-experimental design that exploits a known cutoff (threshold) in a continuous assignment variable to estimate causal effects. Units just above the cutoff receive treatment; units just below do not.

**Core idea**: Units just above and just below the cutoff are essentially randomly assigned to treatment (since their position relative to the cutoff is as-if random). Comparing their outcomes gives a local causal estimate.

**Two types**:
- **Sharp RDD**: Treatment is a deterministic function of the running variable. Everyone above the cutoff gets treatment; no one below does.
- **Fuzzy RDD**: The probability of treatment jumps at the cutoff but doesn't go from 0 to 1. Some units above the cutoff don't get treatment, and/or some below do. Uses IV-like estimation.

**How it works**:

1. **Identify the running variable and cutoff**: e.g., a spending score with a threshold at $500
2. **Plot outcomes against the running variable**: Look for a discontinuity (jump) at the cutoff
3. **Estimate the local effect**: Fit local linear regressions on either side of the cutoff
4. **Bandwidth selection**: Choose how far from the cutoff to include observations (trade-off between bias and variance)

**Key assumption -- Continuity**: In the absence of treatment, the expected potential outcomes would be continuous through the cutoff. There should be no other reason for a jump at that exact point.

**Use case -- Loyalty tier thresholds**:
- Users who spend above $500 per quarter receive a premium loyalty tier with extra benefits
- Compare outcomes (retention, future spending) of users just above $500 vs. just below
- Since users near the threshold are very similar, the difference in outcomes estimates the causal effect of receiving premium tier status

---

### 2.7 Heterogeneous Treatment Effects (HTE)

**What it is**: The recognition that treatment effects are not uniform across all individuals. Different subgroups may experience larger or smaller (or even opposite) effects from the same treatment.

**Core idea**: Move beyond a single ATE to estimate **Conditional Average Treatment Effects (CATE)** -- the treatment effect conditional on observable characteristics:

```
CATE(x) = E[Y(1) - Y(0) | X = x]
```

**Why it matters**:
- A positive ATE could mask the fact that treatment helps some people and hurts others
- Targeting: Resources are finite. If you know which subgroups benefit most, you can target treatment to maximize impact.
- Personalization: In the subscription/gaming context, which types of users benefit most from a particular feature or offer?

**Methods for estimating HTE**:
- **Subgroup analysis**: Simple but atheoretical; risk of p-hacking
- **Causal forests** (Wager & Athey): Random forest adapted for treatment effect estimation
- **Meta-learners** (T-learner, S-learner, X-learner, R-learner): Different strategies for combining prediction models to estimate heterogeneous effects
- **Bayesian Additive Regression Trees (BART)**: Flexible nonparametric approach

**Use case -- Personalized offers**:
- Not all users respond the same to a 20% discount
- Heavy users might subscribe anyway (low incremental effect)
- Light users might need a bigger nudge (high incremental effect)
- Lapsed users might be re-engaged (moderate effect with high variance)
- Estimate CATE for each user segment to optimize offer allocation

**Companion notebooks**:
- [06-Effect-Heterogeneity.ipynb](causal-inference-in-python-code-main/causal-inference-in-python/06-Effect-Heterogeneity.ipynb)
- [07-Meta-Learners.ipynb](causal-inference-in-python-code-main/causal-inference-in-python/07-Meta-Learners.ipynb)

---

### 2.8 Uplift Modeling

**What it is**: A predictive modeling approach that directly estimates the incremental impact of a treatment (e.g., a marketing action) on an individual's behavior. It answers: "What is the right offer for the right person?"

**Core idea**: Classify individuals into four categories based on their response to treatment:

| Category | Without Treatment | With Treatment | Action |
|---|---|---|---|
| **Persuadables** | Would not convert | Converts | Target these |
| **Sure things** | Would convert | Converts | Don't waste treatment |
| **Lost causes** | Would not convert | Does not convert | Don't waste treatment |
| **Sleeping dogs** | Would convert | Does not convert | Avoid treatment (it hurts) |

The goal is to identify **persuadables** -- people for whom the treatment makes a positive difference.

**Methods**:
- **Two-model approach (T-learner)**: Train separate models for treated and control. Uplift = P(outcome | treated) - P(outcome | control).
- **Single-model approach**: Include treatment as a feature in one model
- **Direct uplift models**: Modified tree-based algorithms that directly optimize for uplift (e.g., causal trees)

**Use case -- Marketing spend optimization**:
- A company has run multiple campaigns with different discount levels (10%, 20%, 30% off) and different channels (email, push notification, in-app)
- For each customer, estimate the incremental lift in conversion (or revenue) from each offer type
- Allocate the optimal offer to each customer to maximize total ROI while controlling cost

**Connection to HTE**: Uplift modeling is essentially the operational application of heterogeneous treatment effect estimation. HTE gives you the estimates; uplift modeling turns those estimates into targeting decisions.

---

### 2.9 Complier Average Causal Effect (CACE / LATE)

**What it is**: The causal effect estimated specifically among "compliers" -- individuals who take the treatment when assigned to treatment and don't take it when assigned to control.

**Context -- Non-compliance**: In many experiments, not everyone in the treatment group actually receives/uses the treatment, and some in the control group may find a way to get it. This creates four types of participants:

| Type | Assigned Treatment | Assigned Control |
|---|---|---|
| **Compliers** | Takes treatment | Doesn't take treatment |
| **Always-takers** | Takes treatment | Takes treatment |
| **Never-takers** | Doesn't take treatment | Doesn't take treatment |
| **Defiers** | Doesn't take treatment | Takes treatment |

**Why CACE matters**:
- **Intent-to-Treat (ITT)**: Compares outcomes by assignment, regardless of compliance. Unbiased but diluted (underestimates the effect for those who actually comply).
- **CACE/LATE**: Estimates the effect for compliers specifically. More relevant for understanding the actual treatment effect but applies only to the complier subpopulation.
- Estimated using instrumental variables, with random assignment as the instrument for actual treatment.

**Use case -- Game Pass trial**:
- Users are randomly offered a free Game Pass trial (assignment = instrument)
- Some accept and use it (compliers); others ignore the offer (never-takers)
- Some users in the control group find ways to access Game Pass anyway (always-takers)
- ITT would underestimate the effect because many assigned-to-treatment users didn't actually engage
- CACE gives the effect of Game Pass specifically for users who would use it when offered

---

## 3. Causal Feature Attribution / Drivers Analysis

**What it is**: Identifying which features or behaviors are **causally driving** an outcome (such as churn, revenue, or engagement), as opposed to merely being correlated with it.

**Why prediction is not enough**: A machine learning model might identify that "number of support tickets" is a strong predictor of churn. But does filing tickets *cause* churn, or do users who are already dissatisfied (and about to churn) file more tickets? The policy implications are completely different:
- If tickets cause churn: improve support quality
- If dissatisfaction causes both: address root causes of dissatisfaction

**Causal vs. predictive feature importance**:

| Aspect | Predictive | Causal |
|---|---|---|
| Question | What predicts Y? | What causes Y? |
| Confounders | Irrelevant (may even help prediction) | Must be controlled |
| Actionability | Low (can't act on correlations) | High (interventions are justified) |
| Methods | SHAP, feature importance | Causal forests, do-calculus, IV |

**How causal feature attribution works**:
1. **Construct a causal graph** (DAG) encoding domain knowledge about which variables affect which
2. **For each feature of interest**, estimate its causal effect on the outcome while controlling for appropriate confounders (identified from the DAG)
3. **Account for interactions**: A feature's causal impact may depend on other variables. For example, the effect of "engagement with title X" on churn may depend on whether the user also plays other titles.
4. **Rank features by causal impact**: This gives actionable insights -- e.g., "increasing engagement with multiplayer features causally reduces churn by 15%, after accounting for self-selection"

**Tools**:
- **DoWhy** (Microsoft Research): Python library for causal inference -- model, identify, estimate, refute
- **EconML** (Microsoft Research): ML-based causal effect estimation, including causal forests and DML
- **CausalML** (Uber): Uplift modeling and causal inference library
- **Bayesian networks / probabilistic graphical models**: Encode causal structure and perform inference

**Use case -- Churn driver analysis**:
- For a gaming/subscription platform, behavioral features include: hours played, titles tried, multiplayer sessions, store purchases, friend list activity, support tickets, days since last login
- For each feature, estimate the causal reduction in churn probability
- Unlike standard feature importance (which conflates correlation and causation), this accounts for the fact that, e.g., users who buy from the store may already be more engaged (confounder)
- Result: A ranked list of behaviors that, if increased, would causally reduce churn -- directly actionable for product teams

---

## 4. Method Selection Decision Framework

### Decision Tree

```
Start: What data do you have?
|
|-- Randomized experiment available?
|   |-- YES: Is there full compliance?
|   |   |-- YES --> Standard ATE estimation (A/B test analysis)
|   |   |-- NO --> Instrumental Variables / CACE
|   |-- NO: Observational data
|       |-- Do you have repeated time-series data?
|       |   |-- YES: Multiple untreated units available?
|       |   |   |-- YES, many --> Synthetic Control
|       |   |   |-- Few / paired groups --> Difference-in-Differences
|       |   |-- Single unit, many time points --> Interrupted Time Series
|       |-- Cross-sectional data
|           |-- Is treatment assigned by a sharp cutoff?
|           |   |-- YES --> Regression Discontinuity Design
|           |   |-- NO: Are confounders measured?
|           |       |-- YES --> Propensity Score Matching / IPW
|           |       |-- Unmeasured confounders --> Instrumental Variables
```

### Quick-Reference Table

| Method | Data Structure | Key Assumption | Handles Unmeasured Confounders? | Typical Use |
|---|---|---|---|---|
| **PSM / IPW** | Cross-sectional or panel | No unmeasured confounders (unconfoundedness) | No | Observational treatment effects |
| **DiD** | Panel (pre/post, treated/control) | Parallel trends | Partially (time-invariant confounders OK) | Policy changes, feature launches |
| **Synthetic Control** | Panel (aggregate level) | Pre-treatment fit implies good counterfactual | Partially | Regional interventions, geo-experiments |
| **ITS** | Time series (single unit) | No co-occurring events; correct trend model | No | Campaigns, policy changes |
| **IV / 2SLS** | Cross-sectional or panel | Valid instrument (relevance + exclusion) | Yes | Non-compliance, unmeasured confounding |
| **RDD** | Cross-sectional with running variable | Continuity at cutoff | Yes (locally) | Threshold-based policies |
| **HTE / CATE** | Any of the above | Depends on underlying method | Depends | Personalization, targeting |
| **Uplift Modeling** | Experimental or observational | Depends on underlying method | Depends | Marketing optimization |
| **CACE / LATE** | Experiment with non-compliance | Monotonicity + valid instrument | Yes | Non-compliance adjustment |

---

## 5. Industry References

### Netflix
- One of the most advanced experimentation and causal inference teams in industry
- Published extensively on their **research blog** about experimentation platform design, interleaving for ranking, and causal inference for content decisions
- Key contribution: Scaling experimentation to millions of simultaneous A/B tests with proper statistical rigor
- Focus: Content recommendation, UI optimization, long-term subscriber retention

### Uber
- Published work on **observational causal inference** when A/B testing is infeasible (e.g., pricing, marketplace dynamics)
- **Targeting optimization and bidding**: Using causal methods to optimize rider/driver matching and promotional targeting
- Key conferences: Papers on causal inference applied to marketplace dynamics at KDD, NeurIPS

### Facebook (Meta)
- Research on **long-term return on investment** -- measuring the causal impact of features that play out over months or years
- **Reinforcement learning in practice**: Combining causal reasoning with sequential decision-making
- Key contribution: Interference in experiments (network effects in social platforms where one user's treatment affects another's outcomes)

### TripAdvisor
- **Customer segmentation with recommendation A/B tests**: Using causal inference to understand which user segments benefit from personalized recommendations
- Practical application of HTE in a travel/recommendation context

### Microsoft / Xbox
- **Game Pass incremental revenue**: Measuring the causal effect of Game Pass on user spending, engagement, and retention
- **Feature launch impact**: Using DiD and synthetic control for product launches
- **Geo-experiments**: Testing pricing and feature changes across different markets
- **DoWhy and EconML**: Open-source causal inference libraries built by Microsoft Research

### Airbnb
- Pioneer of **centralized experimentation platforms** in the data science organization
- Published on challenges of experimentation in marketplaces (two-sided markets with interference)
- Focus on "central data science" team structure -- embedding causal thinking across the organization

---

## 6. Key Pitfalls and Practical Advice

### Propensity Score Calibration
Calibration of the propensity score model is **critical** and must be verified before proceeding to matching. A model that predicts treatment with 95% accuracy but produces scores clustered at 0 and 1 will not yield useful matches. Use calibration plots and the Brier score to assess.

### Balance Checking After Matching
After matching, always check that the distributions of covariates are balanced between treated and control groups. Use standardized mean differences (SMD < 0.1 is a common threshold) and visual inspections (density plots, Love plots). If balance is poor, revisit the propensity score model or try different matching strategies.

### Sample Size Loss
Matching inevitably discards unmatched units. Starting with 10,000 users, you might end up with 6,000 after matching. This is a necessary trade-off between bias reduction and statistical power. Plan for this in advance and ensure you still have sufficient sample size for meaningful inference.

### Confounder Identification
The most dangerous confounders are those that affect both treatment and outcome. In a DAG, these are "backdoor paths." Miss an important confounder and your estimate is biased, no matter how sophisticated the method. Invest time in understanding the data-generating process through domain expertise and DAG construction.

### Prediction is Not Causation
Feature importance from a predictive ML model (XGBoost, random forest) tells you what is *associated* with the outcome, not what *causes* it. A feature may be highly predictive because it is:
- A confounder (causes both treatment and outcome)
- A collider (spuriously appears important when conditioned on)
- A proxy for the true cause

Acting on predictive associations without causal reasoning can lead to ineffective or counterproductive interventions.

### Verification and Critical Thinking
Causal claims require more scrutiny than predictive claims because they inform **interventions** (actions with real costs). Always:
- Perform sensitivity analyses (how robust are results to violations of assumptions?)
- Run placebo tests (apply the method to a period/unit where no effect should exist)
- Validate against experiments when possible
- Question whether the key assumptions (parallel trends, exclusion restriction, unconfoundedness) are plausible in your specific context

---

## 7. Cross-Reference with Companion Notebooks

The workspace includes notebooks from the O'Reilly book *Causal Inference in Python* that provide hands-on implementations of these methods.

| Concept | Notebook | Dataset(s) |
|---|---|---|
| Introduction & fundamentals | `01-Introduction-To-Causal-Inference.ipynb` | -- |
| Randomized experiments | `02-Randomised-Experiments-and-Stats-Review.ipynb` | `email_rnd_data.csv` |
| Graphical models / DAGs | `03-Graphical-Models.ipynb` | -- |
| Linear regression for causal inference | `04-The-Unreasonable-Effectiveness-of-Linear-Regression.ipynb` | `online_classroom.csv` |
| Propensity score matching | `05-Propensity-Score.ipynb` | `cross_sell_email.csv` |
| Heterogeneous treatment effects | `06-Effect-Heterogeneity.ipynb` | `discount_data.csv` |
| Meta-learners (T/S/X/R) | `07-Meta-Learners.ipynb` | `discount_data.csv` |
| Difference-in-Differences | `08-Difference-in-Differences.ipynb` | `online_mkt.csv`, `offline_mkt_staggered.csv` |
| Synthetic control | `09-Synthetic-Control.ipynb` | `short_offline_mkt_south.csv`, `short_offline_mkt_all_regions.csv` |
| Geo & switchback experiments | `10-Geo-and-Switchback-Experiments.ipynb` | `sb_exp_every.csv`, `sb_exp_opt.csv` |
| Non-compliance & instruments | `11-Non-Compliance-and-Instruments.ipynb` | `prime_card.csv`, `prime_card_discontinuity.csv` |

All notebooks are in: `causal-inference-in-python-code-main/causal-inference-in-python/`
All datasets are in: `causal-inference-in-python-code-main/causal-inference-in-python/data/`
