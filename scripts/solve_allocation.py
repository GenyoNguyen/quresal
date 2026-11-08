"""Run a RAM-allocation QUBO dataset from the repository root."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from qiskit_addon_opt_mapper.solvers import ScipyMilpSolver  # noqa: E402

from quresal.model import build_allocation_model, load_data  # noqa: E402
from quresal.qubo import build_qubo, interpret_allocation, solve_qubo  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve a RAM-allocation QUBO.")
    parser.add_argument("dataset", type=Path, help="Path to a JSON allocation dataset.")
    args = parser.parse_args()

    model = build_allocation_model(load_data(args.dataset))
    qubo = build_qubo(model)
    qubo_result = solve_qubo(qubo)
    allocation_bits = interpret_allocation(qubo, qubo_result)
    feasible, _, _ = model.problem.get_feasibility_info(allocation_bits)
    reference = ScipyMilpSolver().solve(model.problem)

    utility = model.problem.objective.evaluate(allocation_bits)
    capacity_used = 0
    print(f"Dataset: {model.data.name}")
    print(f"QUBO variables: {qubo.number_of_variables}")
    print(f"QUBO energy: {qubo_result.energy:.1f}")
    print(f"Feasible allocation: {feasible}")
    print("\nAllocation")
    for workload, variable_names in zip(
        model.data.workloads, model.variables_by_workload, strict=True
    ):
        selected_gb = sum(
            allocation_bits[model.problem.variables_index[variable_name]]
            for variable_name in variable_names
        )
        allocated_gb = workload.minimum_ram_gb + selected_gb
        capacity_used += allocated_gb
        print(f"  {workload.name:10} {allocated_gb:2d} GB")

    print(f"\nRAM used: {capacity_used}/{model.data.capacity_gb} GB")
    print(f"QUBO utility: {utility:.1f}")
    print(f"Classical optimum: {reference.fval:.1f}")


if __name__ == "__main__":
    main()
