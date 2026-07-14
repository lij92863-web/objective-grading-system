# vivo X200 USB 连续采集手工验收

自动化实现完成后，由用户在真实设备上填写。所有项目初始状态均为 `NOT TESTED`；只能改为 `PASS`、`FAIL` 或保持 `NOT TESTED`。

## 环境信息

```text
手机：vivo X200
OriginOS 版本：
Android 版本：
Chrome 版本：
Windows 版本：
USB 线：
ADB 版本：
测试日期：
```

## 真机测试

| # | 检查项 | 状态 | 备注 |
| --- | --- | --- | --- |
| 1 | 手机关闭 Wi-Fi 和移动数据 | NOT TESTED | |
| 2 | USB 连接电脑 | NOT TESTED | |
| 3 | 开启 USB 调试并授权 | NOT TESTED | |
| 4 | 运行启动脚本 | NOT TESTED | |
| 5 | 手机能打开 localhost 页面 | NOT TESTED | |
| 6 | 能申请摄像头权限 | NOT TESTED | |
| 7 | 默认使用后置摄像头 | NOT TESTED | |
| 8 | 能切换摄像头 | NOT TESTED | |
| 9 | 拍一张创建一个 CaptureJob | NOT TESTED | |
| 10 | 连续拍摄 20 张无丢失 | NOT TESTED | |
| 11 | 连续拍摄 60 张无丢失 | NOT TESTED | |
| 12 | 上传过程中能继续拍照 | NOT TESTED | |
| 13 | 双击只生成一张 | NOT TESTED | |
| 14 | USB 拔出时待上传照片保留 | NOT TESTED | |
| 15 | 重新连接并重建 reverse 后续传 | NOT TESTED | |
| 16 | 页面刷新后待上传照片恢复 | NOT TESTED | |
| 17 | 电脑端数量与手机一致 | NOT TESTED | |
| 18 | 重复重试不产生重复 CaptureJob | NOT TESTED | |
| 19 | 已上传图片进入现有复核流程 | NOT TESTED | |
| 20 | FINALIZED session 拒绝继续拍摄 | NOT TESTED | |

## 验收结论

```text
真实设备结论：NOT TESTED
问题记录：
验收人：
```

在全部必要项目完成前，软件实现结论保持：

```text
IMPLEMENTATION_APPROVED_MANUAL_DEVICE_ACCEPTANCE_PENDING
```
