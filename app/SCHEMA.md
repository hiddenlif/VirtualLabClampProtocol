# `protocol.json` schema

The file is a JSON object with exactly `segments`. It contains exactly ten
objects, each with exactly two finite numeric fields:

- `voltage_mv`: a member of the disclosed voltage grid;
- `duration_ms`: a member of the disclosed duration grid.

No identifier, score, comment, code, or auxiliary file is graded. The complete
ordering and all ten values are recomputed by the verifier.

