# What industry, grid operators, regulators and consultancies need from optimisation models, and where their tools fail

**Method and reliability note (read first).** WebFetch was blocked in this session: `rmi.org` and `www.aemc.gov.au` did not resolve (outside the session's allowed network domains), so I stopped trying further hosts. Every item below comes from WebSearch result excerpts, not from reading the full source. Text in quotation marks is the wording the search excerpt gave for that source. Treat it as a near-verbatim excerpt to re-check against the linked document before it goes into a headline. Where a date comes only from a URL path (for example `/2026-09/`), the notes say so. Items dated before 2018 are marked as outside the 2018 to 2026 window.

**New themes, beyond the ones already covered** (tagged `[NEW]` below):
1. The licence fee is the price of taking part. Stakeholders cannot run or check a utility's model without a commercial seat.
2. The vendor decides who may look. Licence terms restrict review, the manual is behind the licence, and one university was reportedly embargoed.
3. A published model does not reproduce the published result. Confidential data is stripped out, the model is tied to one engine version, and it comes with "no warranties".
4. Slow models shrink the scenario space. Run time limits how many risks a planner can test.
5. Backcasting: regulators validate a model against what actually happened, which needs an archive of past runs.
6. Traceability of changes: regulators ask how stakeholder input changed the model, and the answer is missing.
7. Model governance is moving from finance to government analysis: version control, one accountable owner, and vendor models in scope.
8. Key-person risk: a model's logic lives in one person's head.
9. The skills gap: people asked to use optimisation cannot define it, so readability is a requirement.
10. Productionising: testing, replay of historical runs, and shadow runs.

---

## Regulator and stakeholder demands for model transparency in planning processes (AEMO ISP, ENTSO-E TYNDP / ACER, German NEP, UK NESO/Ofgem, US IRP)

### Takeaway
Every major planning regime surveyed has a formal transparency demand on its models. The recurring complaints are that the model is a black box, that stakeholders cannot replicate results, that the model is too slow to test risks, and that nobody explains how stakeholder feedback changed it. The remedies regulators ask for are published input and output data, published equations, model files that match the utility's own, and data that is "open by default".

### Cited Findings

**Australia (AEMO Integrated System Plan, AEMC review of the ISP framework, 2026)**
- ANU Centre for Energy Systems, submission to the AEMC Review of the ISP Framework (Sep 2026, date from the URL path). Per the excerpt, it argues that the "computationally complex black-box models" underpinning the ISP are slow to run, which limits AEMO's ability to test risks and opportunities across development paths. `[NEW: slow models shrink the scenario space]` — [ANU CES submission](https://www.aemc.gov.au/sites/default/files/2026-09/anu_centre_for_energy_systems.pdf)
- Private individual, submission to the AEMC (Sep 2026, date from the URL path). Calls the ISP a "black box" that accepts policy inputs without an economy-wide efficiency test. — [Private individual 2](https://www.aemc.gov.au/sites/default/files/2026-09/private_individual_2.pdf)
- Windlab, submission to the AEMC (Sep 2026, date from the URL path). Values AEMO publishing the underlying PLEXOS model, because it "reduces the barrier to entry" for independent modelling and new participants. This is pro-transparency evidence that a published model is valued. — [Windlab submission](https://www.aemc.gov.au/sites/default/files/2026-09/windlab.pdf)
- Centre for Independent Studies (2024 to 2025). By not publishing the ECMC review of the ISP, AEMO "compromised transparency and public accountability". CIS also criticises the ISP model for assuming perfect foresight of the weather. — [CIS ISP methodology submission](https://www.cis.org.au/?p=121182); [CIS submission to AEMC ERC0369, Feb 2024](https://www.aemc.gov.au/sites/default/files/2024-02/Centre%20for%20Independent%20Studies%20Submission%20to%20ERC0369%20%20Improving%20Workability%20of%20the%20Feedback%20Loop%20FINAL.pdf)
- The AER's transparency review of the Draft 2024 ISP assesses whether AEMO was "adequately transparent" in explaining its inputs and assumptions. It is explicitly not a review of the merits. The regulator's statutory role here is transparency, not correctness. — [AER](https://www.aer.gov.au/node/73373)
- AEMO's consultation summary on the 2026 ISP Methodology (2025): stakeholders called for improved transparency on gas development projections, and AEMO agreed to changes. — [AEMO consultation summary report](https://wa.aemo.com.au/-/media/files/stakeholder_consultation/consultations/nem-consultations/2024/2026-isp-methodology/consultation-summary-report---isp-methodology.pdf?la=en)

**Europe (ENTSO-E TYNDP, ACER)**
- ACER Opinion on the draft TYNDP 2024 scenarios (2024). The draft "still did not fully meet the transparency standards set by the Framework Guidelines", in particular because it gave no detailed reasoning on how stakeholder observations were handled. `[NEW: traceability of changes]` — [ACER news](https://www.acer.europa.eu/news-and-events/news/acer-calls-improvements-entsos-draft-tyndp-scenarios-comply-its-framework-guidelines-2024)
- ACER on the TYNDP 2026 scenarios (2026). Welcomes the structured scrutiny of "assumptions, methods and data" by stakeholders. Says the methodology achieves formal compliance with EU targets but does not capture the structural change needed, and calls for alternative scenarios with more transparency and consultation on key assumptions. — [ACER news](https://acer.europa.eu/news/acer-calls-transparent-eu-infrastructure-scenarios-aligned-energy-and-climate-targets)
- ACER on ENTSOG's draft TYNDP 2024 for gas and hydrogen. Recommends that ENTSOG "improve transparency of project information and methodological choices". — [ACER news](https://www.acer.europa.eu/news/acer-criticises-delays-receiving-entsogs-2024-draft-ten-year-gas-and-hydrogen-network-development-plan-and-recommends-improvements)
- ACER Opinion 07/2017 on the interlinked electricity and gas model (2017, outside the window). The model "shall allow the application of CBA and its verification by various parties". ACER "intends to publish the Submitted Model once it has ensured that there are no legal obstacles". This is an early formal requirement that third parties can verify the model. — [ACER Opinion 07-2017](https://acer.europa.eu/Official_documents/Acts_of_the_Agency/Opinions/Opinions/ACER%20Opinion%2007-2017.pdf)
- ACER Opinion 03/2021 on the methodology of the ENTSO-E draft TYNDP 2020 (2021); I did not read the content. — [ACER Opinion 03-2021](https://acer.europa.eu/Official_documents/Acts_of_the_Agency/Opinions/Opinions/ACER%20Opinion%2003-2021%20on%20the%20methodological%20aspects%20of%20the%20ENTSO-E%20draft%20TYNDP%202020.pdf)
- CAN Europe on the ACER scenario guideline (Aug 2022). "Openness of models would not only increase transparency but also encourage the sharing of innovative modelling approaches." Calls for open data licences and open-source modelling. — [CAN Europe](https://caneurope.org/content/uploads/2022/08/CAN-Europe_views_ACER_scenario_guideline_aug22-1.pdf)
- Open-TYNDP, a collaboration between Open Energy Transition and ENTSO-E (2025 to 2026). It is an open model "benchmarked against TYNDP 2024" as of v0.7, with an Open-TYNDP data store for "fully reproducible runs without third-party data providers". The TSO community itself is moving to an open-model track. — [Open-TYNDP docs](https://open-tyndp.readthedocs.io/en/latest/)

**Germany (Netzentwicklungsplan, BNetzA)**
- The BNetzA consultation on the second draft of the NEP Strom 2037/2045 (Version 2025) opened on 12 June 2026. BDEW sees "erheblichen Nachbesserungsbedarf" (a substantial need for improvement), with more transparency at the centre of its asks. — [BDEW Stellungnahme](https://www.bdew.de/service/stellungnahme-zum-netzentwicklungsplan-strom/)
- bne statement on the NEP 2037/2045 V2025 (24 Aug 2026, date from the file name). It disputes a single modelling assumption, the TSOs' 2-hour battery storage, and argues that the draft's own data refute the claim that ambitious electrification is unaffordable. A single parameter choice drives a headline policy conclusion. — [bne](https://www.bne-online.de/wp-content/uploads/260824_bne-Stellungnahme-NEP-Strom-2037_2045_Version-2025_BNetzA-Konsultation.pdf)
- Öko-Institut study on the NEP 2012 (2012, outside the window, but it is the canonical ask). The input data, "die Gleichungssysteme" (the system of equations) and the output data should be published in a technical annex, on the principle of an open grid and data model. This is direct evidence for "published math equals solved math". — [Öko-Institut 2012](https://www.oeko.de/oekodoc/1593/2012-449-de.pdf)
- UfU paper (2016, outside the window). Unpublished data and calculation models mean the planning cannot be fully followed ("nicht vollständig nachvollziehen"). — [UfU Paper](https://www.ufu.de/wp-content/uploads/2016/11/UfU-Paper_Agnes_Harms.pdf)
- Öko-Institut, commentary on the second draft of the NEP 2021 to 2035 (about 2021). Praises the BNetzA's improved transparency, for example the publication of overload indices. — [Öko-Institut Kommentierung](https://www.oeko.de/fileadmin/oekodoc/Kommentierung_2_Entwurf_NEP_2021_2035.pdf)
- The NEP 2037/2045 V2025 second draft, chapter 2 (Mar 2026). Per the search excerpt, the modelling is questioned and a higher degree of transparency on modelling assumptions is suggested. Low confidence: the excerpt is ambiguous about who says this. — [NEP Entwurf Kap. 2](https://www.netzentwicklungsplan.de/sites/default/files/2026-03/NEP_2037_2045_V2025_2_Entwurf_Kap2.pdf)

**United Kingdom (Ofgem, NESO)**
- Ofgem's decision on the Future Energy Pathways guidance (28 Feb 2025) includes "Section 6 - Improvements to transparency in analysis and outputs". The consultation ran from 13 Aug to 13 Sep 2024. — [Ofgem decision](https://consult.ofgem.gov.uk/energy-transmission/future-energy-pathways-draft-guidance/supporting_documents/Decision_Future_Energy_Pathway_Guidance.pdf); [final guidance](https://www.ofgem.gov.uk/sites/default/files/2025-02/Future_Energy_Pathways_Guidance.pdf)
- Ofgem, as summarised by Utility Week (a members-only article; I saw only the summary). The old Future Energy Scenarios "lacked transparency and regional granularity". Ofgem proposed that input and output data be "treated as open by default for all to use, with the FSO only restricting access where there is a clear reason to do so". This was a consultation proposal; I did not confirm it in the final text. — [Utility Week](https://staging4.utilityweek.co.uk/ofgem-says-eso-should-stop-planning-to-fail)
- NESO's methodology document has sections on "stakeholder feedback on our modelling" and "data transparency". — [NESO document](https://neso.energy/document/353151/download)

**United States (IRP proceedings)**
- The LBNL and Synapse "Best Practices in Integrated Resource Planning" guide (2024), prepared for DOE. "Technical experts have access to review all inputs, outputs, modeling files and can gain access to the modeling software the utilities used." It lists "modeling software licenses, paid for by the utility, for all technically sophisticated stakeholders" as a requirement. — [Synapse/LBNL 2024 guide](https://www.synapse-energy.com/sites/default/files/IRP_Best_Practices_2024_Synapse_LBNL_24-061_1.pdf); [DOE page](https://www.energy.gov/documents/best-practices-integrated-resource-planning-guide-planners-developing-electric-resource)
- LBNL and Synapse IRP training slides (Oct 2024, date from the URL path). Utilities should prioritise transparency and provide modelling licences and data to technical intervenors. — [LBNL-Synapse slides](https://eta-publications.lbl.gov/sites/default/files/2024-10/lbnl-synapse_slides-final.pdf)
- New Mexico's 2022 IRP rules, as cited in LBNL and EPRI material, mandate "reasonable access to modeling software" and the sharing of all modelling information, so that stakeholders can replicate results. — [EPRI attachment](https://restservice.epri.com/publicattachment/96104)
- RMI, "Power Planning to the People" (about Dec 2022). Recommends "requiring utilities to fund stakeholder licenses for their proprietary models, or ... signaling openness to zero-cost open-source models". RMI rebuilt LG&E-KU's 2021 IRP in GenX, which is free on GitHub with the Clp solver, to address stakeholder concerns. — [RMI](https://rmi.org/insight/power-planning-to-the-people/); [pv magazine, 12 Dec 2022](https://pv-magazine-usa.com/2022/12/12/free-genx-model-recommended-for-renewables-advocates-to-conduct-utility-resource-modeling/)

### Inferences
- The regulator's ask is now concrete across jurisdictions: the files that match the utility's, the equations, and the input and output data. That maps directly onto a published spec plus tables in and out. "The equations in a technical annex", the Öko-Institut ask for the NEP, is almost a product description of a typeset spec.
- ACER's complaint that the TSOs gave no reasoning on how stakeholder observations were handled points to a need for a diffable model: what changed in the formulation between the draft and the final plan. A text spec under version control gives that for free.
- The ANU point turns speed into a transparency issue, not only a convenience: a slow model means fewer scenarios tested, and so less scrutiny.

### Gaps
- I could not read the full ANU, Windlab or RMI texts (host blocked), so the quotes come from search excerpts.
- I found no source saying the current NEP electricity-market model is closed, and no NESO statement on releasing model code.
- No US commission ruling that weighs intervenor access against trade-secret claims turned up.

---

## Commercial tools (PLEXOS, Aurora, PROMOD, Antares, TIMES/VEDA, GAMS in-house): cost, black boxes, lock-in, the formulation out of reach

### Takeaway
The best-evidenced pain is not "the solver is bad". It is that the licence gates who may participate and check, and that the vendor's terms (named-user seats, use restrictions, a manual behind the licence) set who may see the model. In a 2026 Iowa ethics opinion, a vendor quote put PLEXOS at $75,000 to $90,000 for the platform plus $20,000 to $25,000 per named user.

### Cited Findings
- `[NEW: the licence fee is the price of taking part]` Iowa Ethics and Campaign Disclosure Board, advisory opinion 26-AO-1103 (2026). Energy Exemplar quoted "$75,000 to $90,000" for the PLEXOS platform and "$20,000 to $25,000" for one named-user licence. The opinion concerns a free one-year licence offered to state commissions for MISO transmission planning, which was examined as a possible gift. — [Iowa ethics opinion](https://ethics.iowa.gov/advisory-opinion-26-ao-1096-0)
- `[NEW]` AriSEIA in the Arizona Corporation Commission IRP process (date not confirmed). Licences plus a consultant to run the required portfolios would "cost ~$175,000", which makes the process "cost prohibitive for many stakeholders". Per the excerpt, staff dropped the stakeholder-modelling requirement on cost grounds. — [AriSEIA recommendations](https://www.ariseia.org/news/ariseia-submits-recommendations-on-new-acc-irp-process)
- `[NEW: the vendor decides who may look]` Dominion Energy South Carolina (DESC) IRP stakeholder FAQ (undated). Energy Exemplar "requires that stakeholders that wish to view the utility's model within PLEXOS sign a limited license", and "the PLEXOS manual cannot be provided without a license". One FAQ item flags that a licence limited to reviewing price or power-cost forecasts would exclude IRP use. The utility's workaround is Excel spreadsheets of all input and output data. — [DESC FAQ, miscellaneous](https://desc-irp-stakeholder-group.com/FAQ/Miscellaneous-Other); [DESC FAQ, capacity expansion model](https://desc-irp-stakeholder-group.com/FAQ/Selection-of-Capacity-Expansion-Model)
- `[NEW]` The PLEXOS EULA, per the search excerpt, restricts modifying the software and limits use to internal business operations. — [PLEXOS EULA](https://web.plexosproject.com/eula)
- `[NEW]` openmod forum thread, "Energy Exemplar/PLEXOS embargoes whole University for developing Open-Source Software" (about 2025; the date is uncertain). A TU Berlin student was reportedly denied a licence because another research group there develops PyPSA. The post calls PLEXOS "one of the world's most widely used proprietary (and black-box) energy planning tools". This is an advocacy source; I could not retrieve Energy Exemplar's response. A follow-up thread (Nov 2025) asks whether it is even legal to use or contribute to a PLEXOS-to-PyPSA data converter. — [openmod forum](https://forum.openmod.org/t/energy-exemplar-plexos-embargoes-whole-university-for-developing-open-source-software/4984)
- A third-party researcher who reused AEMO's 2024 ISP model notes that the PLEXOS model files need a licence to the commercial Energy Exemplar software, while the annual results can be read without one. — [Mendeley dataset](https://data.mendeley.com/datasets/ggr5v47vkj/1)
- Counterpoint from the vendor: Energy Exemplar says PLEXOS can make IRP modelling accessible to more stakeholders, and it runs a no-cost academic licence programme that requires users to share how PLEXOS was used. — [Energy Exemplar IRP playbook](https://energyexemplar.com/product-news/plexos-playbook-for-irp-integrated-resource-planning); [Global University Program](https://www.energyexemplar.com/global-university-program)
- RiverLogic, a vendor blog (undated), "Is Your Choice of Optimization Software a Long-term Risk?". Frames the software choice and the key individuals who maintain it as one long-term risk. — [RiverLogic](https://download.riverlogic.com/blog/choice-of-optimization-software-a-long-term-risk)

### Inferences
- Headline material: a published formulation needs no seat to read, and a no-cost engine needs no $20,000 seat to rerun. The DESC workaround (Excel exports of inputs and outputs, because the model itself cannot be shown) is the gap that "tables in, tables out" plus a readable spec closes.
- A vendor that can refuse a licence can decide who audits a public plan. That is a governance argument, not only a cost argument.

### Gaps
- No evidence turned up on Aurora, PROMOD, Antares or TIMES/VEDA specifically. I found no complaint, with a source, about being unable to see or change the PLEXOS formulation itself, beyond "black box" labels.
- I found no current list prices from the vendors.

---

## Confidential data: NDAs, data rooms, "open model, closed data"

### Takeaway
"Open model, closed data" is already the practice at AEMO and ENTSO-E. Its failure mode is that the published model cannot reproduce the published result. US IRPs handle confidentiality through redacted filings under seal and NDAs.

### Cited Findings
- `[NEW: a published model does not reproduce the published result]` AEMO's 2022 ISP model instructions (2022). Confidential data was removed from the package, so the model may not reproduce the exact outcomes in the published 2022 ISP. — [AEMO 2022 ISP model instructions](https://www.aemo.com.au/-/media/files/major-publications/isp/2022/2022-documents/2022-isp-model-instructions.pdf?la=en)
- `[NEW]` AEMO's 2024 ISP PLEXOS model instructions (2024). AEMO makes no warranties and provides the model for stakeholders' information only. The model "may work in other PLEXOS versions" but AEMO has not tested them. The 2022 model ran in "PLEXOS 8.3 Release 9". Reproduction is tied to one vendor engine build. — [AEMO 2024 ISP PLEXOS model instructions](https://aemo.com.au/-/media/files/major-publications/isp/2024/supporting-materials/2024-isp-plexos-model-instructions.pdf?la=en)
- AEMO has published model files with setup guides since at least the 2018 and 2019 ESOO cycles. — [2019 ESOO model instructions](https://aemo.com.au/-/media/Files/Electricity/NEM/Planning_and_Forecasting/NEM_ESOO/2019/2019-ESOO-Model-Instructions.pdf)
- ENTSO-E's TYNDP 2018 data guide (2018). Most data is public, with exceptions "when the data fall under some national confidentiality legal obligation". — [ENTSO-E DataExpertise](https://tyndp-data.netlify.app/Documents/TYNDP%20documents/TYNDP2018/consultation/Technical/DataExpertise.pdf)
- ENTSO-E's TYNDP 2020 dataset specification (2020). Its data policy has "the ultimate objective of ensuring, when relevant, open data license". — [ENTSO-E spec](https://eepublicdownloads.entsoe.eu/clean-documents/CIM_documents/Grid_Model_CIM/TYNDP_2020_ENTSO-E_dataset_specificationv01.pdf)
- PEMMDB (Nov 2026; flag the date). ENTSO-E runs about 10 data collections a year for 40 TSOs on PEMMDB, which feed ERAA, TYNDP and the Seasonal Outlook. — [IT Brief](https://itbrief.co.uk/story/entso-e-boosts-data-collections-with-pemmdb-platform)
- US IRP practice. NIPSCO asked the commission to treat its 2016 IRP inputs as "confidential, proprietary, competitively sensitive and/or trade secret" and to file them redacted and unredacted under seal (2016, outside the window). Vectren South filed a nonredacted IRP under a "Standard Form Nondisclosure agreement" (2014, outside the window). — [NIPSCO petition](https://www.in.gov/iurc/files/NIPSCO_Verified-Petition_11012016.pdf); [SIGECO petition](https://www.in.gov/iurc/files/SIGECO_44556_PETITION_2014_IRP.pdf)
- Pfenninger et al., "Opening the black box of energy modelling: Strategies and lessons learned", Energy Strategy Reviews 19 (2018) 63 to 71, 24 openmod authors. Says the transparency of energy models and data is "of particular importance" because of their "policy relevance and contested nature". It covers IP ownership, licensing, "appropriate modelling languages" and distribution. I could not confirm its section on confidential data. — [arXiv 1707.08164](https://arxiv.org/abs/1707.08164); [TU Delft repository](https://repository.tudelft.nl/record/uuid:a0a6fb7a-5b7d-48a5-8d2a-8e28e23329eb)

### Inferences
- AEMO's own disclaimer ("may not reproduce the exact outcomes") is the strongest available proof that "share the formulation, keep the data" needs the formulation to be separable from the data and the engine. A spec that loads and validates without data, and that a second engine runs, fixes both of AEMO's caveats: the stripped data and the untested PLEXOS versions.

### Gaps
- I found no source on synthetic data or clean-room data rooms used for energy models specifically.

---

## Model governance and quality assurance: validation, audit trails, version control, reproducing a decision years later, model risk management

### Takeaway
Finance (SR 11-7, reportedly being replaced by SR 26-2) and UK government (the AQuA Book, revised 2025) both treat models, vendor models included, as governed assets. They require version control, validation and a named accountable owner. In energy, the closest practice is the regulator-commissioned backcast: run the model on past years and compare it with what happened.

### Cited Findings
- SR 11-7 (2011, the US Federal Reserve and OCC, outside the window but in force through the period). Covers "development, implementation, and use; validation; and governance, policies, and controls". The definition of a model includes approaches with qualitative or expert-judgement inputs, provided the output is quantitative. — [ValidMind summary](https://docs.validmind.ai/about/use-cases/sr-11-7.html)
- SR 11-7 "explicitly states that model risk management applies to vendor and third-party models — not just internally developed ones" (secondary summary). — [Ryan O'Connell Finance](https://ryanoconnellfinance.com/model-risk-management/)
- Status flag: an IBM Promontory document says a new framework, designated SR 26-2, replaces SR 11-7 and SR 21-8. It "largely preserves the underlying principles" but takes "a higher-level approach with less detailed guidance". This is one source, not verified on the Fed's site. — [IBM Promontory](https://www.ibm.com/downloads/documents/us-en/15db806050424f33)
- Federal Reserve OIG (Dec 2022) audited model risk management of the Board's own SABR and BETR models. Even the regulator's own models get an MRM audit. — [Fed OIG report](https://oig.federalreserve.gov/reports/board-model-risk-management-SABR-BETR-models-dec2022.pdf)
- `[NEW: model governance outside finance]` The AQuA Book, revised edition (UK Government Analytical Function, 10 June 2025). A "robust version control process" should exist so that changes are assured, because analysis "needs several cycles to develop, use and update models". "A team or committee may fulfil each role, with a single individual holding overall accountability." Business-critical analysis needs "a single senior responsible officer". Validation measures include "reproducibility". The QA tools cover models "including those from third parties". — [AQuA Book revision, lifecycle](https://best-practice-and-impact.github.io/aqua_book_revision/analytical_lifecycle.html); [analysis chapter](https://best-practice-and-impact.github.io/aqua_book_revision/analysis.html); [home](https://best-practice-and-impact.github.io/aqua_book_revision)
- The UK "Duck Book", on QA of code for analysis. It covers "structuring code, documentation, version control, data management, testing, peer review and automation" in order to improve reproducibility. — [QA of code guidance](https://best-practice-and-impact.github.io/qa-of-code-guidance/intro.html)
- `[NEW: backcasting]` The Irish SEM Committee engaged NERA to validate the SEM PLEXOS model by comparing its results with SEM outturn: the 2021 to 2029 model (2021) and again for 2024 to 2032 (Mar 2025). This is a recurring regulator ritual of input validation and backcasting. — [SEM-21-086](https://www.semcommittee.com/files/semcommittee/media-files/SEM-21-086%20SEM%20PLEXOS%20Model%20(2021-2029)%20Input%20Validation%20and%20Backcast%20Report.pdf); [SEM-25-010](https://www.semcommittee.com/files/semcommittee/2025-03/SEM-25-010%20SEM%20PLEXOS%20Model%20Validation%202024-2032%20Backcast%20Report.pdf)
- McKinsey, "The evolution of model risk management" (undated in the excerpt). — [McKinsey PDF](https://mckinsey.com/~/media/McKinsey/Business%20Functions/Risk/Our%20Insights/The%20evolution%20of%20model%20risk%20management/The-evolution-of-model-risk-management.pdf)

### Inferences
- An archive of every solve (spec, inputs, outputs and versions together) is what a backcast, an MRM validation file and an AQuA "version control process" all need. Candidate headline angle: "every plan is its own audit file".
- Because SR 11-7 brings vendor models into scope, a closed formulation is a validation liability: the validator cannot inspect what it must validate.

### Gaps
- I found no FERC, NERC or state-PUC guidance applying formal model risk management to utility planning or optimisation models. I also found no source on reproducing a specific energy decision years after the fact.

---

## Key-person risk and knowledge transfer

### Takeaway
The evidence is thin and mostly from vendor blogs, but consistent: an optimisation model's logic is often concentrated in "a single person", and handover sessions do not transfer tacit knowledge. Gurobi's surveys show a wide skills gap among the people expected to use optimisation.

### Cited Findings
- `[NEW: key-person risk]` RiverLogic, a vendor blog (undated). "full knowledge of each model's logic remains concentrated within a very small team of people; sometimes only a single person." Managers should not accept a model as a "black box" simply because senior management does not understand it. — [RiverLogic](https://riverlogic.com/?p=3415)
- CloudApper (general legacy IT, undated). When the last person who understands a system leaves, the damage arrives "incrementally ... initially manageable and eventually becomes a crisis". — [CloudApper](https://www.cloudapper.ai/?p=168995)
- Fabric (general, undated). Knowledge-transfer sessions are the standard response, but capturing knowledge "continuously as a by-product of daily work" works better. Their test: "who would the team call if something went wrong at 2am?" — [Fabric](https://fabric.so/blog/key-person-risk)
- `[NEW: the skills gap]` Gurobi, State of Mathematical Optimization in Data Science 2023 (Oct 2023), a survey of 569 data scientists. Of the 63% who claimed to understand mathematical optimisation, "only 57% could correctly define what it is". — [Gurobi newsroom](https://www.gurobi.com/company/newsroom/gurobi-releases-annual-state-of-mathematical-optimization-in-data-science-report); [BusinessWire, 10 Oct 2023](https://www.businesswire.com/news/home/20231010422597/en)
- Gurobi 2025 report (Feb 2025), nearly 500 respondents: 75% want to learn more about mathematical optimisation. The 2024 report had 1,086 respondents. — [BusinessWire, 25 Feb 2025](https://businesswire.com/news/home/20250225823494/en/Gurobi-Releases-the-State-of-Mathematical-Optimization-in-Data-Science-Report); [2024 report](https://www.gurobi.com/resources/reports/report-state-of-mathematical-optimization-in-data-science-2024)
- Gurobi 2022 report: most users experienced optimisation only through "limited-capacity solvers and open-source tools". — [Gurobi 2022 PDF](https://cdn.gurobi.com/wp-content/uploads/State-of-Mathematical-Optimization-in-Data-Science-2022.pdf)
- The AQuA Book's single-accountable-owner rule (above) is the governance answer to key-person risk: an owner is named, so knowledge is not left implicit. — [AQuA Book](https://best-practice-and-impact.github.io/aqua_book_revision/analytical_lifecycle.html)

### Inferences
- A model whose spec typesets to readable math is documentation produced "as a by-product of daily work", in Fabric's phrase. That is a plausible headline for onboarding and key-person risk.

### Gaps
- No energy-specific or GAMS-specific primary evidence (for example a TSO or utility describing a model only one person understood) turned up. Treat this theme as weakly sourced.

---

## In-house optimisation teams outside energy: productionising, data pipelines, deployment, monitoring, scenario runs

### Takeaway
Vendors of decision-ops tooling frame the core problem as the "chasm" between a model that works locally and one that runs in production. Their remedies are versioned model instances, staging environments, CI/CD, batch scenario tests, replay of historical production runs, and shadow and switchback tests. All of this evidence is vendor material.

### Cited Findings
- `[NEW: productionising]` nextmv (vendor blogs, undated). Production readiness means crossing the chasm between "locally developed decision models" and "the production environments where those models provide real-world value". Replaying historical production runs for testing helps address model drift. Its testing is local, batch and production; online, it uses switchback testing (a candidate model against a baseline while both make real decisions) plus acceptance and shadow tests. — [nextmv: road to production](https://nextmv.io/blog/the-road-to-production-is-paved-with-testing-and-experimentation); [6 best practices](https://webflow.nextmv.io/blog/6-best-practices-for-operationalizing-decision-models-from-local-dev-to-production); [testing decision models](https://webflow.nextmv.io/blog/testing-decision-models-how-to-do-it-and-why-it-matters)
- nextmv. "DecisionOps" is positioned as the DevOps or MLOps counterpart for optimisation. Models are organised as versioned apps and instances across development, staging and production, with Git flows and CI/CD. — [What is DecisionOps](https://www.nextmv.io/blog/what-is-decisionops-and-why-does-it-matter); [model versions](https://webflow.nextmv.io/blog/how-can-you-manage-decision-model-versions-on-nextmv-let-us-count-the-ways); [CI/CD for an OR-Tools model](https://webflow.nextmv.io/blog/how-to-set-up-ci-cd-for-an-or-tools-cvrp-model-using-nextmv-decisionops-tools)

### Inferences
- Replaying historical production runs needs exactly an archive of every solve. Scenario tests and batch tests need exactly sweeps. These are existing specsolve features, framed in the language of a buyer outside energy.

### Gaps
- I found no independent (non-vendor) survey of failure modes when productionising optimisation, and no INFORMS practice paper, in this pass. Gurobi's reports, at the level of the search excerpts, did not cover deployment challenges.
