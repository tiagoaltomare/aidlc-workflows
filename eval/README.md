# Memory extension observability

Harness for the checks described in `docs/memoria-ciclos/observabilidade-grok-build.md`.
These scripts prepare trials and score artifacts. They do not run the trial battery.
That execution is F5, which this change does not perform.

`run_trials.py` builds headless `grok` commands (`--no-auto-update`, `--always-approve`,
`--output-format streaming-json`) and writes `trials.jsonl`. It alternates which arm
goes first. OpenTelemetry export is requested with `GROK_EXTERNAL_OTEL=1` and
`OTEL_LOG_TOOL_DETAILS=1`. When the `grok` CLI is absent the script records
`grok_cli_absent` and exits 0. Pass `--require-grok` to fail instead.

The headless JSON schema and the `~/.grok/sessions` layout are still unconfirmed.
OpenTelemetry for Grok Build is alpha. Thresholds get calibrated on a baseline run.

Project hooks in `.grok/hooks/memory-observability.json` log tool use and refuse
automatic OpenSpec conflict resolution. The other scripts inject hotfixes and
divergent specs, parse `audit.md`, compare spec and requirement text, check merge
conflicts against `hook-allowlist.txt`, and summarize paired results.
