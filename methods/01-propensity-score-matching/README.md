# Propensity Score Matching (PSM)

## What It Is and When to Use It

Propensity Score Matching reduces selection bias in observational studies by matching treated and untreated units on their probability of receiving treatment. It collapses high-dimensional covariates into a single score: e(X) = P(Treatment=1 | X).

**Use when**: You have observational (non-experimental) data, you can measure the key confounders, you need to estimate a treatment effect, and there is no clean time-based design available.

**Do NOT use when**: You have unmeasured confounders (use IV instead), you have a sharp cutoff for treatment assignment (use RDD), or you have panel data with a clear intervention point (consider DiD first).

## Industry Use Cases

### Use Case 1: Xbox -- Game Pass Subscription Impact on Revenue
- **Business question**: Does subscribing to Game Pass causally increase a user's total revenue, or do high-spenders self-select?
- **Treatment**: User subscribes to Game Pass
- **Outcome**: Total revenue over next 6 months
- **Covariates**: Pre-subscription hours played, titles owned, purchase history, demographics, platform tenure
- **Why PSM**: No clean intervention date (users subscribe at different times), no randomization. We have rich pre-treatment behavioral data to construct propensity scores.
- **Alternatives considered**:
  - DiD: Ruled out because there is no single "treatment date" -- users subscribe continuously. Staggered DiD is possible but PSM is simpler and more direct for user-level effects.
  - RDD: Ruled out because there is no threshold-based assignment. Subscription is a voluntary choice.
  - A/B test: Ideal but infeasible -- cannot randomly force users to subscribe.

### Use Case 2: Airbnb -- Impact of "Experiences" Feature on Host Revenue
- **Business question**: Does a host listing an Experience (tours, activities) causally increase their accommodation booking revenue?
- **Treatment**: Host lists at least one Experience
- **Outcome**: Accommodation revenue over next 3 months
- **Covariates**: Pre-period booking count, average nightly rate, listing quality score, response rate, location, host tenure
- **Why PSM**: Hosts self-select into offering Experiences. We need to compare hosts who offer Experiences to similar hosts who don't.
- **Alternatives considered**:
  - DiD: Could work if we had a clear launch date, but Experiences rolled out gradually and hosts adopted at different times.
  - IV: Would need a valid instrument. Proximity to tourist attractions could work but is hard to measure precisely.

### Use Case 3: Netflix -- Impact of Downloading Content on Retention
- **Business question**: Does a user downloading content for offline viewing causally improve retention, or are already-loyal users more likely to download?
- **Treatment**: User downloads at least 3 titles for offline viewing
- **Outcome**: 90-day retention (binary)
- **Covariates**: Pre-download watch hours, genre diversity, device type, account sharing behavior, subscription tier, account age
- **Why PSM**: No randomization possible (can't force downloads). Rich behavioral data makes PSM feasible.
- **Alternatives considered**:
  - HTE: Can be layered on top of PSM to understand heterogeneous effects, but PSM is the first step.
  - A/B test: Could test prompts to download but cannot force the behavior itself.

### Use Case 4: Uber -- Impact of UberPro Enrollment on Driver Retention
- **Business question**: Does enrolling in UberPro (driver rewards program) causally reduce driver churn?
- **Treatment**: Driver enrolls in UberPro
- **Outcome**: 6-month driver retention
- **Covariates**: Pre-enrollment trips completed, acceptance rate, driver rating, cancellation rate, hours online, market, vehicle type
- **Why PSM**: Drivers self-select into UberPro. We need to match enrolled drivers to similar non-enrolled drivers.
- **Alternatives considered**:
  - RDD: UberPro has tier thresholds, but enrollment itself is voluntary, so RDD doesn't apply to the enrollment decision.
  - DiD: Possible if we define enrollment date as treatment, but PSM more directly addresses the selection problem.

## Key Assumptions

1. **Unconfoundedness (No unmeasured confounders)**: All variables that jointly affect treatment and outcome are observed and included. This is the STRONGEST and most untestable assumption.
2. **Common support (Overlap)**: For every treated unit, there exists a comparable control unit with a similar propensity score.
3. **SUTVA (Stable Unit Treatment Value)**: One user's treatment doesn't affect another's outcome.

### How to Check
- Overlap: Plot propensity score distributions for treated vs control. Trim non-overlapping regions.
- Balance: After matching, check standardized mean differences (SMD < 0.1) for all covariates.
- Calibration: Verify the propensity model produces well-calibrated probabilities (calibration plot, Brier score).
- Sensitivity: Rosenbaum bounds to assess how strong unmeasured confounding would need to be to overturn results.

## Connection to Other Methods

- **Combine with DiD**: Match first (PSM), then apply DiD on the matched sample. This handles both selection-on-observables and time-invariant unobservables.
- **Extends to IPW**: Instead of matching, reweight the sample using inverse propensity weights. Often more statistically efficient.
- **Feeds into HTE**: Once you have a matched sample, you can estimate heterogeneous treatment effects across subgroups.

## Notebook

See [01-psm-xbox-subscription-revenue.ipynb](01-psm-xbox-subscription-revenue.ipynb) for a complete walkthrough with simulated data.

## Real-World Challenges and Practical Realities

### Challenge 1: The Unobserved Confounder Problem (The #1 Killer)
In practice, the unconfoundedness assumption almost never holds perfectly. At Xbox, when matching Game Pass subscribers to non-subscribers, there's always an unmeasured variable like "gaming enthusiasm" or "intent to spend" that isn't fully captured by hours played or titles owned. Teams at Microsoft Research have published extensively on this -- even with 50+ covariates, sensitivity analyses often show that a moderately strong unmeasured confounder could flip the sign of the estimate.

**What actually happens**: Product teams present PSM results to leadership, and a savvy director asks "but what about users who were going to spend more anyway?" The data scientist has to explain Rosenbaum bounds and why the result is "robust to moderate confounding" -- a nuanced argument that often doesn't land well in a 30-minute decision meeting.

### Challenge 2: Data Quality and Feature Engineering
Real user behavioral data is messy. At Netflix, watch hours might include autoplay background viewing. At Uber, "trips completed" might count cancelled-then-rebooked rides differently across regions. Feature definitions that seem clean in a notebook become ambiguous in production tables.

**What actually happens**: The data scientist spends 60-70% of the project time on data cleaning and feature definition, not on the matching itself. Different feature definitions can change the ATT by 30-50%.

### Challenge 3: The Sample Size vs. Match Quality Trade-off
With strict calipers, you get excellent balance but lose half your sample. With loose calipers, you keep more data but matches are poor. At Airbnb, when matching hosts who offer Experiences to those who don't, strict matching on location + listing quality + tenure might leave only 2,000 of 15,000 treated hosts matched.

**What actually happens**: The team presents results and someone asks "but this only applies to 13% of our hosts -- can we generalize?" The answer is usually "no, not confidently" -- and the project scope shrinks.

### Challenge 4: Temporal Leakage
When the treatment timing varies by user (e.g., subscription date), features computed from the "pre-period" might inadvertently include post-treatment data for some users, or the pre-period length might differ. This is a surprisingly common bug in real PSM implementations.

**What actually happens**: An engineer reviews the pipeline 3 months after launch and discovers that the "pre-period" window was incorrectly aligned, invalidating the original results. The team has to re-run and re-present.

### Challenge 5: Stakeholder Understanding
PSM is conceptually harder to explain than A/B testing. "We found similar users and compared them" sounds reasonable, but when pressed on WHY similar users are valid counterfactuals, most non-technical stakeholders struggle with the logic.

**What actually happens**: The product manager asks "why can't we just run an A/B test?" -- and the honest answer is often "we should have, but we didn't, so now we're using the best available method for observational data."

---

## FAANG Interview Follow-Up Questions

These are the types of follow-up questions an interviewer at a FAANG company would ask after you describe a PSM approach. They test depth of understanding, practical judgment, and awareness of limitations.

### Q1: "You matched on propensity scores and found a positive treatment effect. How do you know there isn't an unmeasured confounder driving both treatment and outcome?"
**What they're testing**: Do you understand the fundamental limitation of PSM?
**Strong answer**: "I can't prove there isn't one -- that's the core limitation. But I can quantify how strong an unmeasured confounder would need to be to nullify the result using Rosenbaum bounds or the E-value. If the result is only overturned by a confounder with a risk ratio > 3, and no known variable in our domain has that kind of effect, we have reasonable confidence. I'd also check if adding additional covariates changes the estimate -- if it's stable as we add more controls, that's reassuring."

### Q2: "Your propensity model has 0.92 AUC. Is that good or bad for matching?"
**What they're testing**: Do you understand the paradox of prediction accuracy in PSM?
**Strong answer**: "High AUC is actually concerning for PSM. It means the model can almost perfectly separate treated from control, which implies POOR overlap in propensity scores. If the model perfectly predicts treatment, there are no comparable control units for treated units. I'd rather have moderate AUC (0.6-0.8) with good overlap. The key metric isn't AUC -- it's whether the propensity score distributions overlap and whether post-matching balance is achieved."

### Q3: "You dropped 40% of your treated sample due to poor matches. How does this affect your conclusions?"
**What they're testing**: Do you understand external validity vs. internal validity?
**Strong answer**: "Dropping unmatched units improves internal validity (the estimate for retained units is less biased) but hurts external validity (results may not generalize to the dropped population). The dropped users are those with extreme propensity scores -- either very likely or very unlikely to be treated. I'd characterize WHO was dropped (e.g., heavy gamers with no match) and caveat that the ATT applies to the matched subpopulation, not all treated users. If stakeholders need the full-population effect, I might switch to IPW with trimmed weights."

### Q4: "You mentioned using logistic regression for the propensity model. Why not gradient boosting or a neural network?"
**What they're testing**: Do you understand the role of the propensity model?
**Strong answer**: "The goal isn't prediction accuracy -- it's covariate balance. Logistic regression is naturally well-calibrated, interpretable, and less prone to overfitting the treatment assignment. GBM or neural nets might overfit and produce extreme scores that hurt overlap. That said, if logistic regression fails to achieve balance on key covariates, I might try GBM with careful calibration (e.g., isotonic regression or Platt scaling). The test is always: does the matching produce good balance? The model is a means, not an end."

### Q5: "If you could go back in time, would you have designed this as an experiment instead? What would that experiment look like?"
**What they're testing**: Do you default to experiments when possible and understand PSM's role as a second-best?
**Strong answer**: "Absolutely. The gold standard would be an encouragement design -- randomly vary the prominence of Game Pass in the UI (some users see a banner, others don't) and use assignment as an instrument for subscription. This avoids the unconfoundedness assumption entirely. PSM is what we use when we didn't plan the experiment in advance or when randomization is impossible (e.g., can't force subscriptions). Going forward, I'd advocate for baking experiment infrastructure into product launches."

### Q6: "Walk me through exactly how you'd present this analysis to a VP who has never heard of propensity score matching."
**What they're testing**: Can you communicate technical results to non-technical stakeholders?
**Strong answer**: "I'd say: 'We wanted to know if Game Pass increases spending. We can't just compare subscribers to non-subscribers because subscribers are already more engaged. So we used a technique that finds, for each subscriber, a non-subscriber who looks identical on every measurable dimension -- same play hours, same number of games, same demographics. Then we compared spending between these matched pairs. The result: Game Pass subscribers spend $12 more per month than their matched counterparts, and this effect is statistically significant. The main caveat: if there's something we can't measure that makes subscribers different, this estimate could be off.' I'd show one visual: the Love plot showing balance before and after matching."
