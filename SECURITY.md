# Security policy

## Generated code is untrusted code

GreenUTest may execute LLM-generated tests and third-party benchmark repositories. Treat both as hostile until isolated.

For real experiments:

- use disposable containers/VMs or benchmark-provided images;
- disable outbound network access where feasible;
- mount only dedicated workspaces;
- never expose SSH keys, cloud credentials, API keys, home directories, or unrelated repositories;
- enforce wall-clock and process limits;
- restrict writable paths;
- record infrastructure failures separately from model-test failures;
- never run generated tests as administrator/root unless the benchmark container explicitly requires it and the host is isolated.

The included `dry-run` command never executes third-party or model-generated code.

## Reporting

Do not file secrets or private benchmark artifacts in public issues. Use a private disclosure channel for security-sensitive findings.
