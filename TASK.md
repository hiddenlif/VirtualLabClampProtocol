# Design a robust voltage-clamp identification protocol

Create `/app/protocol.json`, an ordered whole-cell voltage-clamp protocol for
the disclosed synthetic ion-channel preparation. The experiment will estimate
five local log-parameters: four scale activation, deactivation, inactivation and
recovery rates while the fifth scales conductance. Maximize
information in the least informative of four disclosed cell variants while
satisfying the amplifier and return-to-hold constraints.

This is prospective experimental design. The order of the voltage steps is part
of the answer: each step starts from the closed/open/inactivated occupancy left
by the steps before it.

## Artifact schema

The artifact must contain exactly one key:

```json
{
  "segments": [
    {"voltage_mv": -60, "duration_ms": 80}
  ]
}
```

`segments` must contain exactly 10 objects. Each object must have exactly the
keys `voltage_mv` and `duration_ms`, both finite JSON numbers.

The disclosed grids and feasibility rules are in
`/app/protocol_data.json`:

- voltages are selected from `-100 -80 -60 -40 -20 0 20 40` mV.
- durations are selected from the three allowable values `40 80 120` ms for every segment.
- the ten durations must total exactly 800 ms.
- adjacent segments may not use the same voltage; identical neighbors form one uninformative hold.
- the final segment is `-80` mV for at least 80 ms.
- before that final segment, include at least one activation step at or above
  0 mV. Also include one recovery step at or below -80 mV and one kinetic step
  from -60 through -20 mV inclusively.

## Disclosed scientific model

The synthetic channel has closed, open and inactivated state probabilities.
For each voltage, a continuous-time Markov generator propagates those
probabilities using the four transition-rate equations and cell-variant factors
in `/app/protocol_score.py` and `/app/protocol_data.json`. Those files also give
the holding potential, reversal potential and conductance; they specify sampling
behavior plus the noise, amplifier and finite-difference settings. The state
begins at equilibrium at -80 mV and is carried continuously through the ordered
segments. Current is reported in pA using `I = g * P_open * (V - E_rev)`.
Here `g` is in nS and voltage is in mV. For each cell variant, the scorer samples
current every 20 ms and uses central differences with respect to the five
log-parameters to form a sensitivity matrix `J`. For sample `k`,

```text
sigma_k^2 = baseline_pA^2 + current_factor_pA * abs(I_k)
F = sum_k (J_k^T J_k / sigma_k^2)
```

The public evaluator reports the smallest eigenvalue of `F`, its log determinant
and the weighted mean log determinant. Increasing these information values
improves the design. The cross-variant summaries take the minimum log determinant
and minimum eigenvalue, with final acceptance levels held in the assessment environment.

Every current sample must remain within the amplifier range after adding five
noise standard deviations. At the end of the final hold, the open probability
must be at most the public `maximum_terminal_open_probability` in the data.

You may evaluate a candidate locally:

```bash
PROTOCOL_PATH=/app/protocol.json python3 /app/selfcheck.py
```

The assessment parses JSON data and does not execute code from the artifact. No
particular optimization method is required. The supplied measurements are
deterministic synthetic data created for this candidate; they are not patient
data or a validated wet-lab assay.
