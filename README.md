# Quresal

Small QUBO examples for allocating RAM among workloads. Each dataset is a
workload-by-increment utility table: a row is a workload and each value is the
utility of assigning its next optional 1 GB increment. Minimum RAM allocations
are fixed; the QUBO chooses the additional allocations within the server's
remaining capacity.

# Installation

```bash
uv sync
```

## Project layout

- `data/ram_allocation_3x3.json` — 3 workloads × 3 optional RAM increments.
- `data/ram_allocation_5x5.json` — 5 workloads × 5 optional RAM increments.
- `src/quresal/model.py` — JSON loading and the constrained binary
  allocation model.
- `src/quresal/qubo.py` — Qiskit QUBO conversion and the small
  simulated-annealing solver.
- `scripts/solve_allocation.py` — command-line runner for either dataset.

## Run

The repository already includes its virtual environment. Run either dataset
from the repository root:

```bash
.venv/bin/python scripts/solve_allocation.py data/ram_allocation_3x3.json
.venv/bin/python scripts/solve_allocation.py data/ram_allocation_5x5.json
```

The command reports the QUBO energy, the RAM allocation found, its utility,
and the optimum from SciPy's MILP solver. The latter is a classical reference
for checking the small examples.

## Test

```bash
.venv/bin/python -m pytest
```
