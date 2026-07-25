# Research note: Gaussian copula zero tail dependence + its role in the 2008 CDO crisis

Fork task for `climate_cat_lab/LAB_PLAN.md`. Verifies two claims: (a) the Gaussian copula has
zero asymptotic tail dependence (mathematical fact), and (b) the Gaussian copula was widely used
for CDO pricing and is broadly cited as a contributing factor in 2008 mispricing (historical/
attribution claim — weaker-form evidence expected here, and found).

## Claim (a): Gaussian copula has zero asymptotic tail dependence — VERIFIED, primary source

**Source:** Catherine Donnelly and Paul Embrechts, "The devil is in the tails: actuarial
mathematics and the subprime mortgage crisis," RiskLab, ETH Zürich, January 4, 2010. Published
in *ASTIN Bulletin* 40(1), pp. 1-33 (2010). PDF (author's own institutional copy):
https://people.math.ethz.ch/~embrecht/ftp/CD_PE_devil_Jan10.pdf — fetched and read directly
(pages 1-4 and 10-16), 2026-07-23.

Section 5.1 ("Inadequate modeling of default clustering"), p.13, gives the formal definition and
result verbatim:

> **Definition 5.1.** Let X and Y be random variables with dfs F and G, respectively. The
> coefficient of upper tail dependence of X and Y is
> λ_u := λ_u(X,Y) := lim_{q→1⁻} P(Y > G^←(q) | X > F^←(q)),
> provided a limit λ_u ∈ [0,1] exists. If λ_u ∈ (0,1] then X and Y are said to show upper tail
> dependence. If λ_u = 0 then X and Y are said to be asymptotically independent in the upper tail.
>
> ... Suppose X and Y have a joint df with Gaussian copula C^gau_ρ. As long as ρ < 1, it turns
> out that the coefficient of upper tail dependence of X and Y equals zero; see McNeil et al.
> (2005, Example 5.32). This means that if we go far enough into the upper tail of the joint
> distribution of X and Y, extreme events appear to occur independently.
>
> Recall that the dependence structure in the Li model is given by the Gaussian copula. The
> asymptotic independence of extreme events for the Gaussian copula carries over to asymptotic
> independence for default times in the Li model. If we seek to model defaults which cluster
> together, so that they exhibit dependence, the property of asymptotic independence is not
> desirable. **This undesirable property of the Gaussian copula is pointed out in Embrechts et
> al. (2002)** and was explicitly mentioned in the talk referred to at the beginning of Section 4.
> A first mathematical proof is to be found in Sibuya (1960).

This is a second, independent corroborating source (a specialist arXiv paper, not fetched in full
but confirmed via WebFetch summary of its abstract/results):

> Furman, Kuznetsov, Su, Zitikis, "Tail dependence of the Gaussian copula revisited," arXiv:1607.04736
> (2016) — Corollary 1(A): "λ_L*(C_ρ) = λ_L(C_ρ) = 0" for the Gaussian copula when ρ ∈ [0,1),
> i.e. the lower tail dependence coefficient is zero across the whole correlation range short of
> perfect correlation.

Donnelly & Embrechts also trace the original attribution: the "undesirable property" was **first
pointed out in Embrechts, McNeil & Straumann (2002), "Correlation and Dependence in Risk
Management: Properties and Pitfalls,"** *in* M.A.H. Dempster (ed.), *Risk Management: Value at
Risk and Beyond*, Cambridge University Press, pp. 176-223 — the paper `LAB_PLAN.md` cites as the
canonical reference. I could not get open full-text access to this specific chapter (Cambridge
UP paywall; ResearchGate/SciRP list only the reference, not fetchable text), so I am not quoting
it directly — but its priority and content are independently confirmed by Donnelly & Embrechts
(2010) above, one of whose two authors (Embrechts) is a co-author of the original 2002 paper,
which is about as strong as secondary confirmation gets.

**Verdict: VERIFIED.** This is settled mathematics, not a contested industry claim — a named
theorem with a 1960 origin (Sibuya), formalized for finance by Embrechts/McNeil/Straumann (2002),
and restated with full proof sketch in the 2010 paper quoted above.

## Claim (b): Gaussian copula was widely used for CDO pricing, and is broadly cited as a
## contributing factor in 2008 mispricing — PARTIALLY VERIFIED, with an important nuance

**Industry adoption — verified, and stronger than "one company" (directly useful for the
LAB_PLAN.md "not one oddball company" concern):** Donnelly & Embrechts (2010), Section 5, p.12:

> The advantages of the model meant that it was quickly adopted by industry. **For instance, by
> the end of 2004, the three main rating agencies — Fitch Ratings, Moody's and Standard & Poor's
> — had incorporated the model into their rating toolkit. Moreover, it is still considered an
> industry standard.**

This is a direct, citable statement that three independent major rating agencies adopted the
model — good primary evidence against the "one oddball company" risk, and it strengthens (rather
than duplicates) the separate rating-agency capital-model research fork's task, since it shows
copula-based correlation modeling specifically entered rating-agency methodology, not just bank
trading desks.

**Popular-press attribution — verified as existing and influential, sourced verbatim:** Felix
Salmon, "Recipe for Disaster: The Formula That Killed Wall Street," *Wired* magazine, February
23, 2009 (Wired cover story; Salmon won the American Statistical Association's 2010 Excellence in
Statistical Reporting Award for it — per search-result summary of the piece's reception). Original
Wired URL returned 403 on fetch; text confirmed via a contemporaneous full-text mirror
(srkaufman72.wordpress.com, 2009-02-25 repost), quoted directly:

> "Armed with Li's formula, Wall Street's quants saw a new world of possibilities. And the first
> thing they did was start creating a huge number of brand-new triple-A securities."
>
> "The Gaussian copula soon became such a universally accepted part of the world's financial
> vocabulary that brokers started quoting prices for bond tranches based on their correlations."
>
> "People used the Gaussian copula model to convince themselves they didn't have any risk at all,
> when in fact they just didn't have any risk 99 percent of the time."

**The important nuance LAB_PLAN.md should reflect:** the more rigorous academic treatment of this
same claim explicitly *pushes back* on the popular-press framing. Donnelly & Embrechts (2010),
p.1-2, direct quotes:

> "'Recipe for disaster: the formula that killed Wall Street'. That was the title of a web-article
> Salmon (2009) that appeared in Wired Magazine... The impression gained is that an actuary
> developed a mathematical model which subsequently caused the downfall of Wall Street banks."
>
> "For some of us, the implication that a mathematical model shoulders much of the blame for the
> difficulties on Wall Street and that few people were aware of its limitations are untenable.
> **Indeed, we aim to demonstrate that such criticism is entirely unjustified.**"
>
> "We cannot answer every accusation directed at financial mathematics. Instead, we look at the
> Li model, also called the Gaussian copula model, and use it as a proxy for mathematics applied
> badly in finance. It should be abundantly clear that it is not mathematics that caused the
> Crisis. **At worst, a misuse of mathematics, and we mean mathematics in a broad sense and not
> just one formula, partly contributed to the Crisis.**"

And, importantly, they document that the model's specific tail-dependence flaw was **known and
publicly reported years before the crisis**, not discovered in hindsight — the May 2005 Ford/GM
downgrade event (p.14) "brought to the attention of market participants in a dramatic fashion,"
covered in a front-page 2005 Wall Street Journal article (Whitehouse 2005), three years before
Salmon's piece. This is actually a *stronger*, more defensible version of the claim for
`LAB_PLAN.md` to use than "nobody saw it coming": the tail-dependence blindness of linear/
Gaussian correlation aggregation was understood, demonstrated in a real market event, and
published *while the model remained in standard industry use* — which is precisely the
"known shortcut, still standard practice" framing the lab needs, and is more defensible than
implying the flaw was unknown.

**Verdict: PARTIALLY VERIFIED, with required rephrasing.** Recommend `LAB_PLAN.md` drop or soften
the Salmon citation as primary support, and lean on Donnelly & Embrechts (2010) instead — it is
peer-reviewed, gives the "partly contributed, not sole cause" framing that is actually more
defensible, and independently confirms three-rating-agency adoption. Do NOT phrase this as
"the Gaussian copula caused/killed Wall Street" (the popular framing, explicitly rejected by the
peer-reviewed source) — phrase it as "a well-documented instance where a linear-correlation
aggregation shortcut's known tail-dependence blindness partly contributed to a systemic mispricing
event, and remained standard industry practice for years after the flaw was published."

## Sources used

1. Donnelly, C. & Embrechts, P. (2010). "The devil is in the tails: actuarial mathematics and the
   subprime mortgage crisis." *ASTIN Bulletin* 40(1), 1-33.
   https://people.math.ethz.ch/~embrecht/ftp/CD_PE_devil_Jan10.pdf (fetched, read directly, 2026-07-23)
2. Furman, E., Kuznetsov, A., Su, J., Zitikis, R. (2016). "Tail dependence of the Gaussian copula
   revisited." arXiv:1607.04736. (fetched via ar5iv HTML, 2026-07-23)
3. Embrechts, P., McNeil, A., Straumann, D. (2002). "Correlation and Dependence in Risk
   Management: Properties and Pitfalls." In Dempster, M.A.H. (ed.), *Risk Management: Value at
   Risk and Beyond*, Cambridge University Press, 176-223. (citation and content confirmed via
   source #1 above, co-authored by Embrechts himself; full text not directly accessed — paywalled)
4. Li, D.X. (2000). "On Default Correlation: A Copula Function Approach." SSRN abstract page
   https://papers.ssrn.com/sol3/papers.cfm?abstract_id=187289 (fetch attempt returned HTTP 403;
   citation and content confirmed indirectly via sources #1 and search summaries)
5. Salmon, F. (2009). "Recipe for Disaster: The Formula That Killed Wall Street." *Wired*,
   February 23, 2009. Original URL 403'd; full text confirmed via contemporaneous mirror
   https://srkaufman72.wordpress.com/2009/02/25/recipe-for-disaster-the-formul-0/ (fetched 2026-07-23)
