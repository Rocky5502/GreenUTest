# Frozen confirmatory configurations

This directory is populated **after excluded pilot work and before held-out execution**.

A frozen run should archive at minimum: code SHA, analysis-plan hash, model IDs/revisions/quantization or canonical hosted model IDs, dataset revisions/snapshot hashes, group-disjoint split IDs/hash, prompt hash, calibration/routing/VoI parameters, local energy budgets, hosted resource-reporting policy, retry/missingness rules, and evaluation environment versions.

Do not hand-edit a frozen file after held-out execution begins. If the protocol must change, create a new named freeze and treat the previous confirmatory run separately.
