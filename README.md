# Virtual Lab: clamp protocol

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

A historical clean-extraction container run passed all five reference checks. A no-op and two legal negative controls scored zero. These are local reference results, not blind solver results or platform approval.

The historical evidence concerns the source version. This publication separates public inputs from private evaluation material and cleans documentation. No new task execution or model trial was performed for this publication, and the cleaned repository has not been revalidated end to end.

## Reference and verifier

Reference implementations, held-out cases, expected results and grading code are kept in the private repository `science-task-solutions`, under `VirtualLabClampProtocol/`. They are excluded from this public repository. The public practice inputs and worked examples remain public by design.
