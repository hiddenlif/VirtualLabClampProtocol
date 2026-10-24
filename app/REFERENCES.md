# Scientific basis and scope

The task uses established analysis concepts rather than reproducing empirical
records: continuous-time Markov state models for ion-channel gating, whole-cell
current as conductance times open probability times electrochemical driving
force, and Fisher information for local experimental design. Voltage is in mV,
duration in ms, conductance in nS, and current in pA, matching conventional
patch-clamp reporting units.

The model is intentionally self-contained. Every rate law and numerical value
needed for scoring appears in `protocol_score.py` or `protocol_data.json`.
The cell variants and currents are synthetic and are not claimed to match a
named biological channel, patient, instrument calibration, or validated assay.

