# Workflow map

Runtime surface classification: `full_governed_surface`

| Workbench | Lifecycle placement | Transactions | Inspect views | Artifact families |
|---|---|---|---|---|
| upstream_intake_and_baselines | covered_gates: GT-030, GT-050, GT-060 | inspect, draft, commit, validate | catalog, baselines, lineage | DIP, SPEC, ARCH, INI |
| ch_and_td_readiness | covered_gates: GT-110 | inspect, draft, commit, validate | catalog, readiness, lineage | CH, TD, EV, DEC |
| design_candidate_authoring | lifecycle_span: GT-110 -> GT-115 | inspect, draft, validate | catalog, design_candidates | DC |
| design_selection | covered_gates: GT-115 | inspect, draft, commit, validate | catalog, design_selection | DC, DB, EV, DEC |
| ci_authoring | lifecycle_span: GT-115 -> GT-120 | inspect, draft, validate | catalog, implementation_scope | CI |
| ci_selection | covered_gates: GT-120 | inspect, draft, commit, validate | catalog, ci_selection | CI, EV, DEC |
| selected_ci_application | lifecycle_span: GT-120 -> GT-130 | inspect, commit, validate | catalog, change_surface | CI |
| verification_and_closure | covered_gates: GT-130 | inspect, draft, commit, validate | catalog, verification, closure | CI, EV, DEC |
| issue_operations | lifecycle-independent | inspect, draft, commit, validate | catalog, issues | IS |
| governance_onboarding | lifecycle-independent | inspect, draft, validate | catalog, onboarding | INI, CH, TD |
