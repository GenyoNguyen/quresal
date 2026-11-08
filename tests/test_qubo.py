from pathlib import Path

import pytest
from qiskit_addon_opt_mapper.solvers import ScipyMilpSolver

from quresal.model import build_allocation_model, load_data
from quresal.qubo import (
    build_qubo,
    interpret_allocation,
    solve_qubo,
)

DATA_DIR = Path(__file__).parents[1] / "data"


@pytest.mark.parametrize(
    ("filename", "expected_variables", "expected_utility"),
    [
        ("ram_allocation_3x3.json", 9, 46),
        ("ram_allocation_5x5.json", 25, 58),
    ],
)
def test_datasets_have_expected_classical_optima(
    filename: str, expected_variables: int, expected_utility: int
) -> None:
    model = build_allocation_model(load_data(DATA_DIR / filename))
    result = ScipyMilpSolver().solve(model.problem)

    assert model.problem.get_num_vars() == expected_variables
    assert result.fval == expected_utility


@pytest.mark.parametrize(
    ("filename", "expected_utility"),
    [
        ("ram_allocation_3x3.json", 46),
        ("ram_allocation_5x5.json", 58),
    ],
)
def test_qubo_solution_is_feasible_and_optimal(
    filename: str, expected_utility: int
) -> None:
    model = build_allocation_model(load_data(DATA_DIR / filename))
    qubo = build_qubo(model)
    allocation = interpret_allocation(qubo, solve_qubo(qubo))

    feasible, _, _ = model.problem.get_feasibility_info(allocation)
    assert feasible
    assert model.problem.objective.evaluate(allocation) == expected_utility
