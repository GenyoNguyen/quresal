"""Data loading and binary allocation-model construction."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from qiskit_addon_opt_mapper import OptimizationProblem


@dataclass(frozen=True)
class Workload:
    """The baseline RAM requirement and utility of each additional GB."""

    name: str
    minimum_ram_gb: int
    incremental_utilities: tuple[int, ...]


@dataclass(frozen=True)
class AllocationData:
    """A single-server RAM allocation instance."""

    name: str
    capacity_gb: int
    workloads: tuple[Workload, ...]

    @property
    def minimum_allocation_gb(self) -> int:
        return sum(workload.minimum_ram_gb for workload in self.workloads)

    @property
    def additional_capacity_gb(self) -> int:
        return self.capacity_gb - self.minimum_allocation_gb


@dataclass(frozen=True)
class AllocationModel:
    """The constrained binary model before conversion to QUBO."""

    data: AllocationData
    problem: OptimizationProblem
    variables_by_workload: tuple[tuple[str, ...], ...]


def load_data(path: Path) -> AllocationData:
    """Load a RAM allocation instance from JSON."""
    raw_data = json.loads(path.read_text())
    workloads = tuple(
        Workload(
            name=workload["name"],
            minimum_ram_gb=workload["minimum_ram_gb"],
            incremental_utilities=tuple(workload["incremental_utilities"]),
        )
        for workload in raw_data["workloads"]
    )
    return AllocationData(
        name=raw_data["name"],
        capacity_gb=raw_data["capacity_gb"],
        workloads=workloads,
    )


def build_allocation_model(data: AllocationData) -> AllocationModel:
    """Build the binary additional-RAM allocation model.

    One binary variable represents one optional GB. The values in
    ``incremental_utilities`` are the utility gained by selecting that GB.
    """
    problem = OptimizationProblem(data.name)
    utility_by_variable: dict[str, int] = {}
    variables_by_workload: list[tuple[str, ...]] = []

    for workload_index, workload in enumerate(data.workloads):
        variable_names = []
        for increment_index, utility in enumerate(workload.incremental_utilities):
            variable_name = f"ram_{workload_index}_{increment_index}"
            problem.binary_var(variable_name)
            utility_by_variable[variable_name] = utility
            variable_names.append(variable_name)
        variables_by_workload.append(tuple(variable_names))

    problem.maximize(linear=utility_by_variable)
    problem.linear_constraint(
        linear={name: 1 for name in utility_by_variable},
        sense="<=",
        rhs=data.additional_capacity_gb,
        name="additional_ram_capacity",
    )

    return AllocationModel(
        data=data,
        problem=problem,
        variables_by_workload=tuple(variables_by_workload),
    )
