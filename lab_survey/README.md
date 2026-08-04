The Soft-EM Gaussian Process Value-of-Information (VoI) engine is not a universal "plug-and-play" upgrade. Its success depends heavily on specific domain characteristics, data geometry, and decision economics.

Across the four test domains, the value added by carrying the full GP posterior variance (the core mechanism driving sequential probing) ranges from **massive (+47.5%)** to **completely useless (+0.0%)** or even **slightly damaging (-0.22%)**.

A breakdown of the empirical results explains why the approach behaves so selectively:

### 1. Where it shines: `hydro_reserve_lab` (+47.53% over GPC-mean)

- **Why it worked:** High residual uncertainty, high decision stakes, and a decision breakeven probability ($p = 0.174$) that sits in the "sweet spot" relative to the true base rate ($25.8\%$).
    
- **Takeaway:** The full posterior variance provides massive value when classification is genuinely hard (no near-perfect separable features) and the action threshold requires resolving ambiguous edge cases.
    

### 2. Where it provides modest value: `grid_reserve_lab` (+0.09% overall)

- **Why it was muted:** The domain's real economic breakeven probability ($0.0016$) sat **40x below** the true drought base rate ($6.5\%$).
    
- **Takeaway:** When economics dictate a near-zero threshold, the decision policy degenerates into "always act/commit". Probing and uncertainty estimation add negligible value because you almost never skip.
    

### 3. Where it completely failed / Null Result: `shm_lab` (+0.00%)

- **Why it failed:** The underlying data was already almost perfectly separable using simple z-scores ($AP \approx 0.999–1.000$).
    
- **Takeaway:** If the classifier is already near-certain using basic mean features, there is no residual posterior variance left for the sequential Probe mechanism to exploit. Furthermore, MacKay moment-matching shrinkage miscalibrated probabilities when the base rate was high ($82.4\%$), causing GPC to underperform SVM.
    

### 4. Where variance actually hurt: `climate_cat_lab` (-0.22% vs. GPC-mean)

- **Why it hurt:** While GPC mean significantly beat SVM (+5.52%), full posterior variance was a small, consistent negative across 9 of 12 points in the sweep.
    
- **Takeaway:** In skewed base-rate regimes ($6.67\%$), GP variance shrinkage can introduce noise into the decision threshold, making a simple calibrated mean classifier superior to full sequential VoI.
    

### Key Requirements for the Engine to Add Value

Before deploying the Soft-EM / GP-VoI engine to a new dataset, ensure the domain meets these prerequisite conditions:

1. **Intermediate Class Separability:** The problem must be hard enough that residual variance exists, but predictable enough that a GP can model it. (If $AP \approx 1.0$, use simpler models).
    
2. **Economic Alignment:** The economic breakeven probability ($C_{\text{action}} / V_{\text{payoff}}$) must sit close to the dataset's true base rate. If it is far below or above, static policy dominates.
    
3. **Symmetric/Balanced Base Rates:** Gaussian Process Laplace approximations tend to over-shrink toward $0.5$ in extreme majority/minority base rates, leading to miscalibration.
    
4. **Actionable Probing Phase:** The domain must structurally support a two-stage decision (Skip $\rightarrow$ Probe $\rightarrow$ Commit/Drill) with cheap intermediate information-gathering.
    
