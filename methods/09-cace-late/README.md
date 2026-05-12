# Complier Average Causal Effect (CACE / LATE)

## What It Is and When to Use It

CACE (also called Local Average Treatment Effect, LATE) estimates the causal effect specifically among **compliers** — people who take treatment when assigned to treatment and don't take it when assigned to control. It is the go-to method when experiments have non-compliance.

**Use when**: You ran an experiment but compliance is imperfect — some people assigned to treatment didn't take it, and some people in control found a way to get it anyway.

**Do NOT use when**:
- **Perfect compliance** — just estimate the ATE directly
- **No randomization** — you need observational causal methods instead
- **Very low compliance rate** — weak instrument problem makes estimates noisy and unreliable

### The Four Subpopulations

In any experiment with non-compliance, every participant falls into one of four latent groups:

| Subpopulation | Assigned Treatment | Assigned Control | Description |
|---|---|---|---|
| **Compliers** | Take treatment | Don't take treatment | Behavior is *affected* by assignment |
| **Always-takers** | Take treatment | Take treatment | Always find a way to get treatment |
| **Never-takers** | Don't take treatment | Don't take treatment | Never take treatment regardless |
| **Defiers** | Don't take treatment | Take treatment | Do the opposite of assignment |

Defiers are assumed away via the **monotonicity** assumption — no one does the opposite of what they're told.

---

## Industry Use Cases

### Use Case 1: Xbox — Game Pass Free Trial Offer

- **Instrument**: Random offer of a free Game Pass trial
- **Treatment**: Actually activating the trial
- **Outcome**: 12-month spending on the Xbox platform
- **Setup**: 60% take-up in the offered group, 10% in control (always-takers who find and activate trials on their own)
- **Why CACE**: The ITT (comparing offered vs. not offered) underestimates the effect because many offered users never activate. Per-protocol analysis (comparing activators vs. non-activators) is biased upward because activators include always-takers who have higher baseline spending. CACE isolates the effect for compliers — people whose activation behavior was actually changed by the offer.

### Use Case 2: Uber — Driver Training Program

- **Instrument**: Random invitation to an in-app training module
- **Treatment**: Actually completing the training
- **Outcome**: Average rider satisfaction score over next 90 days
- **Why CACE**: Many invited drivers never attend. Comparing attenders to non-attenders confounds the motivation to self-improve with the actual training effect. CACE separates the two by using random invitation as an instrument.

### Use Case 3: Netflix — Content Warning Impact

- **Instrument**: Random assignment to see content warnings before mature titles
- **Treatment**: Actually reading/processing the warnings (measured via dwell time on warning screen)
- **Outcome**: Completion rate of mature content
- **Why CACE**: Some users click through warnings instantly without reading (never-takers from a behavioral perspective). CACE estimates the effect for users who actually engage with warnings when shown, rather than diluting across everyone.

### Use Case 4: Airbnb — Host Education Program

- **Instrument**: Random invitation to a listing-optimization webinar
- **Treatment**: Actually attending the webinar
- **Outcome**: Listing quality score improvement over 60 days
- **Why CACE**: Attendance is voluntary — many invited hosts don't show up. CACE gives the treatment effect for hosts who would attend when invited, which is the policy-relevant quantity for deciding whether to scale the program.

---

## Key Assumptions

1. **Monotonicity (no defiers)**: Assignment can only encourage treatment, never discourage it. No one does the opposite of their assignment.
2. **Exclusion restriction**: Assignment affects the outcome *only* through its effect on treatment uptake. The offer letter itself doesn't change spending — only activating Game Pass does.
3. **Relevance (first stage)**: Assignment must actually affect treatment uptake. If nobody responds to the offer, there's no instrument. Formally: P(T=1|Z=1) ≠ P(T=1|Z=0).

---

## Relationship to Instrumental Variables

CACE is mathematically identical to an IV estimate where the randomized assignment serves as the instrument for actual treatment:

```
CACE = ITT / Compliance Rate
     = [E(Y|Z=1) - E(Y|Z=0)] / [P(T=1|Z=1) - P(T=1|Z=0)]
```

This is the **Wald estimator** — the reduced-form effect divided by the first-stage effect. In the IV framework, Z is the instrument, T is the endogenous treatment, and Y is the outcome.

---

## ITT vs. CACE vs. Per-Protocol

| Estimate | What it measures | Bias? | When to use |
|---|---|---|---|
| **ITT** (Intent-to-Treat) | Effect of *assignment* on outcome, averaged over everyone | Unbiased for assignment effect, but diluted | Policy decisions about offering/assigning |
| **CACE / LATE** | Effect of *treatment* on outcome, for compliers only | Unbiased under assumptions | Understanding the treatment effect for those who respond |
| **Per-Protocol** | Effect among those who happened to comply | Biased by self-selection | Almost never — it conflates compliance with treatment |

**Rule of thumb**: Report ITT as the primary result (it answers "should we offer this?"). Report CACE as a secondary result (it answers "what's the effect for people who actually take it?"). Avoid per-protocol unless you can convincingly argue selection isn't a problem.

---

## Real-World Challenges and Practical Realities

### Challenge 1: Compliance Is Often Very Low
In many real experiments, compliance rates are dismal. At Xbox, only 30% of users offered a free Game Pass trial actually activate it. At Netflix, only 15% of users shown a content recommendation actually watch it. Low compliance means the CACE is estimated from a tiny effective sample, leading to huge variance.

**What actually happens**: The team runs a large experiment (100K users), but with 15% compliance, the effective sample for CACE estimation is ~15K compliers. The CACE estimate has wide confidence intervals, and the PM asks "so the effect could be anywhere from -$5 to +$30?" The team says yes, and the project feels like a waste.

### Challenge 2: Who Are the Compliers? (The Latent Subpopulation Problem)
Compliers are defined as people who would take treatment when offered and not take it when not offered. But we never observe this -- we can't identify individual compliers. We can characterize them statistically (e.g., compliers tend to be younger, more engaged) but we can't point to specific people.

**What actually happens**: The PM asks "which users are the compliers?" expecting a list of user IDs. The data scientist explains that compliers are a statistical concept, not an identifiable group. The PM is confused: "So this effect applies to a group we can't even find?" This limits the actionability of CACE.

### Challenge 3: The Monotonicity Assumption
CACE requires monotonicity: no "defiers" (people who do the opposite of their assignment). In most settings this is reasonable, but in some it fails. At Uber, if offering a promo to some drivers discourages them (they feel cheapened or surveilled), they're defiers. If defiers exist, the Wald estimator is biased.

**What actually happens**: The team assumes monotonicity without much scrutiny. Later, someone points out a plausible defier mechanism, and the entire analysis is questioned. There's no way to test for defiers -- it's an article of faith.

### Challenge 4: ITT vs CACE Policy Relevance
The PM often just needs the ITT (what happens if we send the offer?) rather than the CACE (what happens if someone actually uses the offer?). ITT is directly actionable because the company controls the OFFER, not the UPTAKE. CACE is more theoretically interesting but less directly actionable.

**What actually happens**: The data scientist presents CACE and the PM asks "so if I send this offer to 100K users, how many more subscriptions do I get?" This is an ITT question, not a CACE question. The CACE is useful for understanding the mechanism (does Game Pass itself drive revenue, or is it just the offer?), but the operational decision depends on ITT.

### Challenge 5: Always-Takers Muddy the Waters
If 20% of the control group finds a way to get the treatment (always-takers), the ITT is diluted and the first-stage compliance rate is lower, making CACE noisier. At Xbox, always-takers might be users who subscribe through a family member's account or a third-party deal.

**What actually happens**: The team discovers that 12% of the control group activated Game Pass through a partner promotion they didn't know about. This contamination reduces the first-stage compliance rate and inflates CACE variance. The team has to decide whether to exclude these users (introducing selection bias) or keep them (accepting the noise).

---

## FAANG Interview Follow-Up Questions

### Q1: "Your experiment has 60% take-up in treatment and 10% in control. What's the compliance rate, and what does it mean?"
**What they're testing**: Can you decompose the compliance structure?
**Strong answer**: "Compliance rate = P(T=1|Z=1) - P(T=1|Z=0) = 0.60 - 0.10 = 0.50. This means 50% of users are compliers -- they take treatment when offered and don't when not offered. The 10% in control are always-takers. The 40% who don't take treatment when offered are never-takers. Under monotonicity (no defiers), these three groups exhaust the population: 50% compliers, 10% always-takers, 40% never-takers. The CACE applies to the 50% complier group."

### Q2: "Your ITT is $8.40 and your CACE is $16.80. The naive per-protocol estimate is $25. Which do you present to the VP?"
**What they're testing**: Can you match the right estimand to the right business question?
**Strong answer**: "It depends on the question: (1) 'If we send this offer to everyone, what's the average revenue increase?' -- present ITT ($8.40). This is what the VP can directly act on. (2) 'Does Game Pass itself drive revenue for users who use it?' -- present CACE ($16.80). This answers whether the product creates value. (3) NEVER present per-protocol ($25) -- it's biased upward because it compares self-selected users. I'd present both ITT and CACE with clear labels: 'For every user we offer the trial to, we gain $8.40 on average. Among users who actually try Game Pass because of our offer, the gain is $16.80.'"

### Q3: "How would you characterize the complier subpopulation without being able to identify individuals?"
**What they're testing**: Do you know complier profiling techniques?
**Strong answer**: "I can't identify individual compliers, but I can estimate the DISTRIBUTION of their characteristics. Method: for any characteristic X, the average X among compliers is: E[X | complier] = (E[X·T | Z=1] - E[X·T | Z=0]) / (P(T|Z=1) - P(T|Z=0)). This is a weighted IV-style estimator. I can compute this for age, engagement, tenure, etc. to build a statistical profile: 'compliers tend to be newer users (avg 8 months vs 24 months overall), moderate engagement (15 hours/month vs 20 overall), and more often on console than PC.' This helps the PM understand WHO the CACE applies to."

### Q4: "If we increase the take-up rate (e.g., better UX for trial activation), does the CACE change?"
**What they're testing**: Do you understand CACE as a function of the complier population?
**Strong answer**: "Yes, the CACE would likely change because the COMPLIER population changes. With better UX: (1) some former never-takers become compliers -- these are the 'marginal' users who needed a lower barrier. Their treatment effect might be SMALLER (they were less interested to begin with) or LARGER (they were deterred by friction, not disinterest). (2) The existing compliers are still compliers. (3) The new CACE is a weighted average of the old compliers and the new ones. In general, expanding compliance means the CACE moves toward the ATE as you include more of the population. But it won't necessarily stay at $16.80."

### Q5: "What's the relationship between CACE and the IV estimand? When are they the same?"
**What they're testing**: Technical depth on the connection.
**Strong answer**: "They're the same when the experiment assignment is the instrument. CACE is the Wald estimator: ITT / (first-stage compliance rate), which is algebraically identical to the IV/2SLS estimator using Z (assignment) as instrument for T (treatment). Under the LATE theorem (Imbens & Angrist): if monotonicity holds, the IV estimand equals the average treatment effect for compliers. This is why CACE and LATE are the same thing. The connection breaks if monotonicity fails (defiers exist) or if the exclusion restriction fails (assignment directly affects the outcome beyond its effect through treatment)."

### Q6: "We're debating whether to report ITT or CACE in the experiment report. The A/B testing platform only reports ITT. Should we change it?"
**What they're testing**: Practical judgment about default reporting.
**Strong answer**: "Keep ITT as the default. It's unbiased, requires no additional assumptions (no monotonicity, no exclusion restriction), and answers the most operationally relevant question: 'what happens when we expose users to this feature/offer?' CACE should be a supplementary analysis for situations where non-compliance is substantial and the team wants to understand the mechanism. I'd add CACE as an optional analysis in the experimentation platform, clearly labeled with its assumptions, for cases where compliance < 80%. For high-compliance experiments (e.g., UI changes where compliance ≈ 100%), CACE ≈ ITT and there's no need to report both."
