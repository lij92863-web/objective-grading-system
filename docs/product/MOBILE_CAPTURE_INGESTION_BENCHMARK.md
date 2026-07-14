# Mobile Capture Ingestion Benchmark

本报告只使用合成、非敏感字节测试本地登记链路；不是 vivo X200 真机、真实摄像头或真实识别 benchmark。

## Workload

- 1 个合成班级和 1 场合成考试
- 60 张不同的合成 PNG
- 5 次相同 Blob 重试
- 2 次非法格式请求
- 1 次超限请求模拟

## Metrics

| metric | value |
| --- | ---: |
| attempted_upload_count | 68 |
| accepted_new_count | 60 |
| duplicate_replay_count | 5 |
| invalid_rejected_count | 3 |
| capture_job_count | 60 |
| missing_job_count | 0 |
| unexpected_duplicate_job_count | 0 |
| wrong_source_type_count | 0 |
| wrong_session_binding_count | 0 |
| failed_upload_count | 0 |
| p50_registration_ms | 12.557 |
| p95_registration_ms | 13.909 |

## Result

`PASS` 表示合成 ingestion 登记、去重、来源和 session 绑定满足本阶段门槛；真机项目仍为 `NOT TESTED`。
