"""QUBO conversion and a compact simulated-annealing solver."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from qiskit_addon_opt_mapper.converters import OptimizationProblemToQubo

from .model import AllocationModel


@dataclass(frozen=True)
class QuboModel:
    """A QUBO produced from an allocation model by Qiskit's mapper."""

    allocation_model: AllocationModel
    converter: OptimizationProblemToQubo
    linear: np.ndarray
    quadratic: np.ndarray
    constant: float

    @property
    def number_of_variables(self) -> int:
        return len(self.linear)

    def energy(self, bits: np.ndarray) -> float:
        """Evaluate ``constant + linear @ bits + bits.T @ quadratic @ bits``."""
        return float(self.constant + self.linear @ bits + bits @ self.quadratic @ bits)


@dataclass(frozen=True)
class QuboResult:
    """The lowest-energy bit string found by simulated annealing."""

    bits: np.ndarray
    energy: float


def build_qubo(model: AllocationModel, penalty: float = 20.0) -> QuboModel:
    """Convert the constrained binary allocation model to an unconstrained QUBO."""
    converter = OptimizationProblemToQubo(penalty=penalty)
    qubo_problem = converter.convert(model.problem)
    return QuboModel(
        allocation_model=model,
        converter=converter,
        linear=np.asarray(qubo_problem.objective.linear.to_array()).reshape(-1),
        quadratic=np.asarray(qubo_problem.objective.quadratic.to_array()),
        constant=qubo_problem.objective.constant,
    )


def solve_qubo(
    qubo: QuboModel,
    reads: int = 256,
    sweeps: int = 2_000,
    seed: int = 7,
) -> QuboResult:
    """Minimize a small QUBO with deterministic, vectorized simulated annealing."""
    rng = np.random.default_rng(seed)
    variable_count = qubo.number_of_variables
    states = rng.integers(0, 2, size=(reads, variable_count), dtype=np.int8)
    energies = np.array([qubo.energy(state) for state in states])

    scale = max(np.abs(qubo.linear).max(), np.abs(qubo.quadratic).max(), 1.0)
    temperatures = np.geomspace(2 * scale, 0.01, num=sweeps)
    diagonal = np.diag(qubo.quadratic)
    rows = np.arange(reads)

    for temperature in temperatures:
        flips = rng.integers(variable_count, size=reads)
        directions = 1 - 2 * states[rows, flips]
        interactions = qubo.quadratic[flips] + qubo.quadratic[:, flips].T
        changes = directions * (
            qubo.linear[flips] + np.sum(interactions * states, axis=1)
        ) + diagonal[flips]
        accept = (changes <= 0) | (
            rng.random(reads) < np.exp(-changes / temperature)
        )
        accepted_rows = rows[accept]
        states[accepted_rows, flips[accept]] ^= 1
        energies[accept] += changes[accept]

    best_index = int(np.argmin(energies))
    return QuboResult(
        bits=states[best_index].copy(), energy=float(energies[best_index])
    )


def interpret_allocation(qubo: QuboModel, result: QuboResult) -> np.ndarray:
    """Map QUBO bits, including slack bits, back to allocation variables."""
    return np.rint(qubo.converter.interpret(result.bits)).astype(int)
