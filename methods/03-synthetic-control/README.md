# Synthetic Control Method

## What It Is and When to Use It
Constructs a weighted combination of untreated units to create a "synthetic" counterfactual for the treated unit. Used when treatment occurs at an aggregate level (country, city, region) and there's only one (or very few) treated units.

**Use when**: Single treated unit at aggregate level, multiple donor units available, long pre-treatment period.
**Do NOT use when**: Many treated units (use DiD), user-level treatment (use PSM), no donor pool available (use ITS).

## Industry Use Cases

### Use Case 1: Airbnb — Experiences Launch in New Market
- **Business question**: Did launching "Experiences" in Austin causally increase total booking revenue?
- **Treated**: Austin. **Donors**: Other mid-size US cities without Experiences.
- **Why Synthetic Control**: Only one treated city, many potential donor cities, long booking history.
- **Alternatives**: DiD ruled out (only 1 treated unit). ITS ruled out (want to leverage donor cities for better counterfactual).

### Use Case 2: Xbox — Regional Price Change Impact
- **Business question**: What was the revenue impact of a 15% price increase in Canada?
- **Treated**: Canada. **Donors**: UK, Australia, Nordic countries.
- **Why SC**: Country-level intervention, only one treated country.
- **Alternatives**: DiD ruled out (single treated unit). A/B test impossible at country level.

### Use Case 3: Netflix — Content Library Expansion in a Country
- **Business question**: Did adding 200 local titles in Brazil increase subscriber growth?
- **Treated**: Brazil. **Donors**: Other LATAM countries.
- **Why SC**: Country-level policy, one treated country, rich donor pool.
- **Alternatives**: DiD (only 1 treated), PSM (aggregate level, not user-level).

### Use Case 4: Uber — Market Entry Effect on Taxi Industry
- **Business question**: Did Uber's entry into Portland causally reduce taxi ridership?
- **Treated**: Portland. **Donors**: Similar cities where Uber hasn't entered yet.
- **Why SC**: City-level event, one treated city, many comparison cities.
- **Alternatives**: DiD (only 1 treated), RDD (no threshold for market entry).

## Key Assumptions
- **Pre-treatment fit**: Synthetic control must closely track treated unit before intervention
- **No spillover**: Donor units unaffected by treatment
- **Convex hull**: Treated unit's outcomes must be within the range of donors

## Connection to Other Methods
- Augmented SC (ridge regression augmentation) for better pre-fit
- Can combine with DiD for "synthetic DiD" (Arkhangelsky et al.)

## Real-World Challenges and Practical Realities

### Challenge 1: Pre-Treatment Fit Is Often Poor
In practice, finding donor units that can be combined to match the treated unit's pre-treatment trajectory is surprisingly hard. At Airbnb, when measuring the effect of launching Experiences in Austin, no combination of other cities perfectly replicates Austin's unique mix of tech workers, college students, and tourists. The pre-treatment RMSPE might be "acceptable" but not great.

**What actually happens**: The team spends weeks trying different donor pools, predictor sets, and optimization specifications to get a tighter pre-fit. This feels like p-hacking -- if you try 20 specifications and present the one with the best fit, you've implicitly selected for overfitting. Best practice is to pre-register the specification.

### Challenge 2: Small Donor Pool
Synthetic control needs enough donor units to construct a credible counterfactual. At Xbox, when measuring the impact of a price change in Canada, the donor pool is limited to maybe 5-8 comparable countries. With so few donors, the method has low power and placebo-based inference is crude (p-value can't be smaller than 1/N_donors).

**What actually happens**: With 8 donors, the smallest p-value from a permutation test is 1/9 ≈ 0.11 -- not significant at the 5% level regardless of the effect size. Teams resort to "the effect is directionally positive and the largest among all placebos" which is not a rigorous statistical statement.

### Challenge 3: Spillover Between Units
If the treatment in one unit affects donor units, the synthetic control is biased. At Uber, if launching in Portland changes rider/driver behavior in nearby Seattle (a donor), the counterfactual is contaminated. In gaming, if a price change in Canada affects behavior in the US (many shared online communities), the donor pool is compromised.

**What actually happens**: The team argues qualitatively that spillover is "unlikely to be large" but cannot test this directly. Excluding geographically proximate donors reduces the pool further.

### Challenge 4: Post-Treatment Divergence Interpretation
A gap between actual and synthetic post-treatment could be causal, OR it could mean the synthetic control's weights no longer work because the relationship between donors changed. At Netflix, macroeconomic shocks (exchange rates, competition entry) might affect Brazil and its donors differently, creating a gap that has nothing to do with the content library expansion.

**What actually happens**: The team shows the gap and a critic says "how do you know this isn't just Brazil's economy diverging from the donors?" -- and there's no clean answer. Co-occurring events are the biggest threat to ITS and synthetic control.

### Challenge 5: Stakeholder Explanation Difficulty
"We created a fake version of Austin by combining 35% of Denver, 25% of Portland, and 40% of Nashville" is a genuinely weird sentence to explain to a VP. The method is elegant but unintuitive to non-technical audiences.

**What actually happens**: The data scientist shows the pre-fit plot (which looks impressive) and the post-gap plot (which tells the story). But when asked "why those weights?" or "why not just compare to Denver directly?", the explanation requires optimization theory that loses the audience.

---

## FAANG Interview Follow-Up Questions

### Q1: "Your synthetic control has pre-treatment RMSPE of 15% of the outcome mean. Is this acceptable?"
**What they're testing**: Do you have practical intuition about fit quality?
**Strong answer**: "15% is on the high side. I'd want RMSPE below 5-10% of the outcome mean for credible inference. With 15%, the post-treatment gap needs to be very large to be distinguishable from pre-treatment noise. I'd try: (1) expanding the donor pool, (2) using different predictor sets, (3) augmented synthetic control (SDID or ridge-augmented SC), (4) if fit can't improve, I'd be transparent that the results are suggestive but not conclusive, and recommend investing in a proper experiment next time."

### Q2: "You assigned weight 0.65 to one donor country and near-zero to the rest. What does this mean?"
**What they're testing**: Do you understand when SC degenerates to a case-comparison?
**Strong answer**: "This means the treated unit is essentially being compared to one donor -- it's a single-unit comparison, not a true 'synthetic' blend. This is a red flag because: (1) any idiosyncratic shock to that one donor will bias the estimate, (2) the method loses its key advantage of constructing a more stable counterfactual by blending multiple donors. I'd investigate why: maybe the treated unit is very different from most donors and only one is a reasonable match. If so, DiD with that single donor might be more transparent. I might also try constrained optimization with an entropy penalty to encourage more spread across donors."

### Q3: "Can you use synthetic control with user-level data instead of aggregate-level data?"
**What they're testing**: Do you understand the method's scope and limitations?
**Strong answer**: "Traditional SC is designed for a small number of aggregate units (regions, countries, stores). At user level, you'd have millions of potential donors and one 'treated' user -- which is basically matching/PSM. The distinction is that SC optimizes for pre-treatment TIME SERIES fit (tracking the trajectory), while PSM matches on pre-treatment FEATURES (snapshots). For user-level treatment effects with time series data, I'd use PSM + DiD (matched DiD) rather than SC. That said, recent work on 'micro-synthetic control' and 'synthetic DiD' (Arkhangelsky et al.) bridges this gap."

### Q4: "Your placebo test shows that 2 out of 8 donor countries have larger gaps than the treated country. What do you conclude?"
**What they're testing**: Can you interpret permutation-based inference correctly?
**Strong answer**: "The p-value is 3/9 ≈ 0.33 -- far from significant. I'd conclude that we cannot distinguish the treated unit's gap from random variation among donors. This DOESN'T mean there's no effect -- it means we don't have enough power to detect it. With only 8 donors, we need the effect to be the single largest gap (p = 1/9 ≈ 0.11) to even approach significance, and even that doesn't reach 0.05. I'd report this honestly: 'The point estimate suggests a positive effect of X%, but we cannot rule out chance given the small number of comparison units. A longer post-period or more donors might improve power.'"

### Q5: "The VP asks: 'We're launching this feature in Brazil next quarter. Can you use synthetic control to predict how much engagement will increase?' How do you respond?"
**What they're testing**: Do you understand that SC is retrospective, not predictive?
**Strong answer**: "Synthetic control is a backward-looking causal method, not a forecasting tool. It tells us what DID happen compared to a counterfactual, not what WILL happen. For prediction, I'd use: (1) results from SC analyses of similar past launches in other countries as a range estimate, (2) a proper forecasting model (time series, ML), or (3) combine both: 'Based on our SC analysis of the Austin launch, we saw a 15% lift. Brazil is somewhat similar in market maturity, so 10-20% is a reasonable planning range, but there's substantial uncertainty.' I'd also advocate for designing the Brazil launch as an experiment (e.g., staggered rollout across Brazilian states) so we can measure the effect cleanly."

### Q6: "A colleague says 'just compare Brazil to the average of all LATAM countries.' Why is synthetic control better?"
**What they're testing**: Do you understand the value of data-driven weighting?
**Strong answer**: "The simple average gives equal weight to all donors, but Brazil might be much more similar to Colombia and Mexico than to smaller markets like Paraguay or Bolivia. SC finds the OPTIMAL weights to replicate Brazil's specific trajectory. This matters because: (1) it reduces bias from dissimilar donors, (2) the weights are transparent (you can inspect them), (3) the pre-treatment fit validates the counterfactual (if the fit is good, we trust the post-treatment projection). An equal-weight average might have terrible pre-treatment fit, meaning the comparison is invalid from the start."


