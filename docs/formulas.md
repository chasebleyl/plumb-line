# Putting Stroke Measurement Formulas

Formulas and event-detection methods for the three initial metrics: tempo, face angle at
impact, and stroke path. Each entry states whether the formula is quoted from a source or
derived here from a source's geometric definition (the golf-science literature defines these
metrics verbally/geometrically; no paper prints an explicit trig equation — commercial systems
like TOMI and SAM PuttLab keep their internal math proprietary).

## Coordinate frame and shared signal pipeline

Reference frame (MacKenzie & Evans, 2010, p. 892[^1]):

- **+X** — along the target line, from the center of the putter face toward the intended
  initial launch direction of the putt.
- **+Y** — vertically up.
- **+Z** — right-hand rule (heel–toe axis).
- **Origin** — theoretical putter-face-center position when the face is flush with the ball
  with zero face angle and zero impact spot.

For breaking putts, the target line is the golfer's *intended initial launch direction*, not
the ball-to-hole line (MacKenzie & MacInnis, 2017, p. 58[^4]): "the far target should be a
point on a line that extends out from the intended initial launch direction of the ball—the
target line." The X-axis must therefore be defined per-putt.

Signal processing pipeline (MacKenzie & Evans, 2010, pp. 893–894[^1]; reused verbatim in
MacKenzie, Foley & Adamczyk, 2011[^3]):

1. Filter raw 3D position data with a **4th-order zero-lag low-pass Butterworth filter,
   8 Hz cutoff**. Justified by power-spectral-density analysis showing negligible signal
   power above 10 Hz for both linear and angular putter-head displacement.
2. If sampling rate is low (TOMI: 30 Hz), **resample to 1000 Hz** via frequency-domain
   reconstruction per Shannon's sampling theorem (Hamill, Caldwell & Derrick, 1997[^8]).
   Valid because 30 Hz > 2 × the ~10 Hz maximum signal frequency.
3. **Filter before differentiating** — numerical differentiation amplifies high-frequency
   noise (Robertson et al., 2004[^7]; Giakas & Baltzopoulos, 1997[^9]).

Impact detection — two documented methods:

- **Nearest-sample:** impact = the sample in the (resampled) putter-head trajectory closest
  to the calibrated origin (0, 0, 0) (MacKenzie & Evans, 2010, p. 894[^1]).
- **Forward extrapolation:** fit a 2nd-order polynomial to the 13 samples preceding impact
  and evaluate at the predicted impact time (MacKenzie & Henrikson, 2018[^2]; used with a
  250 Hz optical system).

## 1. Tempo

No MacKenzie paper defines a tempo metric — his TOMI framework covers only the four impact
variables (face angle, stroke path, putter speed, impact spot)[^1]. Tempo formulas come from
Marquardt's SAM PuttLab tour data (empirical) and Grober's resonance model (theoretical),
which independently converge on the same ~2:1 ratio.

### Phase events

From the putter-head position signal along the stroke direction (velocity `v` and
acceleration `a` by successive differentiation):

- **Start of backswing** `t_start`: acceleration first exceeds a threshold after stationary
  address. SAM PuttLab uses **|a| ≥ 0.6 m/s²** (Marquardt, 2007[^5]).
- **Top of backswing (transition)** `t_top`: velocity zero-crossing = position extremum
  (farthest point from the ball). Both the theoretical definition in Grober's model[^6] and
  the implicit definition of SAM PuttLab's "top of backswing"[^5].
- **Impact** `t_impact`: see impact detection above.
- **End of forward swing** `t_end`: velocity returns to ~zero after impact (follow-through
  extremum).

### Formulas (Marquardt, 2007, Table 2[^5])

```
Backswing Time      BST = t_top − t_start
Time to Impact      TI  = t_impact − t_top
Forward Swing Time  FST = t_end − t_top

Backswing Rhythm (tempo ratio) = BST / TI
Impact Timing                  = TI / FST
```

Reference values from 99 PGA/European Tour players (straight 4 m putts, 210 Hz ultrasound
capture)[^5]:

| Metric | Tour average | SD | Intra-player consistency |
|---|---|---|---|
| BST | 670 ms | 90 ms | 30 ms |
| TI | 317 ms | 35 ms | 11 ms |
| FST | 820 ms | 100 ms | 45 ms |
| Backswing Rhythm | **2.1** | 0.29 | 0.11 |
| Impact Timing | 0.39 | 0.04 | 0.02 |

The ratio is stable across players with very different absolute speeds (Tiger Woods: rhythm
2.2 at BST 660 ms; Loren Roberts: rhythm 2.2 at BST 977 ms)[^5].

### Theoretical basis (Grober, 2009[^6])

Modeling the stroke as a driven pendulum, `ẍ + ω₀²x = f(t)/m`: an impulsive force at the
start of the backswing gives `ω₀·τ_b = π/2` regardless of impulse magnitude; the second
impulse at transition sets the downswing duration via `tan(ω₀·τ_d) = p_b/p_d`, and the
equal-magnitude condition `p_b = p_d` specifically yields `ω₀·τ_d = π/4` — hence
**τ_b/τ_d = 2 exactly**, matching the empirical 2.1. The equal-impulse condition also
minimizes impact-speed variance under random force errors (the paper's own wording is
"local minimum," though it is the unique minimum over the physical domain; assumes
uncorrelated backswing/downswing errors of equal relative variance) — i.e., 2:1 tempo is a
robustness optimum, not just a stylistic norm. Equivalent continuous form: the stroke is
driven at twice its resonant frequency, `f(t) = −f₀·sin(2ω₀t)` for `0 < ω₀t < π`, zero
otherwise.

Caveat: MacKenzie & Henrikson (2018) Figure 2 states the forward stroke starts at
approximately 80% of normalized stroke duration (~4:1), but that is a plot-axis
normalization, not an operationalized tempo metric — the likely reconciliation with the 2:1
BST/TI ratio is that the normalization runs to end of forward swing rather than impact (our
inference; the paper does not state how the 0–100% axis is anchored). Do not treat it as
comparable to Backswing Rhythm[^2].

## 2. Face angle at impact

### Definition

> "Face angle is defined as the angle formed between the target line and a line
> perpendicular to the putter face." — MacKenzie & Evans, 2010, pp. 892–893[^1]

Measured at impact. We project onto the horizontal (X–Z) plane before computing the angle —
that projection is our implementation choice, not stated in the source (implied by the
coordinate frame and Figure 1b's top-down view, but never asserted). It matters physically:
a putter has ~3–4° of loft, so the true face normal has a nonzero Y-component that the
projection discards.

**Sign convention:** positive = face normal pointing right of the target line ("face angle
at impact; positive is pointing to the right," MacKenzie & Henrikson, 2018, Figure 3[^2]).
This holds regardless of golfer handedness; for a right-handed golfer, a face pointing right
of target is termed "open" — an inference from that paper's results (their +0.69° condition
is described as "a significantly more open face at impact"), not a printed definition.

### Formula (derived — see note)

With `n = (n_x, n_y, n_z)` the putter-face normal unit vector (from heel/toe face markers or
sensor orientation) at the impact sample:

```
θ_face = atan2(n_z, n_x)        [degrees after conversion; horizontal-plane projection]
```

*Note: no source paper prints this equation; it is the direct trigonometric form of the
quoted geometric definition and coordinate frame above[^1]. The sign mapping was verified
by direct derivation: with +X toward the target and +Y up, the right-hand rule gives
+Z = X × Y pointing right of the target line viewed from above, so positive θ_face = face
pointing right = open for a right-handed golfer. Still verify against your calibration.*

Karlsen, Smith & Nilsson (2008)[^10] define face angle relative to the golfer's *aim line
at address* rather than the true target line, which decouples aiming error from stroke
error — worth considering if we later measure aim at address separately.

### Why it matters — contribution to initial ball direction

> "Face angle has been reported to account for 83% of the initial direction of a putt
> (Pelz & Frank, 2000)." — MacKenzie & Evans, 2010, p. 897[^1]

Karlsen et al. (2008)[^10], from 1,301 putts by 71 elite golfers, found face angle ≈ 80%,
path ≈ 17%, impact point ≈ 3% of direction-consistency variance. Their effective-variability
weightings — 0.83 (face) and 0.17 (path), both adopted from Pelz & Frank (2000), plus
0.034 °/mm (impact point) from Nilsson & Karlsen's own unpublished data — were applied to
*variability* (standard deviations) in a quadratic decomposition with covariance terms, not
to signed angles. Rough launch-direction heuristic:

```
θ_ball ≈ 0.83·θ_face + 0.17·θ_path        (center-face contact assumed)
```

This linear form is our own construction and extrapolates beyond both sources: Pelz states
only the percentages, and Karlsen et al. used the coefficients for variance propagation.
Treat it as an engineering heuristic, not a validated launch model. MacKenzie & Evans
caution "there probably is no set analytical equation for computing ball direction from
putter head kinematics during impact" — the weights are experimental guidelines (Cochran &
Stobbs, 1968; Karlsen et al., 2008; Pelz & Frank, 2000; Werner & Greig, 2000)[^1].

### Accuracy targets

TOMI face-angle validity: bias 0.02°, 95% limits of agreement ±0.19° (n = 50); test–retest
reliability ±0.21° (n = 25)[^1]. A face-angle error > ~0.6–0.7° causes misses from 4 m[^1].
Expected human variability: ~0.75° SD at 1.22 m, ~0.99° SD at 4 m[^3]. Our system should
target measurement error well under ±0.25° to stay negligible relative to human variability.

## 3. Stroke path

### Definition

> "Stroke path is defined as the angle between the velocity vector of the putter head and
> the target line." — MacKenzie & Evans, 2010, p. 893[^1]

Measured at impact. As with face angle, the horizontal-plane treatment is implied by the
coordinate frame but not stated by the source.

**Sign convention:** positive = path pointing right of the target line ("putter path at
impact; positive is to the right," MacKenzie & Henrikson, 2018, Figure 3[^2]). In golf
terminology that is in-to-out for a right-handed golfer — our gloss; the paper uses only
the geometric statement.

### Formulas

Velocity by central difference on the filtered, resampled position data. MacKenzie & Evans
state the method only for X-axis displacement (putter speed, p. 894[^1]); extending it to
the Z component is our own step — the paper gives no method for computing stroke path from
coordinate data (in their validity study, path was a preset robot/laser ground truth).
Standard form per Robertson et al., 2004[^7]:

```
v_x[i] = (x[i+1] − x[i−1]) / (2Δt)
v_z[i] = (z[i+1] − z[i−1]) / (2Δt)        (v_z: our extension, same standard form)
```

Path angle at the impact sample (derived — same status as θ_face; the paper's definition is
geometric):

```
θ_path = atan2(v_z, v_x)
```

Putter speed (defined in the same paper as velocity of the face center along the target
line): `putter_speed = v_x` at impact[^1].

### Stroke arc

Beyond the impact-path angle, we found no peer-reviewed formula for quantifying arc
curvature (straight-back-straight-through vs. arced) — two independent literature searches
surfaced only patents and commercial marketing material, though absence in a search is not
proof of absence. Brooks (2002)[^11] mathematically modeled the competing arc types without
concluding which is best. If we want an arc metric, a circle fit
or radius-of-curvature computation on the horizontal (X–Z) trajectory is a defensible
engineering choice — but it should be documented as our own method, not a cited one.

### Why it matters / accuracy targets

Stroke path accounts for ~16–20% of initial ball direction (17% per Karlsen et al., 2008 and
Pelz & Frank, 2000)[^1][^10] — a path error > 3.5° is needed to start the ball 0.6°
offline[^1]. TOMI path validity: bias −0.03°, 95% LoA ±1.15°; the larger error vs. face
angle traces to sensor-clip rotational alignment on the shaft (1° clip misalignment = 1°
path error, while face angle is immune to clip misalignment)[^1] — relevant to our own
sensor-mounting design. Expected human path variability is ~1.3–1.4° SD (read from
Figure 7 of the 2011 paper, not a printed statistic) and, unlike face angle, does not
increase with putt distance (F(1,29) = 0.5, p = 0.484)[^3].

## References

[^1]: MacKenzie, S. J., & Evans, D. B. (2010). ["Validity and reliability of a new method for measuring putting stroke kinematics using the TOMI system."](http://www.sashomackenzie.com/publications/MacKenzie%202010%20Validity%20and%20reliability%20of%20a%20new%20method%20for%20measuring%20putting%20stroke%20kinematics%20using%20the%20TOMI%20systerm.pdf) *Journal of Sports Sciences*, 28(8), 891–899. DOI: 10.1080/02640411003792711. Full text read directly.
[^2]: MacKenzie, S. J., & Henrikson, E. (2018). ["Influence of Toe-Hang vs. Face-Balanced Putter Design on Golfer Applied Kinetics."](http://www.sashomackenzie.com/publications/MacKenzie%202018%20Influence%20of%20Toe-Hang%20vs.%20Face-Balanced%20Putter%20Design%20on%20Golfer%20Applied%20Kinetics.pdf) *Proceedings*, 2(6), 244–250. DOI: 10.3390/proceedings2060244. Source of the sign conventions (Figure 3) and the polynomial impact-extrapolation method.
[^3]: MacKenzie, S. J., Foley, S. M., & Adamczyk, A. P. (2011). ["Visually focusing on the far versus the near target during the putting stroke."](http://www.sashomackenzie.com/publications/MacKenzie%202011%20Visually%20focusing%20on%20the%20far%20versus%20the%20near%20target%20during%20the%20putting%20stroke.pdf) *Journal of Sports Sciences*, 29(12), 1243–1251. DOI: 10.1080/02640414.2011.591418. Baseline face-angle and stroke-path variability figures.
[^4]: MacKenzie, S. J., & MacInnis, N. R. (2017). ["Evaluation of Near Versus Far Target Visual Focus Strategies With Breaking Putts."](http://www.sashomackenzie.com/publications/MacKenzie%202017%20Evaluation%20of%20Near%20Verus%20Far%20Target%20Visual%20Focus%20Strategies%20with%20Breaking%20Putts.pdf) *International Journal of Golf Science*, 6(1), 56–67. DOI: 10.1123/ijgs.2017-0009. Target-line definition for breaking putts.
[^5]: Marquardt, C. (2007). ["The SAM PuttLab: Concept and PGA Tour Data."](https://sam-academy.com/wp-content/uploads/2020/04/ARGC07-SAM-PuttLab-Concept-and-Tour-Data.pdf) *Annual Review of Golf Coaching 2007*, 101–114. Full text read directly; tempo metric definitions and Tour reference values (Table 2).
[^6]: Grober, R. D. (2009). ["Resonance in Putting."](https://arxiv.org/abs/0903.1762) arXiv:0903.1762 [physics.pop-ph]. Full text read directly; theoretical derivation of the 2:1 tempo ratio.
[^7]: Robertson, D. G. E., Caldwell, G. E., Hamill, J., Kamen, G., & Whittlesey, S. N. (2004). *Research Methods in Biomechanics*. Champaign, IL: Human Kinetics. Central-difference differentiation; cited by MacKenzie & Evans (2010) for signal-frequency norms.
[^8]: Hamill, J., Caldwell, G. E., & Derrick, T. R. (1997). "Reconstructing digital signals using Shannon's sampling theorem." *Journal of Applied Biomechanics*, 13(2), 226–238. Basis for the 30 Hz → 1000 Hz resampling step.
[^9]: Giakas, G., & Baltzopoulos, V. (1997). "Optimal digital filtering requires a different cut-off frequency strategy for the determination of the higher derivatives." *Journal of Biomechanics*, 30(8), 851–855. PMID: 9239572. Filter-before-differentiate rationale.
[^10]: Karlsen, J., Smith, G., & Nilsson, J. (2008). "The stroke has only a minor influence on direction consistency in golf putting among elite players." *Journal of Sports Sciences*, 26(3), 243–250. DOI: 10.1080/02640410701530902. Full text read directly (free copy at people.stfx.ca/smackenz/Publications/); 80/17/3 relative-importance result and effective-variability equations. Note: the 0.83/0.17 coefficients therein are adopted from Pelz (2000); only the 0.034 °/mm impact-point coefficient is Nilsson & Karlsen's own (unpublished) data.
[^11]: Brooks, R. J. (2002). "Is it a pendulum, is it a plane? Mathematical models of putting." In E. Thain (Ed.), *Science and Golf IV: Proceedings of the World Scientific Congress of Golf* (pp. 127–141). London: Routledge. Cited via MacKenzie & Sprigings (2005); not read directly — lead for future arc-type modeling.

### Verification notes

- Quoted definitions from MacKenzie & Evans (2010) were confirmed word-for-word by two
  independent reads of the PDF.
- `atan2` formulas for face angle and stroke path are **derived**, not quoted — no paper in
  this corpus prints explicit trig equations.
- Delay, Nougier, Orliaguet & Coello (1997), *Human Movement Science* 16:597–619 (DOI:
  10.1016/S0167-9457(97)00008-0) is relevant tempo precedent (downswing duration constant
  across putt lengths; distance controlled via amplitude) but was paywalled — findings known
  only from abstracts, so it is not load-bearing above.
- Pelz & Frank (2000), *Dave Pelz's Putting Bible* (Doubleday): the 83%/17% split was
  verified via direct quotes inside MacKenzie & Evans (2010) and Karlsen et al. (2008), not
  from the book itself.
- Section 3 (Stroke path) was audited by two independent verifiers (2026-07-23), each
  reading all five primary sources in full. Every quote, table number, percentage, and the
  clip-misalignment mechanism verified exactly; the Brooks (2002) characterization matches
  the citing sentence in MacKenzie & Sprigings (2005) near-verbatim. Corrections applied in
  place: the horizontal-plane treatment and the "in-to-out" gloss are our inferences (not
  source statements); the central-difference method is source-stated for the X-axis only,
  with the v_z extension being ours; the ~1.3–1.4° SD figure is read from a bar chart, not
  printed; and the no-arc-formula claim is softened to reflect that it is a search-based
  negative. Both verifiers independently re-derived the +Z-right-of-target geometry and
  found no sign errors.
- Section 2 (Face angle) was audited by two independent verifiers (2026-07-23), each reading
  all four primary sources in full. Every quote, number, and the coordinate-frame geometry
  verified exactly (the +Z-right-of-target sign mapping was confirmed by independent vector
  derivation by both). Three attribution issues found and corrected in place: the
  horizontal-plane projection is our implementation choice (unstated in sources);
  "positive = open" is an inference from the 2018 results, not a printed definition; and the
  0.83/0.17 weightings originate with Pelz (2000), with the linear θ_ball heuristic being
  our extrapolation beyond both sources' actual usage.
- Section 1 (Tempo) was audited by two independent verifiers (2026-07-23), each reading the
  Grober and Marquardt primary sources in full; all quoted equations and Table 2 numbers
  matched exactly, and the Grober ODE solution was re-derived by hand. Terminology note:
  Grober formally defines `x` as pendulum angle but plots/treats it as linear displacement
  throughout; this doc follows the paper's de facto displacement usage. Marquardt lists
  "top of backswing" and "end of forward swing" among his nine detected positions without
  printing detection criteria — the velocity-zero-crossing criteria in Phase Events are the
  physically implied (top) and our own operational (end) definitions.
