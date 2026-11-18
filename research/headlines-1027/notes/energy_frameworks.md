# Pain points across open energy system modelling frameworks (non-PyPSA)

Scope note: this session could reach only GitHub (issues via the search API, files via raw.githubusercontent.com). Every other host (forum.openmod.org, sciencedirect, arxiv, callio.pe, readthedocs, zenodo, doi.org) was blocked by the session network. So:

- **GitHub items are verbatim**, read in full from the issue body, and carry the issue's creation date.
- **Literature items come from search-engine abstracts and snippets**, not full texts. Treat their wording as abstract-level paraphrase unless shown in quotation marks, and re-check before printing a quote in marketing.
- **Recent bulk-filed issues.** Several issues filed Oct–Nov 2026 on OSeMOSYS_GAMS, OSeMOSYS_PuLP, FINE and Temoa share one template-like style and appear to come from a systematic cross-implementation audit. Their provenance was not checked. They are strong as evidence of the problem, but check who filed them before quoting them as "the community says".

---

## 1. Model intercomparison: how hard is comparing formulations across frameworks, and what blocks it?

### Takeaway
Intercomparisons keep finding that harmonising input data narrows the gaps, but **structural formulation choices still drive divergent results**. Each framework writes its math differently and holds it in code, so the comparison cannot isolate which equation caused a difference. Even a single framework, OSeMOSYS, drifts between its own four language implementations.

### Cited Findings
- **Temoa, Switch, GenX and USENSYS on identical inputs (Schivley et al., arXiv 2411.13783, Nov 2024).** The models were run on identical policy, cost and operational assumptions, and structural choices still mattered: "configurations with unit commitment constraints or economic retirement yield different investments and system costs compared to simpler configurations" (search abstract). — [arXiv 2411.13783](https://arxiv.org/pdf/2411.13783)
- **European electricity models, harmonised inputs (arXiv 2412.12964, Dec 2024).** Four models were compared after their scenario inputs were harmonised. The authors find "the result differences mainly depend on the modeling approach" (search abstract). — [arXiv 2412.12964](https://pdf.arxiv.org/pdf/2412.12964)
- **MODEX "Code exposed" (Candas et al., 2022).** oemof, GENeSYS-MOD, Balmorel, urbs and GENESYS-2 were run on two harmonised German scenarios. Results were similar, but differences appeared "especially in the long-term expansion planning model", and some could be traced to identified modelling differences (search abstract). — [RLI publication page](https://reiner-lemoine-institut.de/en/publication/code-exposed-review-of-five-open-source-frameworks-for-modeling-renewable-energy-systems-candas-et-al-2022/)
- **Four US capacity-expansion models (Henry et al., Columbia QSEL, 2021).** The study used "highly simplified scenarios" to separate parametric uncertainty from structural differences, and released an open test dataset for others to build on (search abstract). — [QSEL PDF](https://qsel.columbia.edu/assets/uploads/blog/2021/publications/promoting-reproducibility-and-increased-collaboration-in-electric-sector.pdf)
- **Earlier reviews compared features, not equations (Hoffmann et al., Advances in Applied Energy 16, 100190, 2024).** The review examines 63 optimisation frameworks and 68 earlier reviews. It says prior reviews compared features and adaptability but left out the underlying mathematics, so the authors define one MILP that contains all the features discussed (abstract). — [DOAJ record](https://doaj.org/article/316f10bce49e45f697b7130f71bdc354); [DLR elib](https://elib.dlr.de/207107)
- **OSeMOSYS: one model in four languages, four input formats (GitHub issue #23, 2019-06-11).** "At present, each of the three (four if OSeMOSYS_PuLP is included) language versions of OSeMOSYS use a different input file format." — [OSeMOSYS#23](https://github.com/OSeMOSYS/OSeMOSYS/issues/23)
- **OSeMOSYS: multiple implementations complicate extensions (issue #97, 2019-10-22).** "The situation is complicated somewhat by there being multiple different implementations of OSeMOSYS, in GNU MathProg, GAMS, Pyomo and Pulp." — [OSeMOSYS#97](https://github.com/OSeMOSYS/OSeMOSYS/issues/97)
- **OSeMOSYS GAMS and Pyomo generate a different constraint set from the MathProg reference (issue #5, 2026-10-13).** The GAMS implementation "generates these equations for all indices instead", so "the generated constraint set differs from the reference". — [OSeMOSYS_GAMS#5](https://github.com/OSeMOSYS/OSeMOSYS_GAMS/issues/5)
- **OSeMOSYS PuLP variable bounds differ from the reference (issue #24, 2026-10-13).** The storage rate variables carry `lb = 0` in PuLP while "the reference formulation leaves them free". The issue calls this "inconsistent across implementations". — [OSeMOSYS_PuLP#24](https://github.com/OSeMOSYS/OSeMOSYS_PuLP/issues/24)
- **OSeMOSYS also has a NumberOfNewTechnologyUnits bound discrepancy in GAMS (issue #3, 2026-10-13).** The issue is titled "NumberOfNewTechnologyUnits is declared without a lower bound". Only the title was read. — [OSeMOSYS_GAMS#3](https://github.com/OSeMOSYS/OSeMOSYS_GAMS/issues/3)
- **Alignment across ports was a stated intent, not a check (KTH announcement, 2017).** KTH said the Python and GAMS versions "will be regularly updated and kept in line with the latest available version of OSeMOSYS GNU MathProg" (search snippet). — [KTH news](https://energy.kth.se/energy-systems/desa-news/osemosys-now-available-in-gams-and-python-1.701296?page=12)
- **The verification method for a port is to diff results by hand (IESVic OSeMOSYS e-book).** The method: run both through the same solver "and compare the results"; if the LP format is preserved and outputs are "within a small marginal difference, the translation is considered correct" (search snippet). — [IESVic e-book](https://iesvic2060.github.io/The_OSeMOSYS_EBook_by_IESVic/Book_Files/3_The_OSeMOSYS_Model_in_Pyomo.html)
- **otoole exists because data handling diverged across implementations.** It addresses "the need in the OSeMOSYS community to standardize data handling functions across multiple different model implementations" (JOSS paper, search snippet). — [JOSS otoole](https://joss.theoj.org/papers/10.21105/joss.05511.pdf)

### Inferences
- The blocker in intercomparison is not data access. Once inputs are harmonised, the residual "different results" come from formulation choices that sit in code, so no reader can diff them. A formulation written as a typeset, comparable spec addresses this directly. Headline seed: "Same data, different answer? Diff the math, not the code."
- OSeMOSYS is a natural proof case for "one spec, many engines": its own community maintains four hand ports that drift on bounds and domain filters. Each drift was found only by reading code line by line.

### Gaps
- Full texts of Candas 2022, Schivley 2024 and Hoffmann 2024 could not be fetched, so no verbatim sentences on *what blocked* the comparison (time cost, person-months) were obtained.
- No EMF/EMP-specific source on formulation-diff tooling was found in this session.

---

## 2. Transparency and openness: papers, funder, journal and regulator demands, and math documentation that drifts from code

### Takeaway
The openmod literature from 2017–2018 framed openness as a precondition for trust and reproducibility. Within the frameworks themselves, the recurring concrete pain is that **the documented equations are maintained by hand, separately from the code, and fall out of step**. That is evidenced in oemof, SpineOpt, GenX and Calliope.

### Cited Findings
- **Openness as a precondition (Pfenninger, DeCarolis, Hirth, Quoilin, Staffell, Energy Policy 101:211–215, 2017).** The paper argues models and data "must be openly available to facilitate higher quality science, greater productivity through less duplicated effort, and a more effective science-policy boundary". It finds energy research "ostensibly lags behind other fields" (abstract). — [ORBi](https://orbi.uliege.be/handle/2268/204169); [author PDF](https://www.pfenninger.org/publications-pdf/2017%20-%20Pfenninger%20et%20al%20-%20Importance%20of%20open%20data%20and%20software.pdf)
- **"Energy scientists must show their workings" (Pfenninger, Nature 542:393, 23 Feb 2017).** The comment calls for standards for sharing code, data and assumptions, and notes that only one energy journal, Energy Economics, then required data and models with submissions (search summary). — [author PDF](https://www.pfenninger.org/publications-pdf/2017%20-%20Pfenninger%20-%20Energy%20scientists%20must%20show%20their%20workings.pdf); [TU Delft record](https://research.tudelft.nl/en/publications/energy-scientists-must-show-their-workings)
- **How-to guide for opening models (Pfenninger + 22 co-authors, "Opening the black box of energy modelling", Energy Strategy Reviews 19:63–71, 2018).** It covers IP, licensing, language choice, distribution of code and data, and user communities, and concludes that institutional change is needed (abstract). — [IIASA PURE](https://pure.iiasa.ac.at/14781); [DOAJ](https://doaj.org/article/b08b26ba10db4c88be6f88a92bac9b68)
- **Morrison, Energy Strategy Reviews 20:49–63 (Apr 2018).** "public transparency can often be served by the publication of code and data under standard copyright, scientific reproducibility and open development can only be achieved through the open licensing of the associated software and datasets." A mid-2017 survey counted 28 projects with public source code, "up from six in 2010, and none in 2000" (abstract; an earlier forum draft gave about 45 versus 5, so the published figures are the ones to use). — [openmod forum draft](https://forum.openmod-initiative.org/t/article-on-transparency-reproducibility-and-open-development/251); [BL record](https://eld.bl.uk/catalog/100061785421_0x000001)
- **Openness and accessibility are still a gap (Chang et al., Applied Energy 290:116731, 2021).** The survey of 54 tools names remaining gaps: "understanding how tools are coupled together, openness and accessibility, and the level of engagement between tool developers and policy/decision-makers" (abstract). — [IIASA PDF](https://pure.iiasa.ac.at/id/eprint/17105/1/1-s2.0-S0306261921002476-main.pdf); [survey data](https://data.mendeley.com/datasets/6s59gbxh6p/1)
- **TIMES: open code that is costly to run (ETSAP, code on GitHub since Dec 2019).** The model generator is GPL-3.0, but it is GAMS code, so a GAMS licence is required. The ETSAP runtime licence "cannot be used to change the model's equations and variables", and the VEDA front and back ends are licensed separately through ETSAP (search summaries of ETSAP pages). — [ETSAP getting started](https://iea-etsap.org/getting-started-withtimes-modelling/); [TIMES-DK downloads](https://www.esymodels.man.dtu.dk/times-dk/downloads); [openmod wiki TIMES](https://wiki.openmod-initiative.org/wiki/TIMES)
- **A regulator reviews the transparency of inputs, not the model math (Australia, AER on AEMO's ISP).** The AER review checks whether AEMO's explanations of inputs and assumptions are adequate, not the merits of the modelling (search summary). A stakeholder credits publishing the ISP PLEXOS model with lowering "barriers to independent modelling". — [AER 2025 IASR review](https://www.aer.gov.au/system/files/2025-08/AER%20-%20Review%20report%20-%202025%20Inputs%2C%20Assumptions%20and%20Scenarios%20Report.pdf); [Windlab submission to AEMC](https://www.aemc.gov.au/sites/default/files/2026-09/windlab.pdf)

**Math documentation drifting from code (verbatim, GitHub):**
- **oemof-solph #565 (2019-02-07), "Wrong equation in documentation".** "In the second equation the P_el should be `greater equal` not `lower equal` … In this context we could check the rest :-)" — [oemof-solph#565](https://github.com/oemof/oemof-solph/issues/565)
- **oemof-solph #428 (2018-01-09).** Custom components "do not have their mathematical description listed in their docstrings yet … It should/could be completed easily … by looking into the referenced papers and transferring the equations." — [oemof-solph#428](https://github.com/oemof/oemof-solph/issues/428)
- **oemof-solph #1010 (2023-11-14), "Misleading/missing documentation of OffsetConverter".** The thread has 20 comments; only the title was read. — [oemof-solph#1010](https://github.com/oemof/oemof-solph/issues/1010)
- **SpineOpt #800 (2023-11-15), "Writing the mathematical formulation is a nightmare".** The developer "already has to write complex code and tests, and on top of that, at the moment is also expected to update the latex with the math." — [SpineOpt#800](https://github.com/spine-tools/SpineOpt.jl/issues/800)
- **SpineOpt #647 (2023-05-21).** Documentation was removed while the implementation still ran: "the current implementation as such still exists and works. The users would appreciate those clues on what is going on." — [SpineOpt#647](https://github.com/spine-tools/SpineOpt.jl/issues/647)
- **SpineOpt #649 (2023-05-22), "Build documentation from docstrings (e.g. constraints)".** Title only. — [SpineOpt#649](https://github.com/spine-tools/SpineOpt.jl/issues/649)
- **GenX #455 (2023-05-18).** "In the notation section of the documentation the units for fuel price and emissions intensity are listed per MWh, but in the input files section it says they should be entered per MMBtu. Wondering which is correct?" — [GenX.jl#455](https://github.com/GenXProject/GenX.jl/issues/455)
- **GenX #909 (2026-05-05).** `output_settings.yml` "is mentioned in the documentation but there doesn't seem to be any detailed documentation explaining what it is, when to use it, and what the parameters in it are." — [GenX.jl#909](https://github.com/GenXProject/GenX.jl/issues/909)
- **GenX #394 (2023-03-31).** For time-domain reduction, "it is unclear from the documentation how to set up this function." — [GenX.jl#394](https://github.com/GenXProject/GenX.jl/issues/394)
- **Calliope #446 (2023-04-17), "Parameter documentation hard to find".** "parameters are nowhere defined or described … define parameters in the math yaml-files, too. Doing this would complete the mathematical representation of the problem, all in one place … could have other benefits, e.g. protect against typos." — [calliope#446](https://github.com/calliope-project/calliope/issues/446)
- **urbs #311 (2021-12-31).** "investment cost of the transmission line will be calculated twice. Please fix the bug or note this in the documentation." — [urbs#311](https://github.com/tum-ens/urbs/issues/311)
- **urbs #266 (2019-12-17).** "Although from the urbs documentation it is understandable that trading with more than one external market can be simulated, trying this does not work." — [urbs#266](https://github.com/tum-ens/urbs/issues/266)

### Inferences
- "Published math equals solved math" has strong grassroots evidence. SpineOpt's own developer calls hand-maintaining LaTeX "a nightmare". oemof had a sign flipped (≤ versus ≥) in a documented equation. GenX documented a unit that disagreed with the input files.
- A new adjacent theme: **units**. Unit mismatches between docs and inputs (GenX #455; Calliope #775, "costs must be provided per kW output") suggest the headline "Units are part of the spec, not a footnote", if mathspec declares or checks units.
- The TIMES case shows that "open source" can still mean "you need a commercial language licence to change one equation". Headline seed: "Open math you can change without a licence."

### Gaps
- No verbatim text was obtained from journal data-availability policies beyond the Energy Economics note in the Nature comment summary.
- No funder mandate (Horizon Europe or national) text was retrieved in this session.

---

## 3. Reproducibility of published studies and model documentation standards

### Takeaway
Checklists and fact sheets exist, but applying them shows partial coverage. Quality criteria score lowest, and many studies cannot be re-run because the formulation version, the data format and the code version are not pinned together.

### Cited Findings
- **Transparency checklist applied to a case study (Hülk, Müller, Glauer, Förster, Schachler, Energy Strategy Reviews 22, Nov 2018).** The checklist of Cao et al. was applied to an RLI case study: 93% of transparency criteria and 73% of reproducibility criteria were met, but "only 47% of the quality criteria were answered satisfactorily" (search summary). — [RLI page](https://reiner-lemoine-institut.de/en/publication/transparency-reproducibility-and-quality-of-energy-system-analyses-a-process-to-improve-scientific-work-huelk-et-al-2018/); [REEEM post](https://www.reeem.org/2019/01/23/paper-transparency-reproducibility-and-quality-of-energy-system-analyses-a-process-to-improve-scientific-work)
- **Best-practice guidance for ESOMs (DeCarolis et al., Applied Energy 194:184–198, 2017).** The guidance covers formulating research questions, setting boundaries, quantifying uncertainty and communicating insights (abstract). — [UCC record](https://research.ucc.ie/en/publications/formalizing-best-practice-for-energy-system-optimization-modellin/)
- **SpineOpt provenance request (#1003, 2024-05-02), "Add SpineInterface and SpineOpt commits to results DB".** The request asks that results record which code produced them. Title only. — [SpineOpt#1003](https://github.com/spine-tools/SpineOpt.jl/issues/1003)
- **otoole: old data files no longer load (#179, 2023-06-20).** "the format for the simplicity data file (generated through Otoole) is slightly different from the older Gnumathprog formats." — [otoole#179](https://github.com/OSeMOSYS/otoole/issues/179)
- **urbs: citing the tool is unclear (#262, 2019-12-02).** "We need a proper way of citing the tool and the documentation. Currently, the citation in Zenodo includes pseudonames that are not worthy of use in journals". — [urbs#262](https://github.com/tum-ens/urbs/issues/262)
- **urbs: install instructions contradict each other (#314, 2022-02-17).** "on the website … Version 3.6 or 2.7 is stated. In the ##README.md File in the zip-Folder it says Version 3.5 or 2.7." — [urbs#314](https://github.com/tum-ens/urbs/issues/314)
- **GenX: an official example does not solve (#901, 2026-01-30).** "We are starting by using PowerGenome to create output that is supposed to go into GenX, but so far the basic examples don't have a feasible solution. We set-up the example as the documentation recommended." — [GenX.jl#901](https://github.com/GenXProject/GenX.jl/issues/901)
- **oemof: a documented component example is broken (#1050, 2024-02-08), "GenericCHP component example is broken".** Title only. — [oemof-solph#1050](https://github.com/oemof/oemof-solph/issues/1050)

### Inferences
- Reproducibility fails at the joins between data format, code version and documentation, not only on data access. A self-describing archive of each solve (spec, inputs, outputs, versions) answers SpineOpt #1003 and otoole #179 directly. Headline seed: "Every solve is a reproducible archive."

### Gaps
- Open Energy Platform model factsheets and the Open Energy Ontology were not reachable. No direct evidence was gathered on their uptake or criticisms.

---

## 4. Extending frameworks with custom constraints: what goes wrong

### Takeaway
Every framework exposes custom constraints through a back door into its solver-modelling layer: Pyomo for oemof and Calliope 0.6, JuMP for GenX and SpineOpt, code edits for OSeMOSYS in each language. Users hit three problems: having to know internals, extensions that are "limited by what we put in the base math", and opaque errors when custom math is wrong.

### Cited Findings
- **Calliope #100 (2018-04-16).** "In 0.6.0 we have (temporarily?) removed the ability to introduce custom constraints via the YAML format. … A user familiar with Pyomo can currently add a custom constraint after building the backend model … by accessing the Pyomo ConcreteModel directly via `model._backend_model`." — [calliope#100](https://github.com/calliope-project/calliope/issues/100)
- **Calliope #606 (2024-06-17), "allow for complete math overrides".** Custom math built "on top" of the pre-defined math "introduces problems in cases were the math needs to be heavily modified since users have to essentially look in two different places and are limited by what we put in the base math." — [calliope#606](https://github.com/calliope-project/calliope/issues/606)
- **Calliope #604 (2024-06-13), group constraints in 0.7.** "Good news: It works. There is room for improvement regarding intuitive usability. How do we define a constraints on the summed capacity for some defined subsets of nodes?" — [calliope#604](https://github.com/calliope-project/calliope/issues/604)
- **Calliope #590 (2024-04-17).** Porting 0.6 group constraints to 0.7 custom math: "a specific sum() expression I'm doing in a custom constraint which seems to not calculate correctly." — [calliope#590](https://github.com/calliope-project/calliope/issues/590)
- **Calliope #420 (2023-03-17), "Better error messages/logging for custom math would help".** "If there are excess dims, pyomo receives dataarrays and gives an unrelated error message. This should be checked by us before creating the constraint". — [calliope#420](https://github.com/calliope-project/calliope/issues/420)
- **Calliope #735 (2025-01-27), "Memory error due to huge array introduced by `default_if_empty` in custom math".** Title only. — [calliope#735](https://github.com/calliope-project/calliope/issues/735)
- **Calliope #827 (2025-09-11).** "Trying to use a user-defined parameter as the offset for both `sum_next_n` and `roll` fail with different error messages", for minimum up and down time constraints. — [calliope#827](https://github.com/calliope-project/calliope/issues/827)
- **Calliope user-defined math docs (main branch).** "Although we have tried to make a generalised syntax for all kinds of user-defined math, our focus was on building a system to implement Calliope's base math. Therefore, we cannot guarantee that your math will be possible to implement." Also: "it may not be straightforward to pinpoint what part of your math is the culprit" when math turns nonlinear. — [docs source](https://github.com/calliope-project/calliope/blob/main/docs/building_blocks/user_defined_math/index.md)
- **oemof-solph #785 (2021-08-27).** A user implementing a renewable share constraint adds a custom `re_share` attribute to components and asks for help. — [oemof-solph#785](https://github.com/oemof/oemof-solph/issues/785)
- **oemof-solph #594 (2019-06-04), "Facades/Aliases to solph components" (19 comments).** Title only. — [oemof-solph#594](https://github.com/oemof/oemof-solph/issues/594)
- **oemof-solph #906 (2023-01-18), "GenericStorage is missing `custom_attributes` attribute".** Title only. — [oemof-solph#906](https://github.com/oemof/oemof-solph/issues/906)
- **OSeMOSYS extensions must be coordinated across language ports (#97, 2019).** See section 1. — [OSeMOSYS#97](https://github.com/OSeMOSYS/OSeMOSYS/issues/97)
- **SpineOpt #856 (2024-01-18).** "Some users have even resorted to commenting constraints out to achieve this - which shouldn't be necessary." — [SpineOpt#856](https://github.com/spine-tools/SpineOpt.jl/issues/856)

### Inferences
- "Extending without forking" is well evidenced. The new angle is **the error you get when an extension is wrong**: Calliope users get a Pyomo error about data arrays, not a pointer to their line. Headline seed: "Your constraint, your error message, at load."
- Calliope's own docs concede the custom-math syntax was built for its base math and "cannot guarantee" user math. A general-purpose language for the spec is the contrast.

### Gaps
- No GenX custom-constraint threads were read. GenX's "Model Modification" path via JuMP was not examined.

---

## 5. Onboarding, learning curve, non-programmers, GUI versus code

### Takeaway
Usability studies and issue trackers converge on two recurring problems: **handling input data** and **error messages**. GUIs (Spine Toolbox, VEDA) trade code for their own confusion and licence costs.

### Cited Findings
- **Usability testing of five frameworks (Berendes et al., RSER 159:112174, 2022).** Balmorel, GENeSYS-MOD, GENESYS-2, oemof and urbs were tested with framework developers. The most common problems were "handling input data and error messages", and usability "still needs improvement" (abstract). — [RLI page](https://www.reiner-lemoine-institut.de/evaluating-the-usability-of-open-source-frameworks-in-energy-system-modelling-berendes-et-al-2022/); [IDEAS](https://ideas.repec.org/a/eee/rensus/v159y2022ics1364032122001009.html)
- **Calliope #745 (2025-03-19), "Error messages can be misleading".** For a mistyped key, "what one obtains is a very long error message stating that the entire dictionary of parameters defined for each of those technologies is invalid". The issue proposes printing the unexpected keys. — [calliope#745](https://github.com/calliope-project/calliope/issues/745)
- **Calliope #472 (2023-07-25).** "`'>' not supported between instances of 'str' and 'int'`" … "After a lot of conf[usion]" the cause was a missing `file=`. — [calliope#472](https://github.com/calliope-project/calliope/issues/472)
- **otoole #80 (2020-10-12).** A wrong-case CSV header "gives an incomprehensible error". — [otoole#80](https://github.com/OSeMOSYS/otoole/issues/80)
- **otoole #182 (2023-06-20).** A mismatch between the config and the data file "returns a cryptic error message from Amply". — [otoole#182](https://github.com/OSeMOSYS/otoole/issues/182)
- **otoole #13 (2019-10-30).** "Validation code should raise detailed errors when names do not match convention." — [otoole#13](https://github.com/OSeMOSYS/otoole/issues/13)
- **Spine Toolbox #1817 (2022-11-02).** "It can be quite confusing to have a different name for the specification than its filename. It can also be difficult to find the specification." — [Spine-Toolbox#1817](https://github.com/spine-tools/Spine-Toolbox/issues/1817)
- **Spine Toolbox #1630 (2021-12-16).** Parameter definitions are not shown until an entity exists: "This is bit confusing." — [Spine-Toolbox#1630](https://github.com/spine-tools/Spine-Toolbox/issues/1630)
- **oemof-solph #937 (2023-05-25).** "The documentation of the components does not name all possible keywords but the API reference does. As some do not know that…" — [oemof-solph#937](https://github.com/oemof/oemof-solph/issues/937)
- **oemof-solph #1141 and #1142 (2024-11-24).** "Make introductory tutorials for new docs" and "Make advanced tutorials", part of a docs rebuild. — [oemof-solph#1141](https://github.com/oemof/oemof-solph/issues/1141)
- **Calliope 0.7 migration guide.** "Some might seem like steps back, as you have to write _more_ YAML for the same definition. However, the resulting definition should be easier to understand when you come back to it in the future". — [docs/migrating.md](https://github.com/calliope-project/calliope/blob/main/docs/migrating.md)
- **GenX #875 (2025-10-29): coding agents now modify frameworks.** A maintainer "used a Copilot agent … to modify GenX so that it can read .csv, .csv.gz, or .parquet files … But it didn't update CHANGELOG.md or the existing documentation, and all of the tests are failing." — [GenX.jl#875](https://github.com/GenXProject/GenX.jl/issues/875)

### Inferences
- **New theme: "say which key is wrong".** Load-time validation that names the offending key or header is the single most-requested usability fix across Calliope, otoole and the Berendes study. It is close to the covered "checking a model before data", but aimed at *data and config errors*.
- **New theme: agents editing models.** GenX #875 shows LLM agents already editing framework code and breaking tests and docs. A declarative, validated spec is a safer surface for an agent to edit than framework internals. Headline seed: "A model your coding agent can't silently break."

### Gaps
- No primary source on non-programmer modellers (for example VEDA or Excel-based TIMES users) was retrievable. Their pain is inferred only from licence and GUI evidence.

---

## 6. Performance and scale (temporal and spatial resolution, clustering) and model coupling

### Takeaway
Build time, not solve time, is a repeatedly reported bottleneck in Pyomo- and JuMP-based frameworks. Result writing and loading and the memory they use are emerging pain points. Temporal aggregation is a forced compromise. Model coupling is ad hoc, rarely evaluated, and often done by hand.

### Cited Findings
**Build time and memory:**
- **Calliope #781 (2025-07-24), "Long Calliope build times, even for small models".** "Im taking 10 minutes to build a model of this size … 'nodes': 3, 'timesteps': 365 … Solving and writing output finishes under 2 seconds. … This build time makes debugging of the model very challenging, especially when adding custom math." — [calliope#781](https://github.com/calliope-project/calliope/issues/781)
- **SpineOpt #855 (2024-01-18), "Model generation speed".** "SpineOpt is slow in generating large models as has been reported by many users. This is especially problematic for non-rolling models". The plan includes "Store data in DataFrames so we can use their optimised join". — [SpineOpt#855](https://github.com/spine-tools/SpineOpt.jl/issues/855)
- **SpineOpt #1219 (2025-05-23).** The issue discusses "drastic fundamental approaches to improve the model build time". The causes named are "Globals used in SpineInterface" and "Type instability from functions created on the fly", and it floats "a compiled package and implemented in Rust/C". — [SpineOpt#1219](https://github.com/spine-tools/SpineOpt.jl/issues/1219)
- **SpineOpt #856 (2024-01-18).** "even if many constraints have indices which are a null set, the SpineOpt code to figure that out takes a long time to execute." — [SpineOpt#856](https://github.com/spine-tools/SpineOpt.jl/issues/856)
- **SpineOpt #825 (2023-12-13), "setting of fixed_om_costs severly limiting modeling horizon/performance".** Title only. — [SpineOpt#825](https://github.com/spine-tools/SpineOpt.jl/issues/825)
- **oemof-solph #1064 (2024-03-26), "Implement alternative back-end to Pyomo (e.g. linopy)".** "Model building: 5 s … Solving (with gurobi): 15 s … Results processing. 5 s … only half of the time is spent on solving" (the author notes these are "not the actual times"). — [oemof-solph#1064](https://github.com/oemof/oemof-solph/issues/1064)
- **oemof-solph #505 (2018-06-30).** "Pyomo tends to be quite slow with lots of memory usage for large LPs. This has been discussed by other frameworks like calliope, PyPSA or urbs as well." — [oemof-solph#505](https://github.com/oemof/oemof-solph/issues/505)
- **oemof-solph #1351 (2026-11-13).** Running "multiple solves of various models in a single process … killed my memory" (memory leak with appsi solvers). — [oemof-solph#1351](https://github.com/oemof/oemof-solph/issues/1351)
- **GenX #833 (2025-02-18).** A suggestion to use JuMP `direct_model`: "Direct-mode uses half the memory". — [GenX.jl#833](https://github.com/GenXProject/GenX.jl/issues/833)
- **GenX #908 (2026-05-05).** "There is a memory spike when writing results … can cause out of memory issues with large jobs on a HPC. There are many copies of data being made during the write process." — [GenX.jl#908](https://github.com/GenXProject/GenX.jl/issues/908)
- **FINE #897 (2026-11-12).** The issue asks for an optional LP or MPS hand-over "to roughly halve peak memory for large models". — [FINE#897](https://github.com/FZJ-IEK3-VSA/FINE/issues/897)
- **FINE #889 (2026-11-12).** It points to "#120 (loading large result files is slow)" and notes that the netCDF reader opens the file "about 50" times. — [FINE#889](https://github.com/FZJ-IEK3-VSA/FINE/issues/889)
- **Pyomo forum (2016, older than the target window).** "the memory usage of python during the formulation step is huge, in the order of many tens of GB", while the solver needed a few GB (search snippet). — [pyomo-forum](https://groups.google.com/g/pyomo-forum/c/2ayvSKw-PKw/m/e4wuIdjpDQAJ)

**Long runs, checkpointing, rolling and myopic horizons:**
- **GenX #658 (2024-03-19).** "GenX runs with longer time domain reduction periods can extend to multiple days, and oftentimes corporate computers force restart on e.g., Patch Tuesday causing a loss of all work." — [GenX.jl#658](https://github.com/GenXProject/GenX.jl/issues/658)
- **GenX #904 (2026-02-17).** "GenX can run myopic multi-stage internally, but because it retains all model stages in memory this feature is not always practical. Users often run a single stage model and manually feed results forward." — [GenX.jl#904](https://github.com/GenXProject/GenX.jl/issues/904)
- **GenX #916 (2026-07-17).** "setting `New_Build=0` for a candidate resource in a later stage causes **all capacity built in prior stages to be lost**." — [GenX.jl#916](https://github.com/GenXProject/GenX.jl/issues/916)
- **Temoa #395 and #398 (2026-10).** "Myopic unit commitment output loses earlier periods" and "Myopic unit commitment start costs are discounted to each window's first period". Titles only. — [temoa#395](https://github.com/TemoaProject/temoa/issues/395); [temoa#398](https://github.com/TemoaProject/temoa/issues/398)
- **SpineOpt #411 (2021-10-18), "Update variable and constraint names after rolling".** Title only. — [SpineOpt#411](https://github.com/spine-tools/SpineOpt.jl/issues/411)

**Temporal resolution and clustering:**
- **GenX #659 (2024-03-19).** "GenX runtimes typically limit the number of representative days in a simulation to ~50 per year … the TDR weighted periods can have non-trivially different annual averages vs the full 8760 h input." — [GenX.jl#659](https://github.com/GenXProject/GenX.jl/issues/659)
- **Time-series aggregation review (Energies 13(3):641, 2020).** It reviews 130 publications. Growing model complexity "often results in computationally intractable programs" (search snippet). — [MDPI](https://mdpi.com/1996-1073/13/3/641)
- **Temporal resolution and accuracy (arXiv 1909.05597, 2019).** "temporal resolution has a stronger impact on the accuracy of the optimization than the spatial resolution, especially if the model has temporal linking constraints" (search snippet). — [ar5iv 1909.05597](https://ar5iv.labs.arxiv.org/html/1909.05597)

**Model coupling:**
- **Rosendal et al. (Applied Energy 385, 2025).** Soft-linking "is frequently applied to increase the modelling scope, but … evaluations of the soft-linking strategy itself are rarely investigated or documented" (search snippet). — [IDEAS](https://ideas.repec.org/a/eee/appene/v385y2025ics0306261925002429.html)
- **TIMES–CGE linking analysis (ClimateXChange, Scotland).** "the consistency of the baseline in the two models is fundamental for a successful soft-link". Convergence criteria "do not have a single general solution" (search snippet). — [ClimateXChange](https://www.climatexchange.org.uk/unique_id/e9b5e094ac5442ed9cf5b1e7e82093ff/)
- **Model-linking challenges (Keppo et al., IIASA PURE 20939; RSER, per the search summary 2026).** "little attention has so far been paid to the trade-offs of linking and how it affects interpreting the results" (search snippet). — [IIASA PURE](https://pure.iiasa.ac.at/20939)
- **SpineOpt #318 (2021-02-08), "Linking related optimizations" (44 comments).** Title only. — [SpineOpt#318](https://github.com/spine-tools/SpineOpt.jl/issues/318)
- **Chang et al. 2021.** The survey lists "understanding how tools are coupled together" as a gap (see section 2). — [IIASA PDF](https://pure.iiasa.ac.at/id/eprint/17105/1/1-s2.0-S0306261921002476-main.pdf)

### Inferences
- **"Build in seconds, debug in minutes"** is well supported. A Calliope user waits 10 minutes to build a 3-node model that solves in under 2 seconds. SpineOpt's own team considers a rewrite in Rust or C. SpineOpt's planned fix is literally "Store data in DataFrames so we can use their optimised join", which is the specsolve design.
- **New theme: results I/O is the hidden bottleneck.** GenX runs out of memory writing results, FINE opens one file about 50 times to read results, and oemof spends as long on results processing as on the build. Headline seed: "Tables in, tables out, with no memory spike at the end."
- **New theme: checkpoint every solve.** GenX users lose multi-day runs to forced reboots and feed myopic stages forward by hand. A parquet archive per solve plus built-in rolling horizons maps directly to GenX #658 and #904.
- **Coupling:** the soft-link workflow (export results, reshape, feed the next model) is undocumented and rarely evaluated. Table-native outputs make the link file the result itself.

### Gaps
- No measured cross-framework build-time benchmark was retrieved. The numbers above are single-user reports.
- forum.openmod.org threads on performance could not be reached.

---

## 7. Calliope's rationale for moving its math into YAML (0.7) and community reaction

### Takeaway
Calliope 0.7 moved all built-in math from Python into YAML. It generates its math documentation from that YAML and added pre-validation of math strings before the costly build. Users welcomed the flexibility, but report custom-math errors, a slow build loop, and the limits of a syntax designed around Calliope's base math.

### Cited Findings
- **Changelog: math is no longer hardcoded.** "Pre-defined math is no longer hardcoded in Python. Instead, it is split by mode and feature into separate YAML files - `base.yaml`, `operate.yaml`, `spores.yaml`, `milp.yaml` and `storage_inter_cluster.yaml`." — [CHANGELOG.md](https://github.com/calliope-project/calliope/blob/main/CHANGELOG.md)
- **Changelog: generated math docs.** "Math documentation is generated from the YAML math, including a list of pre-defined parameters, units, default values, cross-references in both directions ("uses" and "used in") (#643)". — [CHANGELOG.md](https://github.com/calliope-project/calliope/blob/main/CHANGELOG.md)
- **Changelog: checks before the build.** "`config.init.pre_validate_math_strings` (default False) to scan the math definition for parsing errors at model initialisation, i.e. before the much more expensive optimisation problem build." — [CHANGELOG.md](https://github.com/calliope-project/calliope/blob/main/CHANGELOG.md)
- **Changelog: replacing built-in math.** "`config.init.math_paths` to name and point to additional math files, which can then be requested via `config.build.extra_math` or used to _replace_ pre-defined math entries". This resolves the request in #606. — [CHANGELOG.md](https://github.com/calliope-project/calliope/blob/main/CHANGELOG.md)
- **Changelog: validation layer.** "`pydantic` is used throughout to document and validate the model configuration, data tables, techs/nodes data, math and general model definition, replacing the JSON schema introduced earlier in the v0.7 development cycle". — [CHANGELOG.md](https://github.com/calliope-project/calliope/blob/main/CHANGELOG.md); discussion in [calliope#726](https://github.com/calliope-project/calliope/issues/726)
- **User-defined math docs.** "As of Calliope version 0.7, all of the internal math used to build optimisation problems is stored in YAML files. The same syntax used for the pre-defined math can be used to define additional math." — [docs source](https://github.com/calliope-project/calliope/blob/main/docs/building_blocks/user_defined_math/index.md)
- **Migration guide: MILP becomes extra math.** "For easier extensibility, the mixed-integer formulation of Calliope is now an extra math option." Custom math is described as "simultaneously more powerful and more human-readable". — [docs/migrating.md](https://github.com/calliope-project/calliope/blob/main/docs/migrating.md)
- **Migration guide: removal of `_equals` constraints.** "With `_equals` constraints, it would trigger a completely different mathematical formulation, which you could not then tweak - you had to rebuild the optimisation problem entirely." — [docs/migrating.md](https://github.com/calliope-project/calliope/blob/main/docs/migrating.md)
- **Earlier position (2018).** In 0.6, YAML custom constraints were removed, and users reached into `model._backend_model` (Pyomo). — [calliope#100](https://github.com/calliope-project/calliope/issues/100)
- **Reaction: parameter declarations.** #642 (2024-07-19) says "the math data and schemas are a bit 'mixed' … `model_def_schema.yaml` contains parameter defaults, which makes looking for them difficult" and proposes that users "explicitly declare new parameters in yaml files". #446 asks for parameters in the math files to "protect against typos". — [calliope#642](https://github.com/calliope-project/calliope/issues/642); [calliope#446](https://github.com/calliope-project/calliope/issues/446)
- **Reaction: build cost and errors.** #781 reports a 10-minute build that makes "debugging … especially when adding custom math" hard. #420, #590, #735 and #827 report custom-math errors. #801 (2025-08-22) is "Docs: where: filter syntax". — [calliope#781](https://github.com/calliope-project/calliope/issues/781); [calliope#801](https://github.com/calliope-project/calliope/issues/801)
- **Reaction: data-dependent math.** #733 (2025-01-27) is "Conducting math operations using dimension data". It was resolved by allowing dimensions in `where` and `expression` strings (changelog). — [calliope#733](https://github.com/calliope-project/calliope/issues/733)

### Inferences
- Calliope independently validates the mathspec thesis: YAML math, generated docs, pre-build validation and replaceable base math. Its math, however, stays tied to Calliope's data model ("our focus was on building a system to implement Calliope's base math"). It is not data-free, not typeset to LaTeX or Typst for papers, and not portable across engines.
- "Pre-validate math strings" defaults to False and checks parsing only. Full load-time checking is still a differentiator.

### Gaps
- The callio.pe news post on the 0.7 pre-release (Mar 2025) and the Zulip discussions could not be fetched, so no verbatim community-reaction quotes outside GitHub were gathered.

---

## 8. New themes beyond the covered list: which complaints suggest fresh headlines?

### Takeaway
Seven themes recur with direct evidence and are not in the covered list. The strongest are silent wrong answers, error messages that name the culprit, and results I/O and checkpointing.

### Cited Findings
- **Silent wrong answers from unsupported combinations (SpineOpt #1236, 2025-06-24).** "If the user is not warned and the optimization silently fails then this has potential create flow on effects which are very expensive (eg. sub-optimal hardware implemented)." It references #643, "Invalid formulations when a pair of conneted `unit` and `node` use different stochastic/temporal structures". — [SpineOpt#1236](https://github.com/spine-tools/SpineOpt.jl/issues/1236); [SpineOpt#643](https://github.com/spine-tools/SpineOpt.jl/issues/643)
- **Silent wrong answers: FINE accepts NaN (#890, 2026-11-12).** "If a period is passed as a series of NaN, FINE accepts the model … NaN becomes the variable bounds". — [FINE#890](https://github.com/FZJ-IEK3-VSA/FINE/issues/890)
- **Silent wrong answers: FINE drops a balance (#896, 2026-11-12).** "For a commodity in `pooledCommodities`, the commodity balance is only enforced for the locations of its pools." — [FINE#896](https://github.com/FZJ-IEK3-VSA/FINE/issues/896)
- **Silent wrong answers: urbs and GenX.** urbs #311 calculates investment cost twice, and GenX #916 loses capacity across stages (see sections 2 and 6).
- **Errors that name the culprit.** Calliope #745 and #472, otoole #80, #182 and #13, and Berendes 2022 (see section 5).
- **Units as part of the model.** GenX #455 (docs per MWh versus inputs per MMBtu) and Calliope #775 (2025-06-30), "Clarify that technology costs must be provided per kW output". — [calliope#775](https://github.com/calliope-project/calliope/issues/775)
- **Results I/O, memory and checkpointing.** GenX #908, #658 and #904, FINE #889 and #897, and oemof #1064 (see section 6).
- **Parquet and tabular input demand.** GenX #875 shows a maintainer adding ".csv, .csv.gz, or .parquet" input. — [GenX.jl#875](https://github.com/GenXProject/GenX.jl/issues/875)
- **Licence-free editing of the math.** The TIMES runtime licence "cannot be used to change the model's equations" (see section 2).
- **Docs maintenance burden on developers.** SpineOpt #800, "a nightmare" (see section 2).
- **Coding agents editing models.** GenX #875 (see section 5).

### Inferences
Candidate headline seeds, each tied to the evidence above:

- "If your model can't run it correctly, it refuses at load, not after the hardware is bought." (SpineOpt #1236)
- "Errors that name the key you mistyped." (Calliope #745, otoole #80)
- "Units live in the spec." (GenX #455, Calliope #775)
- "Every solve checkpointed to parquet, so a reboot costs nothing." (GenX #658)
- "Roll the horizon without hand-feeding results forward." (GenX #904, Temoa #395 and #398)
- "Change an equation without buying a licence." (TIMES / GAMS runtime)
- "The docs are the math, so nobody hand-edits LaTeX." (SpineOpt #800)
- "A spec your coding agent can edit, and the loader checks." (GenX #875)

### Gaps
- None of the 2026 FINE, OSeMOSYS-port or Temoa issues was checked for its filer. Some may come from one systematic audit, possibly related to these tools' own authors. Verify provenance before citing them as independent community complaints.
- Balmorel (GAMS, hosted on GitLab) and PowNet were not covered: there were no reachable trackers in this session, and the GitHub search returned nothing relevant for PowNet.
