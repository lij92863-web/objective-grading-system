# Single Real Qwen Command Template (R387)

## 单张真实 Qwen 调用命令模板

```bash
python scripts/run_single_qwen_real_trial.py \
  --manifest <local-untracked-manifest.json> \
  --roi <local-untracked-roi.json> \
  --allow-real-api \
  --confirm-anonymous \
  --check-only-passed \
  --api-key-env QWEN_API_KEY \
  --max-calls 1 \
  --output data/tmp/<request_id>_sanitized.json
```

## 注意事项
1. 不要把 key 写进命令
2. 不要提交 output
3. 不要提交图片
4. 不要保存 raw response (`--save-raw-response` 必须不传)
5. 不要输出 base64 (`--emit-base64` 必须不传)
6. 不要进入 batch

## 执行前检查清单
- [ ] 图片是匿名 synthetic
- [ ] manifest 已验证通过
- [ ] ROI 已验证通过
- [ ] dry-run 已通过
- [ ] check-only 已通过
- [ ] 已运行 fake replay 并检查 parser audit
- [ ] API key 已设为环境变量 (不写在命令中)
- [ ] output 路径在 data/tmp
