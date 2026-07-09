# Single Trial Cleanup Checklist (R389)

试验后必须检查：

```bash
git status --short
git ls-files data/tmp
git ls-files data/reports
git ls-files | grep -iE '\.(png|jpg|jpeg|webp)$'
```

确认：
- [ ] output 未提交
- [ ] raw response 未保存
- [ ] base64 未输出
- [ ] API key 未出现在日志
- [ ] 真实图片未提交
- [ ] data/tmp 未 track
- [ ] data/reports 未 track
