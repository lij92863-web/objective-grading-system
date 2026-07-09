# Small Batch Gate Policy

Current status: not ready.

Default CLI:

```bash
python scripts/check_small_batch_gate.py --json
```

Default result:

- `ready_for_small_batch=false`

Required before small batch:

- single anonymous image trial passed
- three-image anonymous trial passed
- fixture-driven synthetic batch passed
- model-driven teacher summary passed
- Qwen budget truth passed
- identity exact-code policy passed
- review queue policy passed
- no real data leak

Small batch is still not formal production use. It must not generate official scores or formal class reports.
