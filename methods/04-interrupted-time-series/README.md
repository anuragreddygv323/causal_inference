# Interrupted Time Series (ITS)

## What It Is and When to Use It
Estimates causal effects from a single unit's time series data with a known intervention point. Models the pre-intervention trend and checks for level and slope changes after the intervention using segmented regression.

**Use when**: Single unit (entire platform, one store, one country), many time points before and after intervention, clear intervention date, no control group available.
**Do NOT use when**: You have a control group (use DiD), multiple donor units (use SC), or very few time points.

## Industry Use Cases

### Use Case 1: Uber — Platform-Wide Marketing Campaign Impact
- **Business question**: Did a major TV+digital marketing campaign increase daily ride revenue?
- **Outcome**: Daily platform revenue
- **Why ITS**: Campaign was platform-wide (no control group), have 180+ days of daily data, clear campaign start date
- **Alternatives**: DiD ruled out (no control — campaign affects all markets). SC ruled out (single platform, no donor pool). PSM not applicable (no user-level treatment assignment).

### Use Case 2: Netflix — Price Increase Impact on Subscriber Churn
- **Business question**: Did a subscription price increase cause a spike in cancellations?
- **Outcome**: Daily cancellation rate
- **Why ITS**: Price increase was universal (all subscribers affected simultaneously), long daily cancellation history available
- **Alternatives**: DiD (no control group — everyone faces the new price). SC (single platform, no donor).

### Use Case 3: Xbox — Console Launch Impact on Game Sales
- **Business question**: Did the Xbox Series X launch date cause a structural increase in digital game sales?
- **Outcome**: Weekly digital game sales revenue
- **Why ITS**: Platform-wide event, clear launch date, long sales history available
- **Alternatives**: DiD (no untreated platform exists). SC (no donor pool of comparable platforms).

### Use Case 4: Airbnb — COVID Lockdown Impact on Bookings
- **Business question**: What was the immediate and trend impact of COVID lockdowns on Airbnb bookings?
- **Outcome**: Daily booking volume
- **Why ITS**: Universal shock affecting all markets, no "control" for COVID, massive time series available
- **Alternatives**: SC (could use other travel platforms but data access is limited). DiD (no control group unaffected by lockdowns).

## Key Assumptions
- **Linearity of pre-trend**: The pre-intervention trend is well-approximated by the specified functional form (usually linear)
- **No co-occurring events**: Nothing else changed at the intervention point that could explain the outcome shift
- **Stable composition**: The population/unit generating the time series doesn't fundamentally change at the intervention
- **Sufficient pre/post data**: Enough time points on both sides to estimate trends reliably (rule of thumb: ≥30 per segment)

## Connection to Other Methods
- ITS is a special case of DiD with one unit and time as the comparison dimension
- Controlled ITS (CITS) adds a comparison group, bridging ITS and DiD
- When donor units exist, Synthetic Control provides a data-driven counterfactual instead of extrapolating the pre-trend
- Bayesian Structural Time Series (CausalImpact) extends ITS with probabilistic counterfactuals and covariates

## Real-World Challenges and Practical Realities

### Challenge 1: Co-Occurring Events (The Biggest Threat)
ITS assumes nothing else changed at the intervention point. In reality, things are always changing. At Uber, a marketing campaign might coincide with a competitor's outage, a holiday weekend, or a regulatory change. At Netflix, a price increase might coincide with a major content release. Disentangling these effects is nearly impossible with a single time series.

**What actually happens**: The team presents ITS results showing a revenue bump. A stakeholder says "wasn't that the same week our competitor went down for 2 days?" -- and the analysis becomes inconclusive. Teams learn to maintain a detailed "event log" of everything happening around the intervention, but it's never complete.

### Challenge 2: Functional Form Sensitivity
ITS extrapolates the pre-trend forward. If you model the pre-trend as linear but it was actually quadratic (or plateauing), the counterfactual is wrong. At Xbox, digital game sales might follow an S-curve that looks linear in a short window but saturates over longer periods.

**What actually happens**: The team fits a linear pre-trend and finds a level shift. A colleague re-runs with a quadratic pre-trend and the effect shrinks by 50%. Which model is "right"? This is a judgment call, and both are defensible.

### Challenge 3: Seasonality and Calendar Effects
Daily or weekly data has strong seasonality (weekends, holidays, pay cycles). If the intervention happens near a seasonal shift (e.g., a campaign launches right before Black Friday), the ITS estimate conflates the intervention effect with seasonality.

**What actually happens**: The team adds day-of-week and month fixed effects, which helps, but holidays and one-off events don't fit neatly into fixed-effect structures. Residual seasonality can still bias the estimate.

### Challenge 4: Autocorrelation Makes Standard Errors Wrong
Time series data is autocorrelated by definition -- today's revenue depends on yesterday's. Standard OLS errors dramatically understate uncertainty. Many published ITS analyses use naive standard errors and report spuriously significant results.

**What actually happens**: The team uses Newey-West (HAC) errors, which are wider but more honest. The effect that was "significant at p < 0.001" with OLS errors becomes "p = 0.08" with HAC errors. The PM is disappointed.

### Challenge 5: Short Pre-Period or Post-Period
ITS needs many observations on both sides. But business moves fast -- a PM wants results 2 weeks after a campaign launch. With 14 post-intervention days and perhaps strong day-to-day noise, there's very little power to detect anything other than huge effects.

**What actually happens**: The team says "we need 60+ days of post-data for a reliable estimate" and the PM says "the budget review is in 3 weeks." The team produces preliminary results with wide confidence intervals and everyone is frustrated.

---

## FAANG Interview Follow-Up Questions

### Q1: "Your ITS shows a level shift of +$15K/day. But your pre-treatment trend was already increasing by $500/day. How do you separate the trend from the intervention effect?"
**What they're testing**: Do you understand the segmented regression decomposition?
**Strong answer**: "The segmented regression separates these explicitly. The pre-treatment trend (beta_1) captures the existing $500/day growth. The level shift (beta_2 = $15K) captures the IMMEDIATE jump at the intervention, controlling for the pre-trend. The slope change (beta_3) captures any change in the GROWTH RATE after intervention. The counterfactual is the pre-trend extrapolated forward. The $15K is the gap between actual revenue and where the pre-trend would have taken us -- it's already adjusted for the existing trend."

### Q2: "A major competitor had an outage the same week as your campaign launched. How does this affect your analysis?"
**What they're testing**: Do you recognize the fundamental limitation of single-unit ITS?
**Strong answer**: "This is the biggest weakness of ITS -- co-occurring events cannot be disentangled. The level shift now captures BOTH our campaign AND the competitor outage. I'd try: (1) check if the competitor's outage was resolved quickly -- if so, the effect should decay while our campaign effect persists, (2) use a 'controlled ITS' if we have a comparable metric unaffected by our campaign to check if the competitor outage explains the bump, (3) look at the slope change -- our campaign should affect the slope (sustained growth) while a one-time outage shouldn't, (4) be transparent: 'The immediate level shift is confounded. The sustained slope change is more likely attributable to our campaign.' If I had a control group, I'd switch to DiD."

### Q3: "You're using Newey-West standard errors with 7 lags. Why 7? What happens if you use 14?"
**What they're testing**: Do you understand lag selection in HAC estimation?
**Strong answer**: "7 lags corresponds to one week -- reasonable for daily data since weekly seasonality creates autocorrelation up to 7 days. If I use 14, the standard errors get wider (more conservative) because I'm allowing for longer-range dependence. The standard guidance is ceil(0.75 * T^(1/3)) for automatic selection, but domain knowledge matters: if my data has monthly cycles, I might need 30 lags. I'd report results with multiple lag choices as a sensitivity check. If conclusions change dramatically with lag choice, the result is fragile."

### Q4: "Can you use ITS if the intervention was gradual (phased rollout over 4 weeks) rather than instant?"
**What they're testing**: Do you understand the sharp vs. gradual intervention distinction?
**Strong answer**: "A gradual intervention violates the 'clean break' assumption of standard ITS. Options: (1) define the intervention as the START of the rollout and accept that the estimated level shift captures only the initial impact, (2) model the rollout phase explicitly -- e.g., add a 'ramp-up' variable that goes from 0 to 1 over the 4-week rollout period, (3) use the full rollout completion as the intervention date and exclude the ramp-up period from both pre and post windows. The right choice depends on the business question: 'what was the effect of starting the campaign' vs. 'what was the effect once fully deployed.'"

### Q5: "Your pre-treatment period has 180 days but includes Black Friday and Christmas. How do you handle this?"
**What they're testing**: Can you deal with real-world messy time series?
**Strong answer**: "Holiday effects create outliers that distort the pre-trend estimation. I'd: (1) add holiday indicators as covariates in the regression, (2) check whether the intervention date is near a holiday (if so, the holiday effect confounds the intervention), (3) consider using a robust regression (iteratively reweighted least squares) that downweights outliers, (4) alternatively, model with ARIMA + intervention terms, which handles seasonal patterns more flexibly. The key is that any seasonal pattern in the pre-period that isn't modeled will show up as part of the counterfactual -- so holiday spikes in the pre-trend get extrapolated forward, potentially making the post-intervention period look artificially low."

### Q6: "The PM asks you to estimate the ROI of the marketing campaign using your ITS results. How do you go from 'level shift of +$15K/day' to ROI?"
**What they're testing**: Can you translate causal estimates into business metrics?
**Strong answer**: "Cumulative incremental revenue = (level shift x days) + (slope change x days^2 / 2) over the relevant period. If the campaign ran for 60 days post-launch: incremental revenue ≈ $15K x 60 + $200 x 60^2 / 2 = $1.26M. ROI = incremental revenue / campaign cost. But I'd add caveats: (1) the estimate has a confidence interval -- I'd report the CI on ROI too, (2) I'd check for effect decay (maybe the $15K/day declines over time -- the event study version of ITS would show this), (3) I'd distinguish between revenue shift (pulling forward future purchases) and true incremental revenue, (4) there may be long-run effects not captured in the 60-day window."
