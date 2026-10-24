# Simulation Design Task: Voltage-Clamp Protocol Optimization

Design an ordered voltage-clamp protocol for a synthetic ion-channel model. Candidate protocols produce simulated currents and information metrics across four disclosed cell variants. This is prospective protocol optimization rather than a closed-loop acquisition campaign.

**Task type:** Simulation-based experimental design. **Source version:** 1.0.1.

All scientific specimens, measurements and instrument conditions are synthetic. These examples are not validated biological assays or clinical decision tools.

## Contents

- `TASK.md`: scientific task and required deliverable.
- `app/`: public scientific model, documentation and disclosed practice inputs where supplied.
- `Dockerfile`: the task's original dependency environment.

## Use

Build the environment with `docker build -t virtual-lab-clamp .`.

Create `app/protocol.json` using `TASK.md`, then evaluate the public scientific metrics inside the container:

```sh
docker run --rm -v "$PWD/app":/app virtual-lab-clamp python3 /app/selfcheck.py
```

The public evaluator reports scientific metrics. Final acceptance thresholds and the grading harness are private.

## Execution evidence

On 2026-10-24 this published repository was run end to end: with the private reference installed in `app/`, the protocol written by the private reference optimizer in the task image passed all five grader checks (reward 1); the unchanged starter, with no protocol, scored 0. A historical clean-extraction run of the source version also passed. These are local reference results in Docker, not blind solver results or platform approval.

## Reference and verifier

Reference implementations, held-out cases, expected results and grading code are kept in the private repository `science-task-solutions`, under `VirtualLabClampProtocol/`. They are excluded from this public repository. The public practice inputs and worked examples remain public by design.
