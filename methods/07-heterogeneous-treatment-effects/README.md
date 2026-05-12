# Heterogeneous Treatment Effects (HTE)

## What It Is and When to Use It

HTE methods estimate how treatment effects **vary across subgroups**. Instead of one ATE, estimate Conditional Average Treatment Effects:

$$CATE(x) = E[Y(1) - Y(0) \mid X = x]$$

**Use when:**
- You have a treatment effect estimate (from A/B test, PSM, DiD) but suspect it varies across segments
- You want to personalize or target interventions
- You need to identify who benefits most (and who might be harmed)

**Do NOT use when:**
- You don't have a credible treatment effect in the first place — get ATE right first
- Your sample is too small for subgroup analysis (HTE is data-hungry)
- You're fishing for significant subgroups without pre-registration (p-hacking risk)

---

## Industry Use Cases

### Use Case 1: Netflix — Personalized Content Recommendations

| Component | Detail |
|---|---|
| **Business question** | Which user segments benefit most from the new recommendation algorithm? |
| **Treatment** | New algorithm vs old |
| **Outcome** | Watch time (hours/week) |
| **HTE dimension** | User tenure, genre preference, viewing frequency |
| **Why HTE** | ATE masks that new users benefit significantly more than veterans — who may actually be *hurt* by disrupted habits. Guides rollout prioritization. |
| **Alternatives ruled out** | Simple subgroup analysis (risk of p-hacking, misses interactions). Just ATE (misses actionable heterogeneity). |

### Use Case 2: Uber — Surge Pricing Sensitivity by Rider Type

| Component | Detail |
|---|---|
| **Treatment** | Surge multiplier level |
| **Outcome** | Ride completion rate |
| **HTE dimension** | Business vs leisure riders, peak vs off-peak, loyalty tier |
| **Why HTE** | Price sensitivity varies dramatically across rider types. Business travelers are inelastic; casual riders churn at 1.5x. Informs dynamic pricing strategy. |

### Use Case 3: Xbox — Game Pass Trial Offer Effectiveness

| Component | Detail |
|---|---|
| **Treatment** | Free trial offer vs no offer |
| **Outcome** | Conversion to paid subscription |
| **HTE dimension** | Gaming history, genre preference, platform (PC vs console) |
| **Why HTE** | Some users would subscribe anyway ("sure things"), others are "persuadable." Targeting persuadables saves costs. Classic uplift modeling framing. |

### Use Case 4: Airbnb — Search Ranking Algorithm Effect

| Component | Detail |
|---|---|
| **Treatment** | New search ranking algorithm |
| **Outcome** | Booking conversion rate |
| **HTE dimension** | Property type, location, price range, host experience level |
| **Why HTE** | Algorithm helps budget listings more than luxury ones. Understanding heterogeneity guides algorithm tuning and host communications. |

---

## Methods

### Causal Forests
- Extension of random forests that directly optimizes for treatment effect heterogeneity
- Splits on covariates that maximize variation in CATE
- Best for *discovering* heterogeneity when you don't know where to look
- Implementation: `econml.dml.CausalForestDML`, `grf` (R)

### Meta-Learners

| Learner | Approach | Strengths | Weaknesses |
|---|---|---|---|
| **T-learner** | Separate models for treated/control, CATE = μ₁(x) - μ₀(x) | Simple, flexible | Doesn't share information across arms; high variance |
| **S-learner** | Single model with treatment as feature | Shares information | May miss heterogeneity if effect is small relative to outcome variance |
| **X-learner** | Two-stage: impute counterfactuals, then model difference | Works well with unbalanced treatment | More complex to implement |
| **R-learner** | Residual-on-residual regression | Robust to confounding | Requires good nuisance parameter estimates |

### BART (Bayesian Additive Regression Trees)
- Bayesian nonparametric approach with natural uncertainty quantification
- Posterior intervals on CATE without bootstrap
- Implementation: `bartpy`, `dbarts` (R)

---

## Key Assumptions

1. **Unconfoundedness** (inherited from the identification strategy): Treatment assignment is independent of potential outcomes conditional on X
2. **Overlap/positivity**: All subgroups have both treated and control units — if a segment is 100% treated, you can't estimate CATE there
3. **Sufficient sample size per subgroup**: HTE estimation needs enough data in each region of X-space
4. **SUTVA**: No interference between units

---

## Connection to Uplift Modeling

HTE estimation and uplift modeling are **the same problem** viewed from different traditions:
- **HTE** (causal inference / econometrics): Focuses on estimating CATE with valid statistical properties
- **Uplift modeling** (marketing / ML): Focuses on *ranking* individuals by treatment benefit for targeting

The four quadrants of uplift:
- **Persuadables**: Positive CATE — target these
- **Sure things**: Good outcome regardless — don't waste treatment
- **Lost causes**: Bad outcome regardless — don't waste treatment
- **Sleeping dogs**: Negative CATE — treatment *hurts* — definitely avoid

Both use the same methods (T-learner, causal forests, etc.) but differ in evaluation metrics: uplift modeling uses uplift curves and AUUC; HTE focuses on MSE of CATE estimates.

---

## Real-World Challenges and Practical Realities

### Challenge 1: Overfitting to Noise
Causal forests and meta-learners are flexible ML models applied to treatment effect estimation. They can overfit, finding "heterogeneity" that is actually noise. At Netflix, a causal forest might identify that users born on Tuesdays benefit more from the new algorithm -- this is obviously spurious, but subtler versions of this problem are common.

**What actually happens**: The team finds "users in the 25-34 age group benefit 3x more than others." Is this real heterogeneity or a statistical artifact? Without a holdout validation (which requires a separate experiment), it's hard to tell. Many HTE findings fail to replicate.

### Challenge 2: The "Multiple Comparisons" Problem
Testing for heterogeneity across many subgroups is a form of multiple hypothesis testing. With 20 user segments, there's a high chance of finding at least one that looks significantly different, even if the true effect is homogeneous. Standard corrections (Bonferroni, FDR) are conservative and may kill real findings.

**What actually happens**: The team finds "significant" heterogeneity in 3 of 15 segments. After Bonferroni correction, none are significant. The PM says "but 3 out of 15 is clearly not random!" -- and the statistical debate begins.

### Challenge 3: CATE Estimates Are Noisy
Individual-level treatment effects are inherently noisy because we never observe both potential outcomes. Even with 100K users, the CATE for a specific subgroup of 500 users might have huge variance. At Uber, estimating the treatment effect of surge pricing for "business travelers during evening rush hour" requires slicing the data so thinly that precision evaporates.

**What actually happens**: The CATE estimates are noisy enough that the optimal targeting policy (based on CATE) barely outperforms random assignment. The team shows a 3% improvement in targeting efficiency, and the PM questions whether the complexity of the HTE model is worth it.

### Challenge 4: Operationalization Gap
Even when HTE is estimated cleanly, translating CATE estimates into production targeting systems is hard. The model needs to score users in real-time, the features used in the CATE model need to be available at decision time, and the targeting policy needs to be integrated with the CRM or product system.

**What actually happens**: The data scientist builds a beautiful causal forest on historical data. The engineering team says "we can't compute 'genre diversity score' in real-time" and "our targeting system only accepts binary segments, not continuous CATE scores." The model has to be simplified, losing much of its value.

### Challenge 5: External Validity
HTE estimated from one experiment may not transfer to another context. At Netflix, if the heterogeneity was estimated from a US experiment, it may not apply to the Japan launch. User segments that are "persuadable" in one context might not be in another.

**What actually happens**: The team uses HTE from Q1 experiment to target Q3 campaign. The Q3 results show no benefit from targeting, because user behavior shifted between quarters (new content, seasonal changes, competitive dynamics).

---

## FAANG Interview Follow-Up Questions

### Q1: "You found that new users (< 6 months) benefit most from the recommendation algorithm. But your experiment had 10x more veteran users than new users. How confident are you in the new-user CATE?"
**What they're testing**: Do you understand statistical power for subgroup effects?
**Strong answer**: "Less confident. The new-user subgroup has 1/10th the sample, so the CATE estimate has roughly 3x the standard error. I'd check: (1) is the CATE for new users significantly different from the overall ATE (test for heterogeneity, not just significance within the subgroup)? (2) the confidence interval for new-user CATE -- if it's very wide, the finding is suggestive but not conclusive, (3) I'd recommend a follow-up experiment enriched with new users (oversample new users) to confirm this specific finding before building a targeting strategy around it."

### Q2: "How would you validate that your CATE model actually improves business outcomes compared to treating everyone the same?"
**What they're testing**: Do you know how to operationalize and validate HTE?
**Strong answer**: "Run a three-arm experiment: (1) treat everyone (blanket rollout), (2) treat no one (control), (3) treat only the model-recommended users (targeted rollout). Compare total outcome across all three arms. If arm 3 achieves similar total outcomes to arm 1 but with fewer users treated, the targeting model adds value. An alternative is 'policy evaluation' using inverse propensity weighting on historical experimental data, but a prospective validation is gold standard."

### Q3: "Your causal forest says feature X drives heterogeneity. But feature X is correlated with features Y and Z. How do you know X is the true moderator?"
**What they're testing**: Can you distinguish association from moderation?
**Strong answer**: "Causal forests identify which features best PREDICT treatment effect variation, not which causally MODERATE the effect. Feature X might be a proxy for the true moderator Y. To disentangle: (1) check partial dependence plots for each feature while controlling for others, (2) look at the causal forest's feature importance alongside domain knowledge, (3) if possible, design an experiment that varies X directly (e.g., if X is 'tenure', compare the effect at 3 months vs 12 months within the same experiment), (4) use the X-learner, which handles this more carefully than the T-learner."

### Q4: "The PM wants to know: should we show the new algorithm to users where CATE > 0 and hide it from users where CATE < 0? What's wrong with this approach?"
**What they're testing**: Do you understand the decision framework beyond just CATE sign?
**Strong answer**: "Three issues: (1) The CATE estimates have uncertainty. Users with CATE = -0.1 might actually have CATE = +0.5 -- we'd be withholding a beneficial treatment due to estimation noise. I'd use a confidence interval threshold (e.g., treat unless the UPPER bound of the CI is below some threshold). (2) There might be long-run effects not captured in the short-run CATE. Users who dislike the new algorithm initially might adapt. (3) There are ethical and UX concerns about showing different products to different users. I'd recommend treating users where CATE is clearly negative as a separate investigation -- WHY does the algorithm hurt them? Fix the algorithm for these users rather than just hiding it."

### Q5: "What's the difference between a T-learner and an X-learner? When would you use each?"
**What they're testing**: Technical depth on meta-learner methods.
**Strong answer**: "T-learner trains separate outcome models for treated and control, then CATE = mu_1(x) - mu_0(x). It's simple but doesn't share information between arms and can be noisy when groups are imbalanced. X-learner improves this by: (1) training the two models, (2) using each model's predictions as pseudo-outcomes for the OTHER group to directly estimate individual treatment effects, (3) combining using a propensity-score-weighted average. X-learner is better when one group is much larger (e.g., 90% control, 10% treated) because it leverages the large group's information. I'd use T-learner for balanced experiments and X-learner for imbalanced ones or observational data."

### Q6: "We ran an A/B test and the overall ATE is zero. But you're claiming there are heterogeneous effects. Isn't that just noise?"
**What they're testing**: Do you understand that zero ATE can mask heterogeneity?
**Strong answer**: "Not necessarily noise. A zero ATE can mean the treatment helps some users and hurts others in equal measure -- the average washes out. I'd check: (1) is the variance of the CATE estimates significantly larger than what we'd expect under a constant zero effect? (Best Linearization test), (2) do the estimated CATEs predict outcomes in a holdout sample? If yes, the heterogeneity is real. (3) is there a clear monotonic pattern (e.g., CATE increases with tenure) or is it random? Domain-consistent patterns are more credible. If there truly are winners and losers canceling out, this is a VERY important finding -- it means we should target the treatment, not abandon it."
