# Causal Inference -- Detailed Use Cases

Each use case below follows a structured template covering the full end-to-end workflow: business problem, causal framing, data requirements, methodology, implementation steps, interpretation, and pitfalls.

---

## Table of Contents

1. [Subscription Impact on Revenue (Propensity Score Matching)](#use-case-1-subscription-impact-on-revenue)
2. [Feature Launch Impact on Engagement (Difference-in-Differences)](#use-case-2-feature-launch-impact-on-engagement)
3. [Game Title Release into Game Pass (DiD + Matching)](#use-case-3-game-title-release-into-game-pass)
4. [Geo-Level Personalization Launch (Synthetic Control)](#use-case-4-geo-level-personalization-launch)
5. [Marketing Campaign Impact (Interrupted Time Series)](#use-case-5-marketing-campaign-impact)
6. [Discount Redemption with Non-Compliance (Instrumental Variables)](#use-case-6-discount-redemption-with-non-compliance)
7. [Loyalty Tier Threshold Effect (Regression Discontinuity)](#use-case-7-loyalty-tier-threshold-effect)
8. [Personalized Offer Optimization (HTE + Uplift)](#use-case-8-personalized-offer-optimization)
9. [Game Pass Free Trial with Non-Compliance (CACE)](#use-case-9-game-pass-free-trial-with-non-compliance)
10. [Churn Driver Analysis (Causal Feature Attribution)](#use-case-10-churn-driver-analysis)
11. [Regional Pricing Change (Synthetic Control)](#use-case-11-regional-pricing-change)
12. [Marketing Spend Optimization (Uplift Modeling)](#use-case-12-marketing-spend-optimization)

---

## Use Case 1: Subscription Impact on Revenue

**Method**: Propensity Score Matching (PSM)

### Business Problem

A gaming platform offers a subscription service (e.g., Game Pass). The business wants to know: **Does subscribing to Game Pass causally increase a user's total revenue contribution, or do high-revenue users simply self-select into the subscription?**

### Causal Framing

- **Treatment (T)**: User subscribes to Game Pass
- **Outcome (Y)**: Total revenue contribution over the next 6 months (subscriptions + in-game purchases + DLC)
- **Confounders (X)**: Pre-subscription engagement (hours played, titles owned, purchase history), demographics (age, region), platform tenure, device type
- **Counterfactual question**: What would the subscriber's revenue have been if they had NOT subscribed?

### Why We Can't Just Compare Means

Simply comparing revenue of subscribers vs. non-subscribers would be misleading because subscribers are likely already more engaged and higher-spending. The difference in revenue would reflect both the treatment effect AND the pre-existing differences.

### Data Requirements

| Data Element | Source | Granularity |
|---|---|---|
| Subscription status and date | Billing system | User-level |
| Revenue (pre and post) | Transaction logs | User x month |
| Hours played, titles played | Telemetry | User x month |
| Purchase history | Store transactions | User x month |
| Demographics | Account profiles | User-level |
| Platform tenure | Account creation date | User-level |

- **Pre-period**: 6 months of behavioral data before subscription date
- **Post-period**: 6 months of revenue data after subscription date
- **Sample**: All users who subscribed in a given month (treated) + all non-subscribers active in that month (control pool)

### Methodology Steps

**Step 1: Define the treatment window**
- Pick a cohort: users who subscribed in March 2025
- Pre-period: September 2024 -- February 2025
- Post-period: March 2025 -- August 2025

**Step 2: Engineer pre-treatment features**
- Average monthly hours played (pre-period)
- Number of unique titles played (pre-period)
- Total spending in pre-period
- Days since account creation
- Number of multiplayer sessions
- Region, age group, device type

**Step 3: Estimate propensity scores**

```python
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV

model = LogisticRegression(max_iter=1000)
calibrated = CalibratedClassifierCV(model, cv=5, method='isotonic')
calibrated.fit(X_pre_features, treatment_indicator)
propensity_scores = calibrated.predict_proba(X_pre_features)[:, 1]
```

**Step 4: Check common support**
- Plot propensity score distributions for treated and control
- Trim units outside the overlapping region (e.g., drop treated users with scores > 0.95 and control users with scores < 0.05)

**Step 5: Perform matching**

```python
from sklearn.neighbors import NearestNeighbors

nn = NearestNeighbors(n_neighbors=1, metric='euclidean')
nn.fit(propensity_scores[control_idx].reshape(-1, 1))
distances, indices = nn.kneighbors(propensity_scores[treated_idx].reshape(-1, 1))
```

- Apply a caliper (e.g., 0.05) to discard poor matches

**Step 6: Check balance**
- Compute standardized mean differences (SMD) for every covariate before and after matching
- Target: all SMD < 0.1 after matching
- Visualize with Love plots or density comparisons

**Step 7: Estimate the treatment effect**
- ATT (Average Treatment Effect on the Treated) = mean(Y_treated_post) - mean(Y_matched_control_post)
- Use bootstrap or Abadie-Imbens standard errors for inference

### Interpretation

- "After matching subscribers to non-subscribers with similar pre-period behavior, subscribers generated $12.40 more revenue per month on average (p < 0.01). This suggests that Game Pass causally increases revenue contribution, beyond what would be expected from pre-existing engagement patterns."

### Pitfalls

- If propensity scores are poorly calibrated, matches will be poor even if they look close numerically
- Unobserved confounders (e.g., "intent to spend" that isn't captured in behavioral data) can still bias results
- Heavy trimming of non-overlapping regions may limit generalizability
- Sample may shrink substantially (e.g., 50,000 treated users down to 35,000 after matching)

---

## Use Case 2: Feature Launch Impact on Engagement

**Method**: Difference-in-Differences (DiD)

### Business Problem

A product team launches a new recommendation feature on a platform. The question: **Did this feature causally increase monthly active users (MAU), or was the increase driven by other factors (seasonality, marketing, organic growth)?**

### Causal Framing

- **Treatment (T)**: Exposure to the new recommendation feature
- **Outcome (Y)**: Monthly active usage (days active per month)
- **Treatment group**: Users who were exposed to the feature (e.g., gradual rollout by region or user segment)
- **Control group**: Users not yet exposed
- **Key assumption**: Parallel trends -- in the absence of the feature, both groups would have followed the same trajectory

### Data Requirements

| Data Element | Source | Granularity |
|---|---|---|
| Feature exposure flag and date | Feature flag system | User-level |
| Daily/monthly active usage | Telemetry | User x day/month |
| User segment, region | Account data | User-level |

- At least 3-6 months of pre-launch data to verify parallel trends
- At least 1-3 months of post-launch data

### Methodology Steps

**Step 1: Define groups and time periods**
- Treated: Users in regions/segments that received the feature on launch date
- Control: Users in regions/segments that have not yet received it
- Pre-period: 6 months before launch
- Post-period: 3 months after launch

**Step 2: Verify parallel trends**
- Plot average monthly active days for treated and control groups across the pre-period
- Formally test: run event-study regression with leads (pre-treatment period dummies interacted with treatment indicator). All pre-treatment interaction coefficients should be statistically insignificant.

**Step 3: Estimate DiD**

```python
import statsmodels.formula.api as smf

model = smf.ols(
    'active_days ~ treated + post + treated:post + C(month) + C(region)',
    data=panel_data
).fit(cov_type='cluster', cov_kwds={'groups': panel_data['user_id']})

did_estimate = model.params['treated:post']
```

- The coefficient on `treated:post` is the DiD estimate
- Cluster standard errors at the user level to account for serial correlation

**Step 4: Robustness checks**
- Placebo test: Run DiD on a pre-treatment period where no effect should exist
- Vary the post-period window (1 month, 2 months, 3 months)
- Add covariates to control for observable differences

### Interpretation

- "Users exposed to the recommendation feature increased their monthly active days by 2.3 days (95% CI: 1.8 to 2.8) relative to unexposed users, controlling for time trends and regional differences. Pre-treatment trends were statistically parallel (all lead coefficients insignificant), supporting the causal interpretation."

### Pitfalls

- Violation of parallel trends: If the treated group was already trending upward before the feature launch, DiD will overestimate the effect
- Contamination: If control users find out about the feature or are indirectly affected (spillover)
- Staggered rollout requires more sophisticated DiD estimators (Callaway-Sant'Anna)

---

## Use Case 3: Game Title Release into Game Pass

**Method**: Difference-in-Differences + Propensity Score Matching

### Business Problem

When a major game title is added to Game Pass, **what is the incremental revenue impact?** Users who engage with new titles are self-selected (they're already more active), so naive comparison is biased.

### Causal Framing

- **Treatment (T)**: User engages with the newly added title within 30 days of its Game Pass release
- **Outcome (Y)**: Total revenue over the next 3 months (all sources)
- **Treatment definition nuance**: The user must both claim/download the title AND have meaningful engagement (e.g., > 2 hours played). Simply having access doesn't count.

### Methodology Steps

**Step 1: Define treatment precisely**
- Treated: Users who played the new title for > 2 hours within 30 days of release
- Control pool: Active Game Pass subscribers who did NOT play the new title
- Pre-period: 3 months before title release
- Post-period: 3 months after title release

**Step 2: Match on pre-period behavior using PSM**
- Estimate propensity scores based on pre-period features: engagement, spending, genre preferences, titles played
- Match treated users to control users with similar propensity scores
- This addresses the self-selection problem

**Step 3: Apply DiD on the matched sample**
- Compute the DiD estimate: change in revenue for matched treated vs. matched control
- This combines the benefits of both methods: matching handles selection on observables; DiD handles time-invariant unobservables

**Step 4: Distinguish title-level from platform-level effects**
- Break down revenue into: revenue from the new title itself, revenue from other titles, in-game purchase revenue
- Check whether the new title cannibalizes spending on other titles or generates net new revenue

### Interpretation

- "Users who engaged with Title X generated $8.50 more in total platform revenue over 3 months compared to matched non-engagers, with $5.20 from incremental spending beyond the title itself. The new title did not cannibalize other title spending."

---

## Use Case 4: Geo-Level Personalization Launch

**Method**: Synthetic Control

### Business Problem

A global platform launches a personalization feature in one country (e.g., Brazil). **What is the causal lift in engagement from personalization?** There is no randomized experiment -- the feature was launched nationwide in one market.

### Causal Framing

- **Treated unit**: Brazil (country-level)
- **Outcome (Y)**: Monthly average engagement (hours per user) at the country level
- **Donor pool**: Other countries where personalization was NOT launched (Mexico, Argentina, Colombia, Chile, Peru, etc.)
- **Counterfactual question**: What would Brazil's engagement have looked like without personalization?

### Data Requirements

| Data Element | Source | Granularity |
|---|---|---|
| Monthly avg. engagement | Telemetry aggregated | Country x month |
| Subscriber count | Billing system | Country x month |
| Revenue per user | Finance data | Country x month |
| Macro indicators (optional) | External data | Country x month |

- Pre-period: 12-24 months before launch (long pre-period needed for good synthetic control fit)
- Post-period: 6-12 months after launch

### Methodology Steps

**Step 1: Construct the donor pool**
- Include all countries that did NOT receive the personalization treatment during the study period
- Exclude countries that experienced major idiosyncratic shocks (e.g., a country where a console launched mid-period)

**Step 2: Find optimal weights**

```python
from SparseSC import fit as sparse_sc_fit
# Or using the synth package:
# Minimize the distance between the treated unit's pre-treatment outcomes
# and the weighted combination of donor units' pre-treatment outcomes
```

- Solve the optimization: find weights W such that sum(W_j * Y_j_pre) approximately equals Y_brazil_pre for all pre-treatment periods
- Constraints: weights are non-negative and sum to 1

**Step 3: Verify pre-treatment fit**
- Plot Brazil's actual pre-treatment engagement vs. synthetic Brazil
- The fit should be tight (RMSPE should be small)
- If the fit is poor, the synthetic control is unreliable

**Step 4: Estimate the treatment effect**
- Post-treatment: Gap = Y_brazil_actual - Y_synthetic_brazil
- This gap is the estimated causal effect of personalization

**Step 5: Inference via placebo tests**
- Apply the same procedure to each donor country (pretend each was treated)
- If Brazil's gap is much larger than the placebo gaps, the effect is statistically significant
- Compute the ratio of post-treatment RMSPE to pre-treatment RMSPE for Brazil vs. placebos

### Interpretation

- "Synthetic Brazil (composed of 35% Mexico, 25% Colombia, 20% Argentina, 15% Chile, 5% Peru) closely tracked actual Brazil's engagement for 18 months pre-launch (RMSPE = 0.12 hours). Post-launch, actual Brazil exceeded synthetic Brazil by 1.8 hours/user/month. Placebo tests show this gap exceeds all donor country gaps, corresponding to a p-value of 0.05."

### Pitfalls

- Poor pre-treatment fit invalidates the approach entirely
- Spillover: If the personalization launch in Brazil affects engagement in donor countries (e.g., through shared multiplayer), the synthetic control is compromised
- Requires aggregate-level data; cannot estimate individual-level effects

---

## Use Case 5: Marketing Campaign Impact

**Method**: Interrupted Time Series (ITS)

### Business Problem

A company runs a major marketing campaign (TV + digital) starting on a specific date. **Did the campaign cause a measurable increase in daily revenue, or was the increase part of an existing trend?**

### Causal Framing

- **Intervention**: Campaign launch on day T
- **Outcome (Y)**: Daily revenue
- **Unit**: The entire platform (single unit, many time points)
- **Counterfactual**: What would daily revenue have been if the campaign had not been launched?

### Data Requirements

| Data Element | Source | Granularity |
|---|---|---|
| Daily revenue | Finance / transactions | Day-level |
| Campaign start/end dates | Marketing calendar | -- |
| Known confounding events | Business calendar | Day-level (holidays, product launches, etc.) |

- Pre-campaign: At least 60-90 days of daily revenue data
- Post-campaign: At least 30-60 days

### Methodology Steps

**Step 1: Prepare the time-series data**
- Align to a daily grain
- Flag the intervention point
- Note any other events (holidays, competitor actions, product launches) that might co-occur

**Step 2: Visualize**
- Plot daily revenue with a vertical line at the campaign start
- Eyeball whether there is an obvious level shift or slope change

**Step 3: Fit the segmented regression model**

```python
import statsmodels.formula.api as smf

data['time'] = range(len(data))
data['post'] = (data['date'] >= campaign_start).astype(int)
data['time_since'] = data['time'] - campaign_start_idx
data['time_since'] = data['time_since'] * data['post']

model = smf.ols(
    'revenue ~ time + post + time_since',
    data=data
).fit(cov_type='HAC', cov_kwds={'maxlags': 7})
```

- `post` coefficient = immediate level change at intervention
- `time_since` coefficient = change in the revenue trend slope after intervention

**Step 4: Account for seasonality and autocorrelation**
- Add day-of-week dummies, month dummies, or holiday indicators
- Use Newey-West (HAC) standard errors to handle autocorrelation
- Alternatively, model using ARIMA with intervention indicators

**Step 5: Sensitivity analysis**
- Vary the pre/post window lengths
- Test alternative functional forms for the pre-trend
- Check whether similar "effects" appear at placebo dates

### Interpretation

- "The marketing campaign was associated with an immediate revenue increase of $15,200/day (p = 0.003) and an additional daily growth rate of $180/day (p = 0.02) compared to the pre-campaign trend. These effects are robust to inclusion of day-of-week and holiday controls."

### Pitfalls

- If another event co-occurs with the campaign (e.g., a competitor's outage, a holiday), the estimated effect is confounded
- Requires many pre-period observations to model the trend accurately
- Assumes the pre-trend model would have continued in the absence of intervention

---

## Use Case 6: Discount Redemption with Non-Compliance

**Method**: Instrumental Variables (IV / 2SLS)

### Business Problem

A platform randomly assigns users to receive a discount offer. Not all users redeem the discount. **What is the causal effect of actually using the discount on subsequent spending?**

### Causal Framing

- **Instrument (Z)**: Random assignment to receive the discount offer (binary: offered / not offered)
- **Treatment (T)**: Actually redeeming the discount (binary: redeemed / not redeemed)
- **Outcome (Y)**: Total spending in the next 3 months
- **Unmeasured confounder**: "Deal-seeking propensity" -- users who redeem discounts may be systematically different in unobserved ways

### Why Naive Analysis Fails

- Comparing redeemers vs. non-redeemers confounds the discount effect with self-selection (deal-seekers may have different spending patterns regardless)
- Even within the offered group, redeemers and non-redeemers differ

### Data Requirements

| Data Element | Source | Granularity |
|---|---|---|
| Random assignment indicator | Experiment system | User-level |
| Redemption indicator | Billing system | User-level |
| 3-month post-assignment spending | Transactions | User-level |
| Pre-assignment spending (optional) | Transactions | User-level |

### Methodology Steps

**Step 1: Verify instrument validity**
- Relevance: Check that assignment strongly predicts redemption (first-stage F-statistic > 10)
- Independence: Assignment was random, so this holds by design
- Exclusion: Assignment only affects spending through redemption (plausible if the offer email itself doesn't change behavior without redemption)

**Step 2: First stage regression**

```python
# First stage: T = alpha + beta * Z + epsilon
first_stage = smf.ols('redeemed ~ assigned', data=df).fit()
print(f"First stage F-stat: {first_stage.fvalue:.1f}")
# F > 10 indicates a strong instrument
```

**Step 3: Two-Stage Least Squares (2SLS)**

```python
from linearmodels.iv import IV2SLS

model = IV2SLS.from_formula(
    'spending_3m ~ 1 + [redeemed ~ assigned]',
    data=df
).fit()
```

- The coefficient on `redeemed` is the Local Average Treatment Effect (LATE) -- the effect of redemption for compliers

**Step 4: Compare with ITT and naive OLS**
- ITT (Intent-to-Treat): Simple comparison of offered vs. not offered (unbiased but diluted)
- Naive OLS: Comparison of redeemers vs. non-redeemers (biased by self-selection)
- IV estimate: Effect for compliers (unbiased for this subpopulation)
- Typically: ITT < IV < Naive OLS (the IV falls between, correcting for both dilution and selection)

### Interpretation

- "ITT estimate: being offered the discount increased 3-month spending by $4.20 on average. IV estimate: actually redeeming the discount increased 3-month spending by $18.50 among compliers (those who would redeem when offered and not when not offered). The naive OLS estimate of $25.30 is upward biased due to selection effects."

---

## Use Case 7: Loyalty Tier Threshold Effect

**Method**: Regression Discontinuity Design (RDD)

### Business Problem

Users who spend above $500 in a quarter are automatically upgraded to a "Premium" loyalty tier with benefits (free shipping, exclusive deals, priority support). **Does receiving Premium tier status causally increase future spending and retention, or are these users simply high-spenders by nature?**

### Causal Framing

- **Running variable**: Quarterly spending (continuous)
- **Cutoff**: $500
- **Treatment**: Premium tier status (assigned when spending >= $500)
- **Outcome**: Next-quarter spending and retention (binary: active or churned)
- **Key insight**: Users who spent $498 vs. $502 are essentially identical in their characteristics. The $4 difference that puts one user above and one below the threshold is effectively random.

### Data Requirements

| Data Element | Source | Granularity |
|---|---|---|
| Quarterly spending (running variable) | Transactions | User x quarter |
| Tier assignment and date | Loyalty system | User x quarter |
| Next-quarter spending | Transactions | User x quarter |
| Next-quarter retention | Activity logs | User x quarter |
| Demographics (for balance checks) | Account data | User-level |

### Methodology Steps

**Step 1: Visualize the discontinuity**
- Bin users by quarterly spending and plot average next-quarter spending for each bin
- Look for a visible jump at the $500 threshold

**Step 2: Check for manipulation**
- Run a McCrary density test: Is there bunching just above $500? If users strategically push spending above the threshold, the design is compromised.
- Plot the density of the running variable around the cutoff

**Step 3: Estimate the local treatment effect**

```python
from rdrobust import rdrobust

result = rdrobust(
    y=df['next_quarter_spending'],
    x=df['quarterly_spending'],
    c=500,  # cutoff
    kernel='triangular',
    bwselect='mserd'  # optimal bandwidth selection
)
print(result)
```

- Uses local polynomial regression on both sides of the cutoff
- Optimal bandwidth selection balances bias (too wide) vs. variance (too narrow)

**Step 4: Balance checks at the cutoff**
- Check that observable covariates (age, tenure, region) are continuous through the cutoff
- If they jump, it suggests manipulation or confounding

**Step 5: Sensitivity to bandwidth**
- Re-estimate with different bandwidths (half, double the optimal)
- Results should be qualitatively similar across bandwidths

### Interpretation

- "Users just above the $500 threshold (Premium tier) spent $45 more in the following quarter than users just below (95% CI: $22 to $68, p = 0.001). This local estimate suggests that Premium tier status causally increases spending by approximately 9%, at least for users near the threshold."

### Pitfalls

- Result is LOCAL: it only applies to users near the $500 cutoff, not all users
- Manipulation: If users can control their spending precisely to be above $500, the as-if-random assumption breaks down
- Fuzzy RDD: If the cutoff is not perfectly enforced (some users below $500 get Premium, or some above don't), use fuzzy RDD with IV estimation

---

## Use Case 8: Personalized Offer Optimization

**Method**: Heterogeneous Treatment Effects (HTE) + Uplift Modeling

### Business Problem

A subscription platform wants to reduce churn by offering targeted discounts. Not all users respond the same way. **Which users should receive which offer to maximize retention while minimizing discount costs?**

### Causal Framing

- **Treatment**: Discount offer (e.g., 10% off, 20% off, 30% off, or no offer)
- **Outcome**: Retention (binary: renewed subscription or churned within 30 days)
- **Heterogeneity**: Treatment effects vary by user characteristics (tenure, engagement level, past spending, region)
- **Goal**: Estimate CATE(x) = E[retention(offer) - retention(no offer) | X = x] for each user x and each offer level

### Data Requirements

| Data Element | Source | Granularity |
|---|---|---|
| Offer assignment (ideally random) | Experiment / CRM | User-level |
| Offer type (10/20/30% or none) | CRM system | User-level |
| 30-day retention outcome | Subscription system | User-level |
| Pre-offer features | Telemetry + accounts | User-level |

- Requires historical experimental data where different offers were randomly assigned
- Minimum sample: 10,000+ users per offer variant for reliable HTE estimation

### Methodology Steps

**Step 1: Train CATE estimators**

```python
from econml.dml import CausalForestDML

causal_forest = CausalForestDML(
    model_y=GradientBoostingRegressor(),
    model_t=GradientBoostingClassifier(),
    n_estimators=1000,
    min_samples_leaf=20,
    random_state=42
)
causal_forest.fit(Y=retention, T=offer_level, X=user_features, W=confounders)

cate_estimates = causal_forest.effect(X=user_features)
```

**Step 2: Identify persuadables**
- For each user, predict the uplift (incremental retention) from each offer level
- Classify users:
  - **Persuadables** (high uplift): Offer the cheapest effective discount
  - **Sure things** (would retain anyway): No offer needed
  - **Lost causes** (won't retain regardless): Don't waste discount budget
  - **Sleeping dogs** (offer backfires): Avoid contacting

**Step 3: Optimize offer allocation**

```python
# For each user, find the offer that maximizes:
# net_value = P(retain | offer) * LTV - discount_cost
for user in users:
    best_offer = max(offers, key=lambda o: cate[user][o] * ltv[user] - cost[o])
    assignment[user] = best_offer
```

**Step 4: Validate with a holdout experiment**
- Randomly split users into:
  - Model-targeted group: Each user gets the model-recommended offer
  - Random-offer group: Users get random offers (benchmark)
  - No-offer group: Control
- Compare retention and total cost across groups

### Interpretation

- "The CATE model identified that 23% of at-risk users are persuadable with a 10% discount (uplift in retention: +18pp), while 15% require a 20% discount (uplift: +25pp). 40% of users would retain without any offer. Targeting based on CATE estimates increased overall retention by 12% while reducing discount spend by 35% compared to blanket 20% discounts."

---

## Use Case 9: Game Pass Free Trial with Non-Compliance

**Method**: Complier Average Causal Effect (CACE / LATE)

### Business Problem

Users are randomly offered a 14-day free Game Pass trial. Many offered users don't activate the trial. **What is the effect of actually using Game Pass on long-term spending for users who would take the trial when offered?**

### Causal Framing

- **Instrument (Z)**: Random trial offer (offered / not offered)
- **Treatment (T)**: Actually activating and using the trial
- **Outcome (Y)**: Spending over the next 12 months
- **Compliance types**:
  - Compliers: Activate trial when offered, would not use Game Pass otherwise
  - Always-takers: Would find a way to use Game Pass regardless of offer
  - Never-takers: Ignore the offer even when received

### Methodology Steps

**Step 1: Measure compliance rates**

```
Offered group (Z=1):   N = 50,000
  - Activated trial:   60%  (compliers + always-takers)
  - Did not activate:  40%  (never-takers)

Not-offered group (Z=0):  N = 50,000
  - Used Game Pass:    10%  (always-takers)
  - Did not use:       90%  (compliers + never-takers)
```

- Proportion of compliers = 60% - 10% = 50%

**Step 2: Compute ITT (Intent-to-Treat)**
- ITT = E[Y | Z=1] - E[Y | Z=0]
- This is the average effect of being offered the trial, regardless of compliance

**Step 3: Compute CACE (Wald estimator)**
- CACE = ITT / compliance_rate = ITT / (P(T=1|Z=1) - P(T=1|Z=0))
- This scales up the ITT to account for the fact that only compliers are affected

```python
ITT = df[df['offered']==1]['spending_12m'].mean() - df[df['offered']==0]['spending_12m'].mean()
compliance_rate = df[df['offered']==1]['activated'].mean() - df[df['offered']==0]['activated'].mean()
CACE = ITT / compliance_rate
```

**Step 4: Interpret the subpopulations**
- CACE applies to **compliers only** -- users who would activate the trial when offered and would not use Game Pass otherwise
- It does NOT apply to always-takers (who would use Game Pass anyway) or never-takers (who won't use it regardless)
- This is the most policy-relevant group: they are the ones whose behavior is changed by the offer

### Interpretation

- "ITT: Being offered a free trial increased 12-month spending by $8.40 on average. CACE: Among compliers (50% of users), actually using the Game Pass trial increased 12-month spending by $16.80. This suggests that for users on the margin (those who would try Game Pass if offered but wouldn't seek it out), the trial experience has a substantial positive effect on long-term monetization."

---

## Use Case 10: Churn Driver Analysis

**Method**: Causal Feature Attribution (Causal Graphs + Causal Forests)

### Business Problem

Churn is increasing on a subscription platform. Product leadership asks: **What is actually driving churn? What behaviors should we invest in promoting to reduce churn?** This is different from "what predicts churn" -- we need actionable causal drivers.

### Why Prediction is Insufficient

A predictive churn model (XGBoost, neural net) might identify "days since last login" as the top predictor. But this is tautological -- users who haven't logged in recently are about to churn by definition. The product team can't act on "make users log in more" without knowing what upstream behaviors drive login frequency.

### Causal Framing

- **Outcome (Y)**: 90-day churn (binary)
- **Candidate causal features (X)**: Multiplayer sessions, titles played, store purchases, friend interactions, support tickets, achievement completions, hours in single-player vs. multiplayer
- **Confounders**: Account age, region, device, acquisition channel
- **Goal**: For each behavior X_j, estimate the causal effect on churn: dP(churn) / dX_j, controlling for all other relevant variables

### Methodology Steps

**Step 1: Construct the causal DAG**
- Use domain knowledge (product managers, user research, prior studies) to map out causal relationships
- Identify which variables are confounders, mediators, and colliders
- This determines what to control for when estimating each feature's causal effect

**Step 2: For each candidate driver, estimate the causal effect**

```python
from econml.dml import LinearDML

for feature in candidate_drivers:
    model = LinearDML(
        model_y=GradientBoostingRegressor(),
        model_t=GradientBoostingRegressor(),
        random_state=42
    )
    model.fit(
        Y=churn_indicator,
        T=df[feature],
        X=df[effect_modifiers],
        W=df[confounders]
    )
    ate = model.ate()
    print(f"{feature}: ATE on churn = {ate:.4f}")
```

**Step 3: Rank features by causal impact**
- Create a ranked list: which behaviors, if increased by one unit, would reduce churn probability the most?
- Account for feasibility: some behaviors are easier to promote than others

**Step 4: Validate causal claims**
- If possible, run small experiments to validate the top causal drivers
- Use sensitivity analysis to check robustness to unmeasured confounding

### Interpretation

- "Causal analysis identified three actionable drivers of churn reduction: (1) Adding one multiplayer session per week reduces churn probability by 4.2pp (p < 0.01), (2) Playing a second unique title per month reduces churn by 3.1pp (p < 0.01), (3) Making one friend connection reduces churn by 2.8pp (p = 0.02). In contrast, support tickets (strong predictive feature) have no causal effect on churn -- they are a symptom, not a cause."

---

## Use Case 11: Regional Pricing Change

**Method**: Synthetic Control

### Business Problem

A streaming/gaming platform changes subscription pricing in one country (e.g., increases price by 15% in Canada). **What is the causal effect of the price increase on subscriber growth and revenue?**

### Methodology Steps

**Step 1: Define treated unit and donor pool**
- Treated: Canada
- Donors: Other countries with similar market characteristics (UK, Australia, Nordic countries, etc.) that did NOT experience a price change

**Step 2: Build synthetic Canada**
- Use pre-price-change data (12-24 months) on monthly subscriber count, ARPU, and engagement
- Find weights on donor countries that minimize the pre-treatment prediction error for Canada

**Step 3: Post-treatment gap**
- After the price increase, compare actual Canada to synthetic Canada
- Decompose: subscriber count effect vs. ARPU effect vs. total revenue effect

**Step 4: Quantify trade-off**
- Did the 15% price increase more than offset any subscriber losses?
- Net revenue effect = (new ARPU x new subscriber count) - (old ARPU x old subscriber count)

### Interpretation

- "Synthetic Canada (45% UK + 30% Australia + 25% Netherlands) closely tracked actual Canada's subscriber trajectory for 18 months. Post-price increase, actual Canada had 3.2% fewer subscribers than synthetic Canada, but 11.8% higher revenue. The price increase was net-positive for revenue despite modest subscriber losses."

---

## Use Case 12: Marketing Spend Optimization

**Method**: Uplift Modeling (Multi-Treatment)

### Business Problem

A marketing team has budget for retention campaigns. They can send: (A) a personalized email, (B) a push notification with a 10% discount, (C) a personalized email + 20% discount, or (D) no action. **How should they allocate treatments across users to maximize retained revenue while minimizing cost?**

### Methodology Steps

**Step 1: Collect historical multi-treatment experiment data**
- Past campaigns where users were randomly assigned to A, B, C, or D
- Record treatment, retention outcome, and user features

**Step 2: Train multi-treatment uplift model**

```python
from causalml.inference.meta import BaseTClassifier
from xgboost import XGBClassifier

uplift_model = BaseTClassifier(
    learner=XGBClassifier(n_estimators=200, max_depth=4),
    control_name='no_action'
)
uplift_model.fit(X=features, treatment=treatment_col, y=retention)
uplift_predictions = uplift_model.predict(X=new_user_features)
```

**Step 3: Compute net value for each user-treatment pair**
- Net value = uplift_in_retention(user, treatment) x LTV(user) - cost(treatment)
- Assign each user to the treatment with the highest net value
- Respect budget constraints (e.g., limited number of 20% discounts available)

**Step 4: Deploy and measure**
- Implement the targeting policy
- Hold out a random 10% for uniform random assignment (to measure ongoing calibration)
- Compare model-targeted group vs. random group on total retained revenue and total cost

### Interpretation

- "Optimized targeting allocated personalized emails (low cost) to 45% of users, push + 10% discount to 30% of users, and email + 20% discount to only 12% of users (high-value at-risk users). 13% received no action (sure things). This policy increased retention by 8% over random allocation while reducing total discount spending by 28%."

---

## Summary: Mapping Problems to Methods

| Business Question | Primary Method | Fallback Method |
|---|---|---|
| Does our subscription causally increase revenue? | PSM | DiD (if panel data) |
| What was the impact of a feature launch? | DiD | Synthetic Control |
| Impact of a game title release? | DiD + PSM | Synthetic Control |
| Impact of launching in a new market? | Synthetic Control | DiD |
| Did our marketing campaign work? | ITS | DiD (with control region) |
| What is the effect of using a discount? | IV (2SLS) | CACE |
| Does a loyalty tier cause more spending? | RDD | PSM |
| Which users should get which offer? | HTE / Uplift | Causal Forest |
| What is the effect for people who actually comply? | CACE / LATE | IV |
| What is driving our churn? | Causal feature attribution | DoWhy / DAG analysis |
| What is the optimal marketing allocation? | Uplift Modeling | Multi-arm bandit |
| Impact of a price change in one region? | Synthetic Control | ITS |
