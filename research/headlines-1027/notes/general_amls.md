# Pain points of general algebraic modelling tools (Pyomo, JuMP, GAMS, AMPL, CVXPY, PuLP, gurobipy, linopy)

Method and reliability notes (read first):
- Researched 2026-11-18. Sources reached: GitHub issue bodies (through the GitHub search API, which returns the original text, so quotes from it are verbatim), github.com issue pages, and Gurobi community pages (WebFetch, verbatim).
- These hosts did NOT resolve from this session, so their pages could not be read: discourse.julialang.org, medium.com, jump.dev, gams.com, discuss.ampl.com, staadecker.substack.com, yetanothermathprogrammingconsultant.blogspot.com. Google Groups and OR Stack Exchange were not reached either. Items from those sites come from **search-engine snippets** and are marked **[snippet]**. Their wording is the search tool's summary and may not be the author's exact words. Check them before quoting them in marketing.
- Quotes marked "verbatim" were copied from the original text.
- Conflict of interest: the PyPSA and linopy issues filed in 2026 (for example PyPSA #2084, linopy #756, #768, #813, #1182) come from the ecosystem around mathspec/specsolve, and several are AI-generated. PyPSA #2084 says "math-spec integration" outright. Count them as evidence of the problem, not as independent user voices.

## 1. Model build time and memory (time before the solver starts, LP writing, time-to-first-solve)

### Takeaway
Users of Pyomo, PuLP, CVXPY and gurobipy report the same complaint again and again: building the model takes longer than solving it or becomes the bottleneck. The fixes they are offered are profiling, PyPy, or dropping to a lower-level API, never "write it the same way and it is fast". JuMP's version of the problem is a fixed compile latency ("time-to-first-solve"). Since 2024 there has been an arms race of new tabular/columnar builders (PyOptInterface, pyoframe, polar-high) that benchmark build time and peak memory against linopy and Pyomo.

### Cited Findings
- Pyomo, 2019-08-16, verbatim: "Right now a huge amount of the time used for instantiating an abstract model goes into evaluation and construction of constraints." The user asks for parallel construction because it "would probably speed up the model instantiation extremely". — [Pyomo #1104](https://github.com/Pyomo/pyomo/issues/1104)
- Pyomo, 2020-07-07, verbatim. A university researcher reports "Slow speed when creating the instance of the model" and "High-memory consumption." The issue was closed in April 2021 with "The GitHub Issues are intended for bug reports and enhancement/feature requests", and no fix. — [Pyomo #1548](https://github.com/Pyomo/pyomo/issues/1548)
- Pyomo developers, 2019-11-07, verbatim: "I think users would generally expect direct solver interfaces to be faster, since we're avoiding file I/O. However, I think this is not always the case." — [Pyomo #1160](https://github.com/Pyomo/pyomo/issues/1160)
- Pyomo developers, 2019-11-07, verbatim. They propose C/C++ file writers because this "could significantly reduce the time needed to process a Pyomo model and generate a standard data file". — [Pyomo #1158](https://github.com/Pyomo/pyomo/issues/1158)
- Pyomo, 2023-04-16: open issue titled "performance of sum_product with sparse coefficients". — [Pyomo #2808](https://github.com/Pyomo/pyomo/issues/2808)
- Pyomo [snippet], 2019: a benchmark post reports that a colleague's Pyomo model "took about 25 minutes just to construct (1.2 million variables and 2.5 million constraints)". — [Medium, "Construction speed in popular open-source math modeling tools"](https://medium.com/@vanstark88/construction-speed-in-popular-open-source-math-modeling-tools-712fd841fc50)
- Pyomo [snippet]: the pyoframe author's essay says Pyomo is ">10x slower at constructing large models compared to GAMS or AMPL". — [staadecker substack, "We need better tools for linear programming"](https://staadecker.substack.com/p/we-need-better-tools-for-linear-programming)
- AMPL vs others [snippet]: an independent benchmark thread reports that "AMPL is around 25 times faster than Pyomo, and almost 4 times faster than JuMP". — [AMPL forum, "Model creation time of AMPL vs Gurobipy, Jump, Pyomo"](https://discuss.ampl.com/t/model-creation-time-of-ampl-vs-gurobipy-jump-pyomo/2076)
- gurobipy, 2022-10-12, verbatim: "these constraints are only being added to the model at a rate of ~8.5/second, which seems awfully slow". The model had "around 80,000 variables". Gurobi staff's only reply was to convert the post into a private support ticket. — [Gurobi community](https://support.gurobi.com/hc/en-us/community/posts/9817581374993-Gurobipy-Model-adding-constraints-at-a-very-slow-rate)
- gurobipy [snippet]: in another Gurobi thread the advice is to skip Pyomo's overhead and write the model "once to an LP or MPS file and reload it instead of rebuilding it each run". — [Gurobi community, "Managing high number of constraints"](https://support.gurobi.com/hc/en-us/community/posts/360076350732-Managing-high-number-of-constraints)
- PuLP, 2020-11-18, verbatim: "LpAffineExpression.__init__ is way too slow … It is a major bottleneck in my application". — [PuLP #362](https://github.com/coin-or/pulp/issues/362)
- PuLP, 2024-05-03, verbatim: "Creating large problems in PULP is slow … Creating expressions via `pulp.lpSum` is slower than directly creating them via `pulp.LpAffineExpression`". — [PuLP #749](https://github.com/coin-or/pulp/issues/749)
- PuLP, 2026-11-13: new issue titled "Run time degradation". — [PuLP #981](https://github.com/coin-or/pulp/issues/981)
- CVXPY, 2021-10-29, verbatim: "Compilation time of a standard form LP … increases linearly with the number of variables". — [CVXPY #1521](https://github.com/cvxpy/cvxpy/issues/1521). Also 2023-08-07, "Slow compiling time for an unconstrained quadratic problem". — [CVXPY #2205](https://github.com/cvxpy/cvxpy/issues/2205)
- JuMP time-to-first-solve [snippet]: the JuMP 1.0 paper says new users often report sluggishness on first runs, caused by JIT compilation. Its example shows about 16 seconds of overhead on a trivial model. — [arXiv 2206.03866](https://arxiv.org/pdf/2206.03866). The MOI docs [snippet] say "there are no magic solutions to reduce latency". — [MOI latency tutorial](https://jump.dev/JuMP.jl/stable/moi/tutorials/latency)
- JuMP [snippet]: a Discourse user found that the first `optimize!` was slow while `solve_time` did not show it. The answer: solve_time "reports the time spent inside the solver", and the rest is JuMP copying the problem plus compilation. — [Discourse, "JuMP solve_time not matching actual time"](https://discourse.julialang.org/t/jump-solve-time-not-matching-actual-time/126397)
- JuMP [snippet]: one answer concedes that for solving many small problems "at this moment JuMP might not be the right tool for the job". — [SO mirror, "is julia jump 15x slower then python cvxpy"](https://kiwix.lema.org/stackoverflow.com_en_all_2023-11/questions/67269609/is-julia-jump-15x-slower-then-python-cvxpy)
- JuMP, 2023-04-18 and 2023-12-03: issues titled "Precompiling JuMP" and "Failed to generate a custom sysimage for JuMP". The workaround for latency is itself a source of failures. — [JuMP #3323](https://github.com/jump-dev/JuMP.jl/issues/3323), [JuMP #3594](https://github.com/jump-dev/JuMP.jl/issues/3594)
- linopy vs polar-high, 2026-06-02, verbatim table. At N=3000 (~18M variables, build only): polar-high 87 s / 16.4 GB against linopy (`io_api="lp"`) 300 s / 23.7 GB. Network LP at ~8.4M variables: 51 s / 11.5 GB against 165 s / 14.1 GB. — [linopy #740](https://github.com/PyPSA/linopy/issues/740)
- linopy, 2026-06-04, verbatim: a `LinearExpression` "stores `coeffs`/`vars` over a **dense `coord_dims × _term` rectangle**. Every op that combines terms re-pads that axis — which is the peak allocation in real PyPSA builds." — [linopy #756](https://github.com/PyPSA/linopy/issues/756) (ecosystem-internal)
- linopy, 2024-04-10, verbatim: the PyOptInterface benchmark "shows that the speed in constructing the matrix is comparable to Jump". The issue asks whether linopy can use it to speed up construction. — [linopy #271](https://github.com/PyPSA/linopy/issues/271)
- PyPSA, 2026-11-03, verbatim: "On large networks, PyPSA's own data preparation inside `n.optimize.create_model()` costs more than linopy does." The issue says this matters "mostly" for rolling-horizon runs. — [PyPSA #2084](https://github.com/PyPSA/PyPSA/issues/2084) (ecosystem-internal)

### Inferences
- The time before the solver starts has three separate parts that users experience separately: building expressions, writing or handing off to the solver, and data preparation upstream of the modelling layer (PyPSA #2084). A headline that covers "data in to solver start" is wider than "fast builds".
- Memory peak, not only wall time, is now a benchmark axis (linopy #740, #756).

### Gaps
- No verbatim Pyomo Google Group or JuMP Discourse quotes: those hosts did not resolve. The Medium and AMPL-forum numbers are from snippets only.

## 2. Readability vs performance ("the fast way is unreadable")

### Takeaway
The speed advice for every Python tool is "write it differently": avoid `lpSum`, avoid loops and if-statements in rules, use the lower-level API. Maintainers in JuMP and GAMS acknowledge that the data format and sparse indexing decide performance, so the same math runs fast or slow depending on how the code is written.

### Cited Findings
- PuLP, 2024-05-03, verbatim: the idiomatic `pulp.lpSum([...])` is the "Slow objective function" and `pulp.LpAffineExpression(...)` is the "Faster objective function". — [PuLP #749](https://github.com/coin-or/pulp/issues/749)
- Pyomo forum advice [snippet]: "avoid unnecessary loops and move 'if' comparisons out of the loops", and try running Pyomo "through PyPy". — [Pyomo forum, "Excessively long time to create models for large systems"](https://groups.google.com/g/pyomo-forum/c/YTPByhZzboA), [Pyomo forum, "Time required to create and solve model instance"](https://groups.google.com/g/pyomo-forum/c/NcBrG-swdNc)
- JuMP vs GAMS, 2023 [snippet]: the JuMP maintainers replied to GAMS's benchmark that "differences in the input data format—not anything intrinsic to the respective libraries" explain the gap, and they presented a faster JuMP version. — [jump.dev, "JuMP, GAMS, and the IJKLM model" (2023-07-20)](https://jump.dev/2023/07/20/gams-blog/)
- JuMP, 2023-07-29: after that blog post, JuMP opened "Improve support for relational algebra" to make the fast (join-style) syntax "a bit nicer". — [JuMP #3438](https://github.com/jump-dev/JuMP.jl/issues/3438)
- GAMS [snippet]: GAMS's own post argues that Pyomo, JuMP and gurobipy "rely on general programming conventions", which affects how readable a model is. — [GAMS blog, 2023-07](https://gams.com/blog/2023/07/performance-in-optimization-models-a-comparative-analysis-of-gams-pyomo-gurobipy-and-jump/)
- Readability [snippet]: the pyoframe author says JuMP "has a particularly clear syntax due to its use of syntactic macros, a feature of Julia that doesn't exist in Python". — [staadecker substack](https://staadecker.substack.com/p/we-need-better-tools-for-linear-programming)
- Translation [snippet]: a consultant comparing a Pyomo and a GAMS version of one network model advises against translating line by line between tools and suggests translating concepts instead. — [Yet Another Math Programming Consultant, 2021-08](https://yetanothermathprogrammingconsultant.blogspot.com/2021/08/a-network-model-pyomo-vs-gams.html)
- linopy, 2024-04-10, verbatim: "The syntax is also [easier to read] compared to Jump." This is a readability claim made as a selling point inside an issue about speed. — [linopy #271](https://github.com/PyPSA/linopy/issues/271)

### Inferences
- "The idiomatic form is the slow form" is documented for PuLP (verbatim) and claimed by advice threads for Pyomo. That supports the covered theme "readable equals fast".

### Gaps
- No direct user quote of the form "the fast way is unreadable" was found verbatim. The evidence is implied by the advice threads.

## 3. Errors found late: build/solve-time errors, unhelpful messages, wrong indices

### Takeaway
A strong NEW angle beyond "check before data": **silent acceptance**. Pyomo accepts an invalid index without complaint, and transformations quietly produce wrong values. Users report spending "a while" or "significant amounts of time" before finding the cause. Errors that do surface come "six function calls deep". JuMP opened an umbrella issue in 2026 to improve error messages, explicitly for coding agents.

### Cited Findings
- Pyomo, 2026-10-07, verbatim: "I spent a while troubleshooting a bug in a PrOMMiS model. The problem is that a variable was being fixed for an invalid index." Also: "I'd expect a `KeyError` to be raised, because `"d"` isn't a valid index … Instead, it continues, returning an empty list." — [Pyomo #4051](https://github.com/Pyomo/pyomo/issues/4051)
- Pyomo, 2024-08-13, verbatim: scaled Expressions return "erroneous values. I've encountered this issue twice now and spent significant amounts of time debugging before I realized the scaling transform was the issue." — [Pyomo #3344](https://github.com/Pyomo/pyomo/issues/3344)
- Pyomo, 2019-09-26, verbatim: "New users (like me) are unfamiliar with `pyomo`'s quirks and are extremely confused when they try to make a `Param` but end up with an unhelpful error message from six function calls deep." — [Pyomo #1126](https://github.com/Pyomo/pyomo/issues/1126)
- Pyomo, 2021-10-19, verbatim: "the exception provided is cryptic and unhelpful … The traceback I got was not helpful for debugging". — [Pyomo #2156](https://github.com/Pyomo/pyomo/issues/2156)
- Pyomo, 2023-08-19, verbatim, on `Block.Skip`: "you can't rely on iterating through an IndexedBlock's keys to know what is actually real." — [Pyomo #2957](https://github.com/Pyomo/pyomo/issues/2957)
- Pyomo index errors [snippet]: recurring forum and Stack Overflow questions about "Index '(None, 0)' is not valid for indexed component 'sigma'", and about indexing a tuple-indexed variable with a single element. — [SO mirror](https://kiwix.lema.org/stackoverflow.com_en_all_2023-11/questions/75535802/keyerror-index-none-0-is-not-valid-for-indexed-component-sigma), [Pyomo forum](https://groups.google.com/g/pyomo-forum/c/gDF0IB3aQbI)
- JuMP, 2026-06-19, verbatim: "@mlubin and I have been talking about improving JuMP for coding agents. One area in which we can do a lot better is to provide more informative error messages, so that when things go wrong agents (and users) have more guidance on what to do next". The issue proposes "two-part error messages". — [JuMP #4175](https://github.com/jump-dev/JuMP.jl/issues/4175)
- JuMP, 2025-12-12: issue titled "MethodError: no method matching zero(::Type{Any})", reported in a DataFrames context. — [JuMP #4096](https://github.com/jump-dev/JuMP.jl/issues/4096)

### Inferences
- "Wrong index accepted silently" (Pyomo #4051) is concrete, recent and quotable evidence for load-time validation that names the bad label.
- "Error messages for agents" (JuMP #4175) is a NEW theme: messages that name the rewrite now serve LLM coding agents as well as people.

### Gaps
- No "hours lost" quote with a number of hours was found verbatim.

## 4. Debugging infeasibility, reading duals, finding the wrong constraint

### Takeaway
Users ask the same question for every tool: which constraint makes it infeasible? The answers rely on solver-specific IIS support, which wrappers expose unevenly. Pyomo's helper flags cascading constraints, so the culprit is not obvious.

### Cited Findings
- [snippet] Stack Overflow answer on Pyomo: if one constraint is infeasible, every other constraint "having variables linked to that infeasible constraint will also turn out to be infeasible". It suggests deactivating constraints one at a time. — [SO mirror, "finding out reason of pyomo model infeasibility"](https://kiwix.lema.org/stackoverflow.com_en_all_2023-11/questions/51044262/finding-out-reason-of-pyomo-model-infeasibility)
- [snippet] A Pyomo forum post asks for a "step by step post about how to access the IIS with pyomo and gurobi solver" and says the suggested route was "not working with the options" tried. — [Pyomo forum](https://groups.google.com/g/pyomo-forum/c/9n5KAg2nKDk)
- [snippet] PyPSA forum: "How can I find which equations are infeasible in PyPSA lopf?" The logging helper "might not tell you all combinations of constraints which are infeasible". — [PyPSA forum](https://groups.google.com/g/pypsa/c/UDFnQAyILWg)
- [snippet] Gurobi community: "How to check which constraints make model infeasible?" — [Gurobi community](https://support.gurobi.com/hc/en-us/community/posts/6967869511441-How-to-check-which-constraints-make-model-infeasible)
- linopy, 2024-10-10, verbatim: "COPT has a python example of how to calculate the IIS to help debug infeasible solutions. It would be great to add this functionality to linopy." — [linopy #358](https://github.com/PyPSA/linopy/issues/358)
- Pyomo, 2023-08-01 and 2022-02-16: issues titled "Termination condition is optimal, but solution does not appear to be" and "Termination condition is optimal but number of solutions is 0". Users cannot trust the status they read back. — [Pyomo #2933](https://github.com/Pyomo/pyomo/issues/2933), [Pyomo #2290](https://github.com/Pyomo/pyomo/issues/2290)
- [snippet] PyPSA forum: "Understanding Gurobi Variable Names". Users struggle to map a solver's names back to model components. — [PyPSA forum](https://groups.google.com/g/pypsa/c/1kZFTmcXRK4)

### Inferences
- Getting an IIS back in the model's own names and labels, rather than the solver's `c123` names, is a recurring need. Mapping solver names back to model rows is a pain point in its own right.

### Gaps
- No verbatim user complaint about reading duals was found in this pass.

## 5. Licence cost, lock-in, and migrating between GAMS/AMPL and Python

### Takeaway
GAMS's commercial solver add-ons are expensive. Large legacy GAMS models (TIMES) weigh migration and find that redevelopment plus running two platforms side by side is the cost. Vendors answer with Python front-ends (GAMSPy) and converters. Converters exist, but practitioners advise translating concepts, not lines.

### Cited Findings
- [snippet] GAMS price list: GAMS/CPLEX $10,500, GAMS/BARON $3,500 (commercial). — [GAMS pricing](https://gams.com/sales/pricing_regular)
- [snippet] ETSAP feasibility study on moving TIMES from GAMS to Python or Julia/JuMP: "the cost of redeveloping and then the cost of maintaining both GAMS & the alternative platform needs to be quantified". It also says Julia/JuMP performance "appears acceptable, but falls well behind GAMS" and that Pyomo performance "can probably be optimised". (2018, before the requested window.) — [ETSAP, "Migrating TIMES to another modelling language"](https://www.slideshare.net/slideshow/migrating-times-to-another-modelling-language-approaches-issues-and-problems/103936589)
- [snippet] GAMS offers a convert tool from .gms to Pyomo .py. Pyomo's GAMS route "does not directly talk to a GAMS solver, but instead has GAMS generate the model again". — [GAMS blog, 2020-06](https://gams.com/blog/2020/06/new-and-improved-gams-links-for-pyomo-and-jump/)
- linopy, 2025-06-11: issue titled "GAMS Solvers compatibility". Users want GAMS-licensed solvers from a Python tool. — [linopy #461](https://github.com/PyPSA/linopy/issues/461)
- linopy, 2021-06-22: issue titled "Add `PuLP` migration guide". — [linopy #3](https://github.com/PyPSA/linopy/issues/3)
- JuMP, 2022-07-07: issue titled "Export Nonlinear Models". Exporting a model to another tool is a request in its own right. — [JuMP #3015](https://github.com/jump-dev/JuMP.jl/issues/3015)

### Inferences
- Migration cost is framed as "maintain both", which supports the covered theme "one spec, many tools": a spec that targets several engines avoids the period of running two platforms.

### Gaps
- No verbatim post-2019 user complaint about AMPL or GAMS licence cost was found. The forum sites did not resolve.

## 6. Documenting the math: LaTeX from a model, keeping papers and code in sync

### Takeaway
Users have asked for GAMS-Model2Tex-style generated documentation since at least 2018. The tools that now print LaTeX (Pyomo `latex_printer`, JuMP `latex_formulation`) break on common model styles and corrupt numbers, so the printed math and the solved math can differ.

### Cited Findings
- Pyomo, 2018-11-18 (before the window), verbatim: "It would be a great, great feature to be able to automatically generate model documentation. I'm thinking of something like GAMS Model2Tex". The fallback is hand-written LaTeX in docstrings, as Calliope does. — [Pyomo #752](https://github.com/Pyomo/pyomo/issues/752)
- Pyomo, 2024-06-25, verbatim: "`latex_printer` … works well with the 'procedural style' of defining a model, but it does not work if the model is defined in an 'object-oriented' style." — [Pyomo #3300](https://github.com/Pyomo/pyomo/issues/3300)
- Pyomo, 2024-07-18 and 2024-02-04: issues titled "latex_printer throws KeyError on numpy.int64" and "Error using latex_printer with IDAES model". — [Pyomo #3325](https://github.com/Pyomo/pyomo/issues/3325), [Pyomo #3121](https://github.com/Pyomo/pyomo/issues/3121)
- Pyomo, 2023-11-27: issue titled "Additional task items from the latex printer PR that were cut for bandwidth/time reasons". — [Pyomo #3048](https://github.com/Pyomo/pyomo/issues/3048)
- JuMP, 2026-10-16: issue titled "latex_formulation drops the sign of negative coefficients in scientific notation". The printed math is wrong. — [JuMP #4268](https://github.com/jump-dev/JuMP.jl/issues/4268)
- JuMP, 2024-10-06: issue titled "LaTeX printing does not format scientific numbers". — [JuMP #3837](https://github.com/jump-dev/JuMP.jl/issues/3837)
- JuMP, 2021-02-12: issue titled "Restore multiline LaTeX". — [JuMP #2460](https://github.com/jump-dev/JuMP.jl/issues/2460)

### Inferences
- JuMP #4268 (sign dropped) is a clean example of "published math does not equal solved math". It supports the covered theme with a 2026 date.
- Printers that work on an instantiated model print the expanded instance, not the indexed algebra, and fail on some styles. A spec-level typesetter avoids both problems.

### Gaps
- Did not find user posts about keeping a paper's appendix in sync with code (beyond Pyomo #752).

## 7. Dataframes, databases, data pipelines; getting results out as tables

### Takeaway
Users want variables as dataframe columns and results back as tables. Polars is now being requested by name (2026). In production energy-model work, results across scenarios are slow to compare because they are stored as multi-GB netCDF files.

### Cited Findings
- JuMP, 2023-02-09, verbatim: "it'd be nice to improve this … by adding `x` as a column to the data frame instead of a separate variable … I'd imagine there are lots of models where the variables correspond to a row in a dataframe." — [JuMP #3212](https://github.com/jump-dev/JuMP.jl/issues/3212)
- JuMP, 2022-09-28, verbatim: "getting large results feels kind of slow. Fast read of results that can easily be dropped into dataframes, plots, csv etc" is wanted, along with result tables "with good default column names automatically". — [JuMP #3096](https://github.com/jump-dev/JuMP.jl/issues/3096)
- JuMP, 2023-06-05: issue titled "`Containers.rowtable` is slow on Julia 1.9". — [JuMP #3404](https://github.com/jump-dev/JuMP.jl/issues/3404)
- gurobipy-pandas, 2026-10-29, verbatim: "One of our customers has mentioned Polars is becoming more popular relative to Pandas. To what extent would it be feasible to implement a Polars-version of this package?" — [gurobipy-pandas #105](https://github.com/Gurobi/gurobipy-pandas/issues/105)
- PyPSA, 2026-03-02, verbatim: "Comparing scenarios requires loading multiple multi-GB files into memory and writing custom pandas code for every query. This works for research notebooks but is a bottleneck for production workflows (trading desks, dispatch scheduling, automated reporting)". The proposed table: comparing 10 scenarios' total cost takes "30-50s (load 10 files)" against "0.5s (single query)". — [PyPSA #1590](https://github.com/PyPSA/PyPSA/issues/1590)
- Pyomo, 2021-03-25: issue titled "Data type problems combining DataFrames and CPLEXDirect". — [Pyomo #1886](https://github.com/Pyomo/pyomo/issues/1886)
- Pyomo [snippet]: "Slow DAT-file parsing can dominate build time." — [Pyomo forum](https://groups.google.com/g/pyomo-forum/c/NcBrG-swdNc)
- pyoframe, 2025-02-12, verbatim: "there is no shift... In model that has time connections, shift is quite useful. Also I couldn't find cumulative sum method." — [pyoframe #93](https://github.com/Bravos-Power/pyoframe/issues/93)

### Inferences
- NEW theme: **results across scenarios as queryable columnar files** (PyPSA #1590). This matches specsolve's parquet archives and catalog directly.
- NEW theme: **Polars by name**, from a vendor's customer (gurobipy-pandas #105).
- NEW theme: **time-series operators** (shift, cumulative sum) missing from dataframe-style modellers (pyoframe #93).

### Gaps
- No verbatim database (SQL) integration complaint was found for Pyomo or JuMP.

## 8. Testing optimisation models, CI, version control

### Takeaway
Users find unit-testing optimisation models hard because small changes produce different optimal solutions. The expert answer is to test properties (feasibility, non-triviality, magnitudes), not exact solutions. Projects running CI benchmarks find that a dependency bump silently changes performance or results.

### Cited Findings
- Gurobi community, 2023-08-18, verbatim: "if there are any minor changes in constraints or objective it creates lot of different solutions". The user asks for a testing strategy. The 2024-03-11 answer from Aimpoint Digital recommends checking feasibility with "independent feasibility checkers, ideally built by someone unfamiliar with the math model", plus non-triviality and realistic magnitudes. — [Gurobi community, "Software Testing"](https://support.gurobi.com/hc/ja/community/posts/17874003668369-Software-Testing)
- [snippet] A blog post says the "usual unit-testing approach will most likely fail here" and uses property-based testing (Hypothesis) on a small MIP. — [nonvisual.github.io, 2021-02-07](https://nonvisual.github.io/)
- [snippet] EURO practice webinar, 2026-03: move logic out of model-building so it can be tested separately, and test solutions against business rules. — [EURO EPF webinar slides](https://www.euro-online.org/websites/or-in-practice/wp-content/uploads/sites/8/2026/03/54-EPF-webinar-6-Mar-26-presentation.pdf)
- linopy, 2026-07-02, verbatim: "CodSpeed went red on `master` with a −16.66% regression … The only relevant change … is the **highspy bump `1.13.1 → 1.15.0`**". The root cause was `addRows` being about 4x slower. — [linopy #813](https://github.com/PyPSA/linopy/issues/813) (ecosystem-internal)
- linopy, 2026-11-18, verbatim: "coefficients between `1e-10` and `1e-9` survive in the linopy model and in `io_api="direct"`, but are silently missing from the MPS file. The same model gives different results with the same solver, depending on `io_api`." — [linopy #1182](https://github.com/PyPSA/linopy/issues/1182) (ecosystem-internal)
- PuLP, 2023-05-11: issue titled "static type checks with `mypy`". — [PuLP #650](https://github.com/coin-or/pulp/issues/650)

### Inferences
- Archiving the inputs and the answer of every solve makes it possible to diff a run against the last one, which is what these testing threads lack. That is a candidate headline angle for specsolve.
- "Same model, different answer depending on the export path" (linopy #1182) is a NEW theme: the path from the model to the solver is itself a source of error.

### Gaps
- No public discussion was found about version control of GAMS or AMPL code (diffing .gms files, merge conflicts).

## 9. NEW themes beyond the covered list (summary)

### Takeaway
Eight themes are not in the covered list and have dated, linkable evidence.

### Cited Findings
- **Silent wrong acceptance**: an invalid index is accepted and returns an empty list (Pyomo, 2026-10-07). — [Pyomo #4051](https://github.com/Pyomo/pyomo/issues/4051). A transform silently gives "erroneous values". — [Pyomo #3344](https://github.com/Pyomo/pyomo/issues/3344)
- **Error messages for coding agents**: "improving JuMP for coding agents … more informative error messages". — [JuMP #4175](https://github.com/jump-dev/JuMP.jl/issues/4175) (2026-06-19)
- **Export path changes the answer**: the "same model gives different results with the same solver, depending on `io_api`". — [linopy #1182](https://github.com/PyPSA/linopy/issues/1182) (2026-11-18). The printed LaTeX drops minus signs. — [JuMP #4268](https://github.com/jump-dev/JuMP.jl/issues/4268) (2026-10-16)
- **Scenario comparison is slow when results are not columnar**: "loading multiple multi-GB files into memory and writing custom pandas code for every query". — [PyPSA #1590](https://github.com/PyPSA/PyPSA/issues/1590) (2026-03-02)
- **Rolling-horizon rebuild cost**: model creation speed is "relevant for rolling horizon optimizations mostly". — [PyPSA #2084](https://github.com/PyPSA/PyPSA/issues/2084) (2026-11-03). A design issue on slicing a model along a coordinate for a rolling horizon: [linopy #768](https://github.com/PyPSA/linopy/issues/768) (2026-06-07)
- **Peak memory as the limit**: dense padding is "the peak allocation in real PyPSA builds". — [linopy #756](https://github.com/PyPSA/linopy/issues/756). The benchmark reports GB next to seconds. — [linopy #740](https://github.com/PyPSA/linopy/issues/740)
- **Polars demand from vendor customers**. — [gurobipy-pandas #105](https://github.com/Gurobi/gurobipy-pandas/issues/105) (2026-10-29)
- **Testing without a single "right answer"**. — [Gurobi community](https://support.gurobi.com/hc/ja/community/posts/17874003668369-Software-Testing) (2023-08-18)
- **Status you cannot trust**: "Termination condition is optimal, but solution does not appear to be". — [Pyomo #2933](https://github.com/Pyomo/pyomo/issues/2933) (2023-08-01)
- **Fixed start-up latency for small, frequent solves** (JuMP) [snippet]. — [arXiv 2206.03866](https://arxiv.org/pdf/2206.03866)

### Inferences
- Candidate headline material, inferred and not quoted: "A wrong label is an error, not an empty list." "Compare a hundred scenarios with one query." "The math you print is the math you solve, minus signs included." "Error messages that name the fix, for people and agents."

### Gaps
- Unreachable hosts (Julia Discourse, Medium, jump.dev, gams.com, AMPL forum, substack, blogspot, Google Groups, OR Stack Exchange) probably hold more verbatim user voice. A re-run with those hosts allowed would turn the [snippet] items into verbatim quotes.
