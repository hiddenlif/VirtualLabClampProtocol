# Evaluator method

`protocol_score.py` is the executable public specification. It propagates a
three-state continuous-time Markov model in 20 ms observation intervals using a
matrix exponential. States are closed, open, and inactivated. The generator is
column-conservative and includes closed/open activation and deactivation,
open-to-inactivated loss, and inactivated-to-closed recovery.

Each of the first four parameters is a multiplicative rate scale represented in
log space. The fifth is a log conductance scale. Current at each sample is
`g_nS * P_open * (V_mV - E_rev_mV)` in pA. The initial state is the stationary
distribution at the disclosed -80 mV hold; later states are never reset between
segments.

The sensitivity Jacobian uses the disclosed central log-parameter perturbation.
The noise-weighted Fisher matrix is `J.T @ diag(1/sigma^2) @ J`. The evaluator
reports its smallest eigenvalue and log determinant per variant, then the
minimum across variants. A larger determinant shrinks the joint local confidence
ellipsoid; a larger minimum eigenvalue improves the weakest identifiable
parameter combination.

Saturation is assessed at every sampled mean current plus five modeled standard
deviations. Terminal occupancy is propagated over the entire last holding
segment. Both constraints are evaluated separately from information quality.
