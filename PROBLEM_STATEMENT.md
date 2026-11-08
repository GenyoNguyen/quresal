# Continuous RAM Resource Allocation in a Small Computing Cluster

This document distinguishes the resource-allocation problem from the
technical formulation and the plan for evaluating a QAOA implementation.

## 1. Problem Statement

Resource allocation is the process of distributing limited computing
resources among competing workloads. This project studies **RAM
allocation in a small computing server**, where several workloads share
a fixed physical-memory capacity.

A workload may represent a web server, database, data-analytics job, or
caching service. Each workload benefits from receiving RAM, but the
benefit is not necessarily proportional to the amount allocated. In
general, additional memory is most valuable when a workload is
memory-constrained; its marginal benefit tends to decrease as more
memory is assigned.

The objective is to determine how much RAM to allocate to each workload
so that the total system utility is maximized while respecting the
server's memory capacity and each workload's allocation limits.

This is a divisible-resource allocation problem: RAM may be shared among
workloads rather than assigning each workload as a whole to one machine.
The problem is intentionally limited to a single server with a fixed
capacity and known workloads.

## 2. Initial Scenario

Consider a server with **32 GB of RAM available for allocation**. It
hosts four workloads:

  Workload           Minimum RAM (GB)   Maximum useful RAM (GB) Priority
  ---------------- ------------------ ------------------------- -----------
  Web server                        4                        10 High
  Database                          8                        16 Very high
  Data analytics                    6                        14 Medium
  Cache service                     2                         8 Low
  **Total**                    **20**                    **48** 

The minimum requirements sum to 20 GB, so the instance is feasible and
leaves 12 GB for additional allocation. The sum of the maximum useful
allocations is 48 GB, which exceeds the server capacity. Therefore, not
every workload can receive its maximum useful allocation.

The priority labels are qualitative descriptions for the scenario. They
should not be used directly as numerical coefficients until a
quantitative utility model has been specified.

### 2.1 Workload interpretation

-   **Web server:** Additional RAM can support more concurrent requests
    and reduce memory pressure.
-   **Database:** Additional RAM can improve query performance by
    keeping more frequently accessed data and indexes in memory.
-   **Data analytics:** Additional RAM can allow larger portions of a
    dataset to be processed in memory and reduce disk access.
-   **Cache service:** Additional RAM can increase the cache hit rate,
    although the benefit generally diminishes as the cache grows.

These are illustrative assumptions. A real deployment would estimate
utility from measurements, workload profiles, or a performance model.

## 3. Technical Formulation

The allocation is continuous in the conceptual model. A QUBO
implementation must represent it at a selected finite granularity, such
as 1 GB or 0.5 GB. The following formulation defines that translation.

Let:

-   \(N\) be the number of workloads.
-   \(C\) be the server's available RAM capacity, in GB.
-   (x_i) be the RAM allocated to workload (i), in GB.
-   (m_i) be the minimum RAM requirement of workload (i).
-   (M_i) be the maximum useful RAM allocation of workload (i).
-   (U_i(x_i)) be the utility obtained by allocating (x_i) GB to
    workload (i).

The initial optimization problem is:

\[
```{=tex}
\begin{aligned}
\max_{x_1,\ldots,x_N}\quad
    & \sum_{i=1}^{N} U_i(x_i) \\
\text{subject to}\quad
    & \sum_{i=1}^{N} x_i \le C, \\
    & m_i \le x_i \le M_i,\quad i=1,\ldots,N.
\end{aligned}
```
\]

The lower and upper bounds ensure that each workload receives at least
its minimum requirement and no more than its maximum useful allocation.
Non-negativity is already implied when (m_i `\ge 0`{=tex}).

For the example scenario:

\[ C=32 \]

and the allocation bounds are:

\[ 4`\le `{=tex}x\_{`\text{web}`{=tex}}`\le10`{=tex}, \]

\[ 8`\le `{=tex}x\_{`\text{database}`{=tex}}`\le16`{=tex}, \]

\[ 6`\le `{=tex}x\_{`\text{analytics}`{=tex}}`\le14`{=tex}, \]

\[ 2`\le `{=tex}x\_{`\text{cache}`{=tex}}`\le8`{=tex}. \]

The capacity constraint is:

\[ x\_{`\text{web}`{=tex}}+x\_{`\text{database}`{=tex}}+
x\_{`\text{analytics}`{=tex}}+x\_{`\text{cache}`{=tex}}`\le32`{=tex}. \]

### 3.1 Why maximize utility?

The objective should represent the system's benefit from the allocation,
rather than simply maximizing the amount of RAM distributed. The server
has a fixed capacity, and allocating more memory to one workload means
less memory is available to others.

A useful starting assumption is **diminishing marginal utility**: each
additional unit of RAM provides no more benefit than the previous unit.
This captures the idea that a workload's first few additional gigabytes
may be more valuable than later ones.

One possible model is a piecewise-linear utility function. For example,
suppose the database receives its required minimum of 8 GB. Its
additional-memory utility could be defined as:

\[ U\_{`\text{database}`{=tex}}(x)=
```{=tex}
\begin{cases}
10(x-8), & 8\le x\le12,\\
40+6(x-12), & 12 < x\le16.
\end{cases}
```
\]

The first 4 GB above the minimum provide 10 utility units per GB; the
next 4 GB provide 6 utility units per GB. The utility is continuous at
12 GB, and the marginal benefit decreases after that point.

This is an illustrative utility curve, not an empirical claim about
database performance. Equivalent curves must be defined for the other
workloads before the complete instance can be solved.

### 3.2 A note on priority

Priority can be incorporated into the utility model, for example by
scaling a workload's utility or its marginal utility. However, priority
should not be added as an arbitrary bonus without defining what it
means. A high-priority workload might receive greater utility weight, a
stronger minimum guarantee, or a service-level constraint. These choices
represent different policies and can produce different allocations.

### 3.3 From the Allocation Model to QUBO

A standard QUBO model uses binary decision variables. It cannot
represent arbitrary real-valued allocations directly. The continuous
allocation model must therefore be discretized for the QUBO experiment.

Choose an allocation granularity (`\Delta`{=tex}), measured in GB. For
workload (i), define:

\[ K_i=`\frac{M_i-m_i}{\Delta}`{=tex}, \]

assuming the range is divisible by (`\Delta`{=tex}). Let
(b\_{ij}`\in`{=tex}{0,1}) indicate whether the (j)-th additional memory
increment is assigned to workload (i). Then:

\[ x_i=m_i+`\Delta`{=tex}`\sum`{=tex}*{j=1}\^{K_i}b*{ij}. \]

For the initial experiment, choose (`\Delta=1`{=tex}) GB. The number of
optional binary variables is:

  Workload           Optional 1 GB increments
  ---------------- --------------------------
  Web server                                6
  Database                                  8
  Data analytics                            8
  Cache service                             6
  **Total**                            **28**

The 20 GB of minimum allocation is fixed, so the binary variables
represent the remaining allocation decisions. The server has 12 GB of
capacity remaining after minimum requirements are met.

The capacity constraint becomes:

\[ `\Delta`{=tex}`\sum`{=tex}*{i=1}\^{N}`\sum`{=tex}*{j=1}\^{K_i}b\_{ij}
`\le`{=tex} C-`\sum`{=tex}\_{i=1}\^{N}m_i. \]

For this example, with (`\Delta=1`{=tex}):

\[ `\sum`{=tex}*{i,j}b*{ij}`\le12`{=tex}. \]

The utility function must also be expressed in terms of the binary
increments. For a piecewise-linear utility with non-increasing marginal
gains, the utility can be represented as a sum of incremental gains:

\[ U_i(x_i)= `\sum`{=tex}*{j=1}\^{K_i}g*{ij}b\_{ij}, \]

where (g\_{ij}) is the utility gained by assigning the (j)-th additional
increment to workload (i). The increments should be ordered so that
earlier increments have at least as much marginal utility as later
increments.

This gives a binary optimization objective:

\[ `\max`{=tex}*{`\mathbf `{=tex}b}
`\sum`{=tex}*{i=1}\^{N}`\sum`{=tex}*{j=1}\^{K_i}g*{ij}b\_{ij} \]

subject to the binary capacity constraint above.

To express this as a QUBO, the inequality constraint must be handled
using a suitable penalty construction, such as a slack-variable
encoding. The resulting unconstrained binary objective has the general
form:

\[
`\min`{=tex}\_{`\mathbf `{=tex}z} `\mathbf `{=tex}z\^`\mathsf{T}`{=tex}Q`\mathbf `{=tex}z,
\]

where (`\mathbf `{=tex}z) contains the allocation variables and any
auxiliary slack bits. The sign of the utility term must be reversed
because the original problem is a maximization problem. The penalty
coefficient must be chosen large enough to discourage infeasible
allocations without making the optimization numerically ill-conditioned.

**Important modeling detail:** The binary variables above are optional
increments, not independent choices of arbitrary memory blocks. If the
marginal gains are ordered from highest to lowest, an optimal solution
to this particular capacity-allocation model will naturally prefer
higher-value increments first. If the model includes other constraints
or non-concave utility curves, explicit precedence constraints may be
needed to prevent selecting a later increment without selecting an
earlier one.

## 4. Research Plan

### 4.1 Research objective

The central research question is:

> How effectively can QAOA solve a discretized RAM resource-allocation
> problem, compared with classical optimization methods, in terms of
> solution quality, feasibility, computational cost, and scalability?

The work proceeds through the following stages:

1.  Define a resource-allocation scenario and specify workload
    requirements.
2.  Construct utility functions with a clear interpretation and, where
    possible, empirical justification.
3.  Formulate the constrained allocation problem mathematically.
4.  Discretize the allocation variables and derive the binary
    optimization model.
5.  Convert the constrained binary model into a QUBO, carefully
    designing and validating penalty terms.
6.  Map the QUBO to an Ising Hamiltonian and implement QAOA using
    Qiskit.
7.  Compare QAOA against exact and heuristic classical baselines.
8.  Study how allocation granularity and problem size affect solution
    quality and computational cost.

The first milestone is a correct classical solution to the discretized
model. Once the objective, constraints, and optimal allocation have been
independently verified, the same model can be encoded as a QUBO and used
for the quantum experiments.

### 4.2 Evaluation and baselines

The QAOA solution should be compared with classical methods on exactly
the same discretized problem and utility function.

Recommended baselines are:

1.  **Exact classical optimizer:** Solve the discrete allocation problem
    to obtain an optimal reference solution. For this small instance,
    exhaustive search, dynamic programming, or a suitable
    mathematical-optimization solver may be practical.
2.  **Greedy marginal-utility allocation:** Repeatedly assign the next
    available RAM increment with the highest marginal utility, until the
    remaining capacity is exhausted or no useful increment remains.
3.  **QAOA:** Encode the discrete model as a QUBO/Ising problem and
    evaluate the quality of sampled solutions.

First-Fit and Best-Fit Decreasing are primarily bin-packing or placement
heuristics. They are not direct baselines for this divisible-resource
utility-maximization problem unless the research question is changed to
include indivisible tasks or placement decisions. For the present
scenario, an exact solver and a greedy marginal-utility method are more
meaningful comparisons.

Useful evaluation metrics include:

-   **Total utility:** The objective value achieved by an allocation.
-   **Optimality gap:** The difference between the QAOA result and the
    exact optimum, reported with a clearly stated normalization.
-   **Feasibility rate:** The fraction of sampled solutions that satisfy
    all constraints.
-   **RAM utilization:** The fraction of available memory allocated.
-   **Runtime:** Report problem construction, classical optimization,
    circuit execution, and post-processing separately where possible.
-   **Scalability:** Repeat experiments with more workloads, larger
    capacity, and finer allocation granularity.

For stochastic QAOA runs, report results across multiple random seeds or
independent runs. Distinguish the best observed sample from average
performance.

### 4.3 Initial experimental configuration

  -----------------------------------------------------------------------
  Parameter                           Initial value
  ----------------------------------- -----------------------------------
  Server RAM capacity                 32 GB

  Number of workloads                 4

  Minimum total allocation            20 GB

  Remaining allocatable RAM           12 GB

  Allocation granularity              1 GB

  Optional allocation bits            28

  Utility model                       Piecewise-linear, diminishing
                                      marginal utility

  Quantum algorithm                   QAOA

  Quantum simulation                  Qiskit Aer

  Classical references                Exact solver and greedy
                                      marginal-utility allocation
  -----------------------------------------------------------------------

Start with this small, static, single-server scenario. Do not introduce
multiple servers, task migration, workload arrivals, or time-varying
demands in the first experiment. Those extensions add modeling decisions
that can obscure whether the initial QUBO formulation is correct.

### 4.4 Scope and assumptions

The initial model deliberately makes several simplifying assumptions:

-   The server's usable RAM capacity is known and fixed.
-   All workloads are known before allocation.
-   Each workload has a minimum and maximum useful RAM allocation.
-   RAM is divisible at the selected allocation granularity.
-   Workload utility is additive: the total utility is the sum of
    individual workload utilities.
-   Workload utilities are known and do not depend on the allocation of
    other workloads.
-   The model does not account for operating-system overhead, memory
    fragmentation, swapping, or dynamic changes in demand.

These assumptions define a controlled baseline rather than a complete
production memory manager. They can be relaxed in later experiments if
the initial model and its QUBO encoding are validated.

