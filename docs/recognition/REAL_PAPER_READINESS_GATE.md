# Real Paper Readiness Gate

Current status: not ready.

Default CLI:

```bash
python scripts/check_real_paper_readiness.py --json
```

Default result keeps all readiness flags false:

- `ready_for_single_real_qwen_trial=false`
- `ready_for_three_image_trial=false`
- `ready_for_small_batch_trial=false`

Required before a single real Qwen trial:

- anonymous single image
- validated template
- manual ROI
- Qwen `--check-only`
- explicit real API approval
- sanitized output audit
- parser candidate audit
- review queue audit

Current prohibitions:

- no real class use
- no real batch Qwen
- no formal grading CSV, Excel, or HTML report
- no raw API response saved
- no base64 image output
