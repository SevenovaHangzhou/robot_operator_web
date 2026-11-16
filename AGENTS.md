# Agent Contract

- This repository holds the RT-Control operator web only. It belongs to the RT-Control domain and
  is deployed with a `robot_driver` installation; it never starts hardware, writes drive control
  words, enables or resets automatically.
- Versions: `compat.yaml` pins one `robot_driver` commit, `deps.repos` pins `robot_interfaces` to
  the same commit that revision uses. `tools/check_compat.py` must pass. Never use branch names.
- Interfaces: use the public endpoints of `robot_interfaces` or the RT-Control internal endpoints
  listed in `README.md`. A new internal dependency must be added to that list in the same PR.
- No machine or joint names in code or package config; deployments supply them (`--view-model`,
  `status_joint_*`, robot label).
- No guessed defaults or defensive fallbacks; prefer behaviour tests.
- PRs use `.github/pull_request_template.md`; `tools/pr_contract_gate.py` checks it. One purpose per PR.
- Commit, push, merge and deployment follow the same authorization as `robot_driver`: merge only
  when the user asks and CI is green. Hardware actions need explicit authorization.
