# Pain points raised by users of PyPSA, PyPSA-Eur and linopy (2021–2026)

Scope note on sources. Evidence is GitHub issues and PRs on PyPSA/PyPSA, PyPSA/pypsa-eur and PyPSA/linopy, read through the GitHub search API and github.com pages on 2026-11-18. Each item gives the filing date and the author's GitHub association: NONE or CONTRIBUTOR means an outside user; COLLABORATOR or MEMBER means a maintainer. Many 2026 linopy issues are maintainer-filed and several say they were AI-drafted. They are good evidence of a defect class but weak evidence of a user complaint, and they are labelled that way below. The PyPSA Google group (groups.google.com) and forum.openmod.org could not be fetched from this session because the network blocked them. A few Google group items appear only as search-engine summaries and are marked so.

Conflict-of-interest flag: as of Oct–Nov 2026, PyPSA and linopy maintainers are building a "mathspec-backed `linopy.spec`" ([linopy #561 closing comment, 2026-10-30](https://github.com/PyPSA/linopy/issues/561#issuecomment-6520819726); [PyPSA #2138, 2026-11-13](https://github.com/PyPSA/PyPSA/issues/2138)). Those threads are about the product itself, so they are not independent user demand.

## 1. Model build time and memory

### Takeaway
Memory, not solver time alone, is the complaint that recurs at PyPSA-Eur scale. The causes users name are dense xarray arrays for sparse models, the in-memory footprint linopy keeps beside the solver during a solve, and file handoff overhead. Build time becomes the main cost for iterative workflows (MGA, rolling horizon, sweeps) because the model is rebuilt each time.

### Cited Findings
- Sparsity is a blocker for some users: "a linear expression is composed of the sum of only 0.1% of the coordinates of an xarray. Not supporting sparsity hence would increase our model size by ~900x. This effectively prohibits us from using Linopy as is." (2024-03-07, @staadecker, outside contributor) — [linopy #248](https://github.com/PyPSA/linopy/issues/248)
- The same user found the fix invasive because "`xarray` is still developing support for `sparse`" (2024-03-08) — [linopy #248 comment](https://github.com/PyPSA/linopy/issues/248#issuecomment-1985043708)
- A PyPSA-Eur user ties memory to dense xarray: "the non-sparse nature of xarray is also impacting the memory footprint of solving pypsa-eur networks" (35 clusters, 3000 time steps, myopic, 2024-04-19, @koen-vg) — [linopy #248 comment](https://github.com/PyPSA/linopy/issues/248#issuecomment-2066113554)
- A maintainer concedes that "Memory spikes in the building phase seem to be a recurring issue" and that "New versions of xarray sometimes cause memory leaks" (2024-04-19, @fneum, MEMBER) — [linopy #248 comment](https://github.com/PyPSA/linopy/issues/248#issuecomment-2066136914). The user then asks which xarray version or "whole software environment" gave the low footprint, so reproducibility and memory interact — [same thread](https://github.com/PyPSA/linopy/issues/248#issuecomment-2066174016)
- Maintainer measurement: "for a 112 GB peak memory example solving, 31 GB was held by linopy and 81 GB by gurobi" (2024-01-18, @FabianHofmann, COLLABORATOR) — [linopy #219](https://github.com/PyPSA/linopy/issues/219)
- File handoff costs memory: "passing an LP to the solver (Gurobi in this case) using the .mps format has a significant memory overhead … you should use the .lp io interface for the moment if you care about memory." (2024-03-28, @koen-vg, NONE) — [linopy #261](https://github.com/PyPSA/linopy/issues/261)
- PyPSA-Eur preprocessing is also heavy: "the `build_line_rating` rule seems to use tens of GBs of memory, and takes a really long time (I didn't get it to complete)" (2024-10-03, @koen-vg) — [pypsa-eur #1346](https://github.com/PyPSA/pypsa-eur/issues/1346)
- A third-party benchmark that a user brought to linopy: at N=3000 (~18M variables), building took 300 s and 23.7 GB peak in linopy (`io_api="lp"`), against 87 s and 16.4 GB in polar-high, a polars-backed eDSL on HiGHS (2026-06-02, @MaykThewessen, outside contributor) — [linopy #740](https://github.com/PyPSA/linopy/issues/740). This directly supports a "polars-based, fast builds" pitch. The numbers are polar-high's own and were not re-run here.
- "For production workloads (120+ buses, 8760h, scenario sweeps), the model building step is the dominant bottleneck. This is especially painful for iterative workflows like MGA, rolling horizon, and sensitivity analysis where the model is rebuilt many times." (2026-03-02, @MaykThewessen) — [linopy #599](https://github.com/PyPSA/linopy/issues/599). The same issue cites profiling where matrix construction was "55% of total solve time (8s out of 14.5s)". The speedup table in that issue is marked as estimates, not measurements.
- Re-solving without a rebuild: "I have a PyPSA model which takes about 50 seconds to solve using highs. I want to solve this model many time with different costs" (2023-11-09, @dannyopts) — [linopy #198](https://github.com/PyPSA/linopy/issues/198). Maintainer framing: "Today every `Model.solve()` rebuilds the native solver model from scratch … For large models the build dominates total wall-clock." (2026-05-19, COLLABORATOR) — [linopy #699](https://github.com/PyPSA/linopy/issues/699)
- Historical context: linopy was pitched as faster and leaner than Pyomo. The announcement claimed "speedup of times 4-7" and about 50% memory reduction above a million variables, and on a 37-node PyPSA network about 60% of Pyomo's memory and 20% of its time. This comes from a search-engine summary of the 2022 openmod mailing-list post, which could not be fetched — [openmod group](https://groups.google.com/g/openmod-initiative/c/_hbH-c8dotU). The JOSS paper says linopy "outperforms all Python AMLs in memory efficiency" and is close to CVXPY and gurobipy in speed (search summary) — [JOSS 2023](https://joss.theoj.org/papers/10.21105/joss.04823.pdf)
- Hardware expectations: a PyPSA-Eur fork's README says sector-coupled solves need at least 32 GB for a two-country test and at least 64 GB for the full model (search summary) — [pypsa-eur_RFNBO](https://github.com/IntSusEnergySystems/pypsa-eur_RFNBO). An older Google group thread reports about 6 h and 32 GB for 100 nodes at 2-hourly resolution (2019-era, search summary only) — [pypsa group "pypsa-eur system requierements"](https://groups.google.com/g/pypsa/c/-gG6mf16TiA)
- The solver can run out of memory after infeasibility: a Gurobi community post shows a PyPSA-Eur user hitting `GurobiError: Out of memory` in the IIS step that runs after an infeasible result (search summary) — [Gurobi community](https://support.gurobi.com/hc/ja/community/posts/43368014235409-Please-help-me-gurobipy-exception-GurobiError-Out-of-memory)

### Inferences
- Candidate new theme, "sparse by nature": energy models are sparse (technology × node × carrier), and dense labelled arrays make users pay for the empty cells. A long-format tables-in engine answers the ~900x complaint directly.
- Candidate new theme, "rebuild cost multiplies": users feel build time most in loops (MGA, sweeps, rolling horizon), so a pitch about sweeps and fast builds should frame speed as per scenario × number of scenarios.

### Gaps
- No verbatim "MemoryError" or "takes hours to build" user quote was found in GitHub issues. Such reports probably live on the Google group, which was blocked here.

## 2. Custom constraints (extra_functionality): internals, upgrades, persistence, alignment

### Takeaway
`extra_functionality` is a Python callback that reaches into linopy internals. It breaks across upgrades and is lost when a network is saved. It is dropped or misapplied in rolling-horizon solves, and maintainers themselves call reserve-style custom constraints too hard for "non-proficient users". Underneath it, linopy's coordinate alignment has produced silently wrong models.

### Cited Findings
- Examples broke when the backend changed: running the custom-constraint example with `pyomo=False` gives "an Attribute error" (2022-11-16, @oorishko). Maintainer: "The power-to-gas-boiler examples were still written for pyomo and `network.model` there referred to the pyomo `Model`." — [PyPSA #498](https://github.com/PyPSA/PyPSA/issues/498)
- A migration error: `create_model(multi_investment_periods=True)` raises an error "wich worked up to 0.35" after moving to PyPSA 1.0 (2026-01-29, @Tooblippe) — [PyPSA #1541](https://github.com/PyPSA/PyPSA/issues/1541)
- Custom constraints are not part of the saved model. The request dates from 2021: "Custom constraint and their duals should become a officially supported part of the data model with IO functionality." (2021-12-09, still open) — [PyPSA #322](https://github.com/PyPSA/PyPSA/issues/322)
- "When defining custom constraints via `extra_functionality` in e.g. PyPSA-Eur, additional data is added to the linopy model that the pypsa network object never sees … land use constraints exist over component `carrier` + `bus`" (2026-10-16, @brynpickering, COLLABORATOR) — [PyPSA #2014](https://github.com/PyPSA/PyPSA/issues/2014)
- A maintainer wants text math so that custom constraints become "declarative (and thus persistable within a saved network) rather than providing only a callback function" (2026-01-30, @coroa, MEMBER) — [linopy #561 comment](https://github.com/PyPSA/linopy/issues/561#issuecomment-3822631204)
- The original YAML-math ask: "define all the mathematics of a linopy model in human-readable text format. This would help with transparency and shareability … making it easier to define new math without needing to be so familiar with Python." (2026-01-28, @brynpickering, of Calliope) — [linopy #561](https://github.com/PyPSA/linopy/issues/561)
- Reserve constraints "go deep into the logic about creating custom linopy variables updating existing constraints and correctly registering indices … Non-proficient users are therefore very much left out" (2026-06-15, maintainer) — [PyPSA #1729](https://github.com/PyPSA/PyPSA/issues/1729)
- Rolling horizon drops custom constraints: "Custom constraints are not applied when the operational model is solved." (2026-11-18, nick-gorman, Open-ISP/ISPyPSA) — [ISPyPSA #166](https://github.com/Open-ISP/ISPyPSA/issues/166). A Google group thread reports the same, and the maintainer said the callback "should not call create_model, that is done for you within the optimize_with_rolling_horizon function" (search summary) — [pypsa group](https://groups.google.com/g/pypsa/c/cU24t8kMUEk)
- Silent misalignment from users:
  - "BUG: silently map wind to pv and two to one instead of taking the union" when adding two variables with same-size but different labels (2026-05-02, @sdementen, NONE) — [linopy #670](https://github.com/PyPSA/linopy/issues/670)
  - A user who could not express a per-day cyclic shift: "assignment does not seem to work … My fallback solution would be to create single constraints per point in time" (2024-03-12, @apfelix) — [linopy #256](https://github.com/PyPSA/linopy/issues/256)
  - "I am currently struggling with xarray and linopy" over grouping a dimension by an auxiliary coordinate: "In the end I made B full dimension … instead of having small dimensional case of 7 dimensions I will end with at least 9" (2024-05-24, @aurelije) — [linopy #295](https://github.com/PyPSA/linopy/issues/295)
- Maintainer catalogue of the same class: "linopy aligns coordinates with size-based heuristics. When operands don't line up it guesses, and the guesses are sometimes **silently wrong** — no exception, the solver returns `Optimal`, the objective looks plausible." It cites a PyPSA workaround for "a capacity-expansion result 47% too cheap" (2026-05-21, @FBumann, COLLABORATOR) — [linopy #714](https://github.com/PyPSA/linopy/issues/714)
- "`*` by label, `+` `-` `/` by position … algebraically identical expressions produce different results" (2026-05-21, maintainer) — [linopy #708](https://github.com/PyPSA/linopy/issues/708). A pandas bound missing a dimension silently drops that dimension from the variable (maintainer) — [linopy #709](https://github.com/PyPSA/linopy/issues/709)
- The 47% case: in PyPSA 1.2's ramp-limit constraint, "xarray's outer-join alignment quietly re-sorts the result's `name` axis alphabetically" and rows were paired by position, so an illustrative model "reports an annual system cost 47% below the constraint-respecting answer". The 47% is the PR author's illustrative scenario, not a production measurement (PR merged 2026-05-18) — [PyPSA #1677](https://github.com/PyPSA/PyPSA/pull/1677)

### Inferences
- Candidate new theme, "custom math that survives a save": a constraint written as data stays with the model; a callback does not. This is distinct from "extending without forking".
- Candidate new theme, "no silent Optimal": alignment and NaN rules that guess are the users' fear, and load-time rejection of a dimension mismatch is a direct answer. Strong evidence also for the covered theme "checking a model before data".

### Gaps
- Google group threads on `extra_functionality` ("Efficient addition von custom constraints", "Contraint Values – Extra functionality") could not be read verbatim.

## 3. Finding and reading the math PyPSA solves; docs vs code

### Takeaway
Users find the meaning of a constraint by reading code, and several reports are docs/code or intuition/code mismatches in units and scopes. These include standby cost, CO2 limits over multiple years, carriers in operational limits, and `s_nom_max` in losses.

### Cited Findings
- Docs say one thing and code another. The docs describe standby cost as "Stand-by cost for operating the generator at null power output", but "The code on the other hand is: `status * stand_by_cost` … which seems to give cost to the Generator once it's running" (2024-04-15, @Cellophil) — [PyPSA #864](https://github.com/PyPSA/PyPSA/issues/864)
- "The CO2 limit via global constraints more or less silently multiplies by the number of years that it stands for. While not really a bug and somewhat supported by the docs it's maybe a bit confusing." (2026-11-17, @Andreas-naut, NONE) — [PyPSA #2169](https://github.com/PyPSA/PyPSA/issues/2169)
- "In the global constraint for the operational limit, for stores we do not consider the carrier of the store itself, but the carrier of the bus", found by reading `global_constraints.py` (2024-09-06, @p-glaum) — [PyPSA #1024](https://github.com/PyPSA/PyPSA/issues/1024)
- "For expandable lines PyPSA uses s_nom_max, instead of s_nom or `s_nom_opt` for the line losses. Thus … the result may change when `s_nom_max` changes" (2025-08-11, @lindnemi) — [PyPSA #1320](https://github.com/PyPSA/PyPSA/issues/1320)
- Semantic confusion from modelling demand as a negative generator: users ask "should I touch change the `sign` attribute or `p_min_pu`/`p_max_pu`?" and "why are they called generators then?" (2026-06-16, maintainer reporting users) — [PyPSA #1736](https://github.com/PyPSA/PyPSA/issues/1736)
- Ramp limits in multi-horizon models apply to the first snapshot for some generators and not for others, found by inspecting results (2023-11-28, @PeterKlein11) — [PyPSA #791](https://github.com/PyPSA/PyPSA/issues/791)

### Inferences
- These support the covered theme "published math equals solved math". The new angle is units and scope: per-year vs per-period, which carrier, which capacity. A typeset spec with declared dimensions and units makes these visible.

### Gaps
- No issue was found in which a user says outright "the documentation equations differ from the implementation" in those words. The cases above are concrete instances, not a general complaint.

## 4. Debugging infeasible, unbounded or numerically troubled models

### Takeaway
Beginners and experienced PyPSA-Eur users both struggle to find why a model is infeasible. The usual cause is bad input data (NaN, inf, near-zero potential) that surfaces only at solve time, and the tool support is thin: IIS per solver, no network diff, no soft constraints.

### Cited Findings
- "Even if AC is used as carrier, beginners could get infeasible solutions that are hard to handle for them … Would be great if PyPSA could give some hint why the solution is infeasible" (2024-11-28, @fhg-isi, NONE; Fraunhofer ISI account). Maintainer: "Improving consistency warnings next to docs is on the list." — [PyPSA #1094](https://github.com/PyPSA/PyPSA/issues/1094)
- Bad data shows up only as infeasibility. "The coke demand for NL is inf leading to an infeasible solution. The proximate cause is infinite values in the resource industry_sector_ratios" (2024-08-20, @Timon-R) — [pypsa-eur #1226](https://github.com/PyPSA/pypsa-eur/issues/1226). Default model, 39 nodes, 6H: "get an infeasible model" (2024-12-19) — [pypsa-eur #1463](https://github.com/PyPSA/pypsa-eur/issues/1463)
- "since several weeks I experience numerical issues in my pypsa-eur model. At first I assumed them to be related to my specific changes, but they are remaining even after cutting those changes back" (2025-08-30, @MaikSa2, NONE) — [pypsa-eur #1819](https://github.com/PyPSA/pypsa-eur/issues/1819)
- "The optimization is failing due to infeasibility. I am using custom constraints for the agg_p_nom_minmax, and the infeasibility occurs due to very low calculated wind potential" (2026-02-05, NONE) — [pypsa-eur #2039](https://github.com/PyPSA/pypsa-eur/issues/2039). Corsica is infeasible at NUTS-2 but feasible at bidding-zone level (2026-02-04) — [pypsa-eur #2038](https://github.com/PyPSA/pypsa-eur/issues/2038)
- Users diff networks by hand: a request for "a function that would allow for an easy comparison of networks … for finding issues with networks when they e.g. suddenly become inexplicably infeasible to solve. I'm currently utilising default `pandas` functionality" (2026-03-20, @euronion) — [PyPSA #1627](https://github.com/PyPSA/PyPSA/issues/1627)
- Silent NaN in data: "Silent NaN load data when using fixed_year with snapshots from a different year" (2026-06-04, @luciboon) — [pypsa-eur #2187](https://github.com/PyPSA/pypsa-eur/issues/2187). `cluster_heat_buses` "silently sets p_set=0.0 … via NaN-summing aggregation" (2026-05-30, NONE) — [pypsa-eur #2182](https://github.com/PyPSA/pypsa-eur/issues/2182)
- Maintainers acknowledge the gaps. "Users often build large models and have limited visibility into why solves are slow or produce unexpected results" (2026-04-07) — [linopy #645](https://github.com/PyPSA/linopy/issues/645). There is no generic soft-constraint mechanism, which would help with "debugging an infeasible model" (2026-06-15) — [PyPSA #1732](https://github.com/PyPSA/PyPSA/issues/1732). IIS is missing for COPT — [linopy #358](https://github.com/PyPSA/linopy/issues/358)
- Maintainer-filed, AI-drafted reports of rows dropped silently: "`0 >= 5` solves 'optimal'" with "No warning" (2026-11-18) — [linopy #1170](https://github.com/PyPSA/linopy/issues/1170). `update(rhs=nan)` leaves a row "solvers silently ignore" — [linopy #1181](https://github.com/PyPSA/linopy/issues/1181)

### Inferences
- Candidate new theme, "infeasible is a data bug": most infeasibility reports trace to NaN, inf or zero in the data, not to the math. A data-free spec checked at load, followed by a data check against declared domains before the build, splits "math wrong" from "data wrong". Specsolve's archived inputs make the comparison by diff that #1627 asks for possible.

### Gaps
- No direct user thread on reading duals or shadow prices for custom constraints in linopy was found, beyond #322's request that duals be part of the data model.

## 5. Reproducibility, upgrades, scenarios and storing results

### Takeaway
Upgrades change results, some code paths are non-deterministic, and results are multi-GB netCDF files compared by hand-written pandas. Scenario management in PyPSA-Eur conflicts with several scripts.

### Cited Findings
- "We recently migrated to `PyPSA 1.2 (from 0.35)` and observed a delta in the solved model results." It was resolved in 1.2.1 (2026-05-19, @Tooblippe, outside contributor) — [PyPSA #1681](https://github.com/PyPSA/PyPSA/issues/1681)
- Non-determinism: the default cycle basis "returns a different cycle matrix `C` for each Python string-hash seed … per-unit and per-line results moved by more than 0.5 % between ident[ical runs]" (2026-10-20, maintainer, AI-drafted) — [PyPSA #2022](https://github.com/PyPSA/PyPSA/issues/2022). "Make simplification of network deterministic" (2026-03-19) — [pypsa-eur #2124](https://github.com/PyPSA/pypsa-eur/issues/2124)
- Result storage and comparison: "PyPSA stores results in netCDF files. Comparing scenarios requires loading multiple multi-GB files into memory and writing custom pandas code for every query … a bottleneck for production workflows (trading desks, dispatch scheduling, automated reporting)" (2026-03-02, @MaykThewessen) — [PyPSA #1590](https://github.com/PyPSA/PyPSA/issues/1590)
- Scenario management breaks scripts: "`make_global_summaries` not compatible with scenario management" (2026-02-26) — [pypsa-eur #2104](https://github.com/PyPSA/pypsa-eur/issues/2104); "prepare_sector_network incompatible with using scenarios" (2026-07-14) — [pypsa-eur #2234](https://github.com/PyPSA/pypsa-eur/issues/2234)
- Myopic runs: "cost assignment(s) might not update in myopic optimisation" (2025-11-24) — [pypsa-eur #1922](https://github.com/PyPSA/pypsa-eur/issues/1922); existing capacities "are added twice" with myopic foresight (2024-04-11, @koen-vg) — [pypsa-eur #1016](https://github.com/PyPSA/pypsa-eur/issues/1016)
- Breaking changes are planned. A maintainer meta-issue lists "Text math | Global constraints, ad-hoc custom constraint approach" among the v2 breaks (2026-07-23, MEMBER) — [PyPSA #1835](https://github.com/PyPSA/PyPSA/issues/1835)

### Inferences
- Candidate new theme, "rerun last year's study": an archive that holds the spec, inputs and answer together, with a layout version that refuses a stale file by name, answers #1681, #2022 and #1590 as one story.
- Candidate new theme, "query results as tables": scenario comparison is the production user's complaint (#1590). Parquet catalogs across a sweep fit it directly.

### Gaps
- No public user thread was found about failing to reproduce a published PyPSA-Eur paper's numbers. Such reports may exist on the Google group.

## 6. Rolling horizon and multi-window semantics

### Takeaway
New in 2026: a cluster of reports that global limits and custom constraints are wrong under `optimize_with_rolling_horizon`. Caps are re-applied per window, minimums are multiplied, overlaps are double counted, and infeasible windows are dropped silently.

### Cited Findings
- "With a primary_energy CO2 GlobalConstraint of 100 … Running optimize_with_rolling_horizon(horizon=1) on the same data emits 200: each window receives the full cap again." (2026-11-01, outside user, AI-assisted report) — [PyPSA #2067](https://github.com/PyPSA/PyPSA/issues/2067)
- "`e_sum_min` is applied per-window, multiplying the intended requirement … a silent footgun" (2026-06-30, @MaykThewessen) — [PyPSA #1769](https://github.com/PyPSA/PyPSA/issues/1769). Overlap snapshots are double counted — [PyPSA #2073](https://github.com/PyPSA/PyPSA/issues/2073). Out-of-order windows "read zero-filled outputs of unsolved snapshots as history" — [PyPSA #1995](https://github.com/PyPSA/PyPSA/issues/1995)
- Unit commitment with rolling horizon: "The previous window SEES the outage and plans the shutdown correctly. Yet the seam constraint st[ill fails]" (2026-04-01, @kennethfungch, NONE) — [PyPSA #1644](https://github.com/PyPSA/PyPSA/issues/1644)
- Speed: "Faster rolling horizon with persistent solver instances" (2026-03-24) — [PyPSA #1634](https://github.com/PyPSA/PyPSA/issues/1634). Maintainer-filed: "WindowModel.solve silently ignores infeasible windows" — [linopy #1109](https://github.com/PyPSA/linopy/issues/1109)
- Custom constraints dropped in rolling horizon — [ISPyPSA #166](https://github.com/Open-ISP/ISPyPSA/issues/166)

### Inferences
- Candidate new theme, "a horizon that keeps its budget": specsolve's rolling horizon could claim that period-wide limits carry across windows by construction. Only claim it if verified.

### Gaps
- None beyond verification of the specsolve claim, which is outside this research.

## 7. Solvers: support, file vs direct interfaces, solver-specific issues

### Takeaway
Users hit solver-specific failures: the CPLEX fork crash, SCIP rejecting quadratic problems, Gurobi memory with MPS, licences. File and direct paths can give different models.

### Cited Findings
- "solving a large pypsa network with cplex … use of fork() may lead to deadlocks in the child. Afterwards, the script crashes" (2025-11-18, @thomgeo) — [pypsa-eur #1906](https://github.com/PyPSA/pypsa-eur/issues/1906); "cplex issue sector_model pypsa 1.0.6" (2026-01-09) — [pypsa-eur #1964](https://github.com/PyPSA/pypsa-eur/issues/1964)
- The electricity-only example fails with HiGHS and SCIP: "Solver scip does not support quadratic problems" (2026-02-24) — [pypsa-eur #2092](https://github.com/PyPSA/pypsa-eur/issues/2092); "Optimization problem with HIGHS" (2025-02-19) — [pypsa-eur #1550](https://github.com/PyPSA/pypsa-eur/issues/1550)
- MPS overhead with Gurobi (user) — [linopy #261](https://github.com/PyPSA/linopy/issues/261). Maintainer-filed, AI-drafted: the MPS writer drops coefficients between 1e-10 and 1e-9, so "The same model gives different results with the same solver, depending on" the I/O path — [linopy #1182](https://github.com/PyPSA/linopy/issues/1182); "MPS export silently drops all indicator constraints" — [linopy #1186](https://github.com/PyPSA/linopy/issues/1186)
- An old but recurring want: open-source solver support, "Is there a way to run the pypsa-eur model with an opensource solver like GLPK, CBC" — [pypsa-eur #3](https://github.com/PyPSA/pypsa-eur/issues/3) (2019, outside the date range)

### Inferences
- These support the covered theme "one spec, many tools". A new angle is "same model, same answer, any path": an LP file and a direct handoff should not differ.

### Gaps
- No quantified user report comparing direct and LP-file solve time was found.

## 8. Companies, TSOs and consultancies

### Takeaway
Production users exist, including a Dutch HV-grid DC-OPF, trading desks, ENTSO-E's Open-TYNDP and APG. Their asks are scenario comparison at scale, migrations without result drift, piecewise bid curves and reserve products.

### Cited Findings
- "In our production DC-OPF model of the Dutch HV grid, every fossil plant is cloned into 2-3 tranche generators with increasing markups … to get a convex bid curve" (2026-09-10, @MaykThewessen) — [PyPSA #1914](https://github.com/PyPSA/PyPSA/issues/1914)
- Production workflows named as "trading desks, dispatch scheduling, automated reporting" — [PyPSA #1590](https://github.com/PyPSA/PyPSA/issues/1590)
- ENTSO-E and Open Energy Transition are replicating TYNDP 2024 on PyPSA-Eur, "under active development and is not yet feature-complete" (search summary) — [Open-TYNDP](https://open-tyndp.readthedocs.io/en/latest/)
- PyPSA's self-maintained user list includes Austrian Power Grid (APG), Energynautics, and Fraunhofer ISI and IEG (search summary; self-reported) — [PyPSA users](https://docs.pypsa.org/latest/home/users/). d-fine built a PyPSA-based European model — [d-fine](https://www.d-fine.com/en/news/european-energy-modelling-project/)
- Open-ISP/ISPyPSA builds on PyPSA and hits the rolling-horizon custom-constraint gap — [ISPyPSA #166](https://github.com/Open-ISP/ISPyPSA/issues/166). That the organisation relates to AEMO's ISP is unconfirmed.
- A framework maintainer considers switching: the flixopt maintainer proposes "Effects" to "maybe allow us to switch from our own Framework to pypsa sometime in the future" (2026-07-07) — [PyPSA #1788](https://github.com/PyPSA/PyPSA/issues/1788)

### Inferences
- Industry users are few but vocal on GitHub, and one contributor (@MaykThewessen) accounts for several production-flavoured asks. Do not present them as a broad market signal.

### Gaps
- No public statement from a TSO or consultancy about PyPSA pain (as opposed to adoption) was found. Such feedback is likely private or given at the developer meetings.

## Summary: candidate NEW themes, beyond those already covered
1. **No silent "Optimal"**: guessed alignment, NaN fill and dropped rows give plausible wrong answers ([linopy #714](https://github.com/PyPSA/linopy/issues/714), [#670](https://github.com/PyPSA/linopy/issues/670), [PyPSA #1677](https://github.com/PyPSA/PyPSA/pull/1677)).
2. **Custom math that survives a save**: callbacks are not persisted, and custom data never reaches the network ([PyPSA #322](https://github.com/PyPSA/PyPSA/issues/322), [#2014](https://github.com/PyPSA/PyPSA/issues/2014), [linopy #561 comment](https://github.com/PyPSA/linopy/issues/561#issuecomment-3822631204)).
3. **Sparse by nature**: dense arrays inflate sparse energy models ([linopy #248](https://github.com/PyPSA/linopy/issues/248)).
4. **Rebuild cost multiplies in loops**: MGA, sweeps and rolling horizon ([linopy #599](https://github.com/PyPSA/linopy/issues/599), [#198](https://github.com/PyPSA/linopy/issues/198), [PyPSA #1634](https://github.com/PyPSA/PyPSA/issues/1634)).
5. **Infeasible is usually a data bug**: inf, NaN or zero inputs surface only at solve ([pypsa-eur #1226](https://github.com/PyPSA/pypsa-eur/issues/1226), [#2187](https://github.com/PyPSA/pypsa-eur/issues/2187), [PyPSA #1094](https://github.com/PyPSA/PyPSA/issues/1094), [#1627](https://github.com/PyPSA/PyPSA/issues/1627)).
6. **Rerun last year's study and get last year's answer**: upgrade drift and non-determinism ([PyPSA #1681](https://github.com/PyPSA/PyPSA/issues/1681), [#2022](https://github.com/PyPSA/PyPSA/issues/2022)).
7. **Results you can query**: multi-GB netCDF and bespoke pandas per comparison ([PyPSA #1590](https://github.com/PyPSA/PyPSA/issues/1590)).
8. **A rolling horizon that keeps its budget**: caps and minimums are re-applied per window ([PyPSA #2067](https://github.com/PyPSA/PyPSA/issues/2067), [#1769](https://github.com/PyPSA/PyPSA/issues/1769)).
9. **Units and scope you can read**: per-year vs per-period CO2, docs vs code on standby cost ([PyPSA #2169](https://github.com/PyPSA/PyPSA/issues/2169), [#864](https://github.com/PyPSA/PyPSA/issues/864)).
