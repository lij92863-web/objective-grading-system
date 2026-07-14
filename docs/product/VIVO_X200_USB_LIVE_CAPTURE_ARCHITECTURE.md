# vivo X200 USB 连续采集架构

## 范围与事实边界

vivo X200 不作为 Windows UVC 摄像头使用。手机 Chrome 调用手机摄像头，HTTP 流量经 USB 数据线上的 `adb reverse tcp:8765 tcp:8765` 到达仅监听 `127.0.0.1:8765` 的本地服务。

本阶段只实现照片可靠保存、上传、创建 `CaptureJob`、进入现有保守处理和显示状态。不接入真实 OMR、OCR、Qwen、AI API、云服务或成绩发布；“上传成功”不代表“识别成功”或“批改完成”。

## 组件职责

```text
vivo X200 Chrome
  -> Mobile Capture Web Controller
  -> ProductFacade / MobileCaptureService
  -> MobileWebCameraSource
  -> CaptureQueue + SQLite + local image storage
  -> existing conservative ProductPipeline
  -> review-required status
```

手机浏览器只负责：

- 请求和切换手机摄像头；
- 通过 `ImageCapture.takePhoto()` 或高质量 canvas fallback 生成照片 Blob；
- 先把 Blob 与有限设备元数据写入 IndexedDB；
- 使用单消费者 worker 顺序上传；
- 在服务器确认 `capture_job_id` 后删除本地 Blob；
- 显示本地队列和服务器采集状态。

Web 层只负责：

- 解析受大小限制的 HTTP 请求；
- 调用 facade/application service；
- 将领域结果映射为 HTML 或 JSON；
- 不直接访问 SQLite，不调用 grading，不生成成绩。

Capture 层负责：

- 校验手机图片、客户端采集标识和有限元数据；
- 以 SHA-256 在同一 session 内精确去重；
- 绑定 `client_capture_id` 与内容摘要，阻断同一 ID 对应不同内容；
- 安全保存图片并创建 `CaptureJob`；
- 记录 `MOBILE_WEB_USB_CAMERA` 来源和采集审计元数据；
- 在数据库失败时移除未发布文件。

Pipeline 层负责：

- 对已经创建的 `CaptureJob` 运行现有保守处理；
- 在没有真实识别器时产生待复核证据和状态；
- 不把候选结果写成最终答案。

## 采集与处理解耦

拍照按钮只等待 Blob 成功写入 IndexedDB，随后立即恢复；它不等待上传和服务器处理。上传 worker 与摄像头操作独立，同一时间最多上传一张。服务器登记成功后调用现有轻量保守 pipeline；该调用不锁住手机的下一次拍照。处理失败被记录为失败状态，已可靠登记的原图和任务不会被伪装成识别成功。

不引入无限线程池、无人管理的后台 worker 或新的第三方依赖。

## 数据一致性与故障模型

- 文件使用服务器生成的任务 ID 命名，客户端文件名不能控制路径。
- 图片临时文件、正式图片、`capture_jobs` 和 `mobile_capture_receipts` 在一个受控注册操作中协调；异常时回滚数据库并清理本次文件。
- 同一 Blob 重试返回原任务；同一 `client_capture_id` 携带不同 Blob 时 fail-closed。
- session 只在 `CAPTURE_READY`、`CAPTURING`、`PROCESSING` 或 `REVIEW_REQUIRED` 时接收照片。
- `FINALIZED`、`ARCHIVED` 和未准备 session 均拒绝上传。
- IndexedDB 中未获服务器确认的 Blob 不因刷新、USB 中断或暂时网络失败而删除。

## 安全边界

- 服务继续监听 `127.0.0.1`，不开放到局域网或公网。
- 图片上限统一为 32 MiB；只接受签名、扩展名和 MIME 一致的 JPEG/PNG。
- width/height 只作为不可信元数据记录，不用于断言真实图像尺寸。
- 状态接口不返回绝对路径、图片内容或学生敏感信息，recent 有固定上限。
- 手机页面不得直接改数据库、调用 grading、生成成绩或把候选结果写成最终答案。
- ADB 工具不下载二进制、不修改 PATH/驱动/手机设置，也不绕过 USB 调试授权。

## 真机验收边界

自动化只能验证代码、合成数据、HTTP 和脚本静态行为。摄像头权限、默认后置摄像头、USB 断线恢复和连续 20/60 张必须由用户使用 vivo X200 手工验收；完成前结论只能是 `IMPLEMENTATION_APPROVED_MANUAL_DEVICE_ACCEPTANCE_PENDING`。
