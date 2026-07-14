# vivo X200 USB 连续采集 API 契约

所有路由由电脑本地 `127.0.0.1:8765` 提供。手机通过 ADB reverse 访问 `http://localhost:8765`，不是通过公网或 Wi-Fi 访问。

## 页面路由

### `GET /mobile-capture`

返回手机考试选择页。只列出存在班级且状态为 `CAPTURE_READY`、`CAPTURING`、`PROCESSING` 或 `REVIEW_REQUIRED` 的 session。

### `GET /mobile-capture/<session_id>`

返回指定 session 的连续拍摄页。不存在返回 404；状态不允许采集返回 409。

## 健康检查

### `GET /mobile-capture/health.json`

成功固定返回 200：

```json
{
  "ok": true,
  "service": "objective-grading-mobile-capture",
  "transport": "adb-reverse-compatible",
  "real_recognition_enabled": false
}
```

该接口只证明本地 HTTP 服务可用，不证明手机、USB 或 ADB 已连接。

## 图片登记

### `POST /sessions/<session_id>/capture/mobile-web`

请求必须为 `multipart/form-data`，字段如下：

| 字段 | 规则 |
| --- | --- |
| `image` | 必填、非空，JPEG/PNG，最多 32 MiB |
| `client_capture_id` | 必填，1–128 个受限 ASCII 字符 |
| `captured_at` | 必填 ISO-8601 时间字符串，最多 64 字符 |
| `capture_method` | `IMAGE_CAPTURE` 或 `CANVAS` |
| `device_label` | 可空，最多 200 字符 |
| `device_id` | 可空的浏览器设备标识/摘要，最多 200 字符 |
| `facing_mode` | `environment`、`user`、`left`、`right` 或 `unknown` |
| `width` / `height` | 1–16384 的整数，仅作不可信元数据 |
| `mime_type` | `image/jpeg` 或 `image/png`，须与 multipart MIME、扩展名和签名一致 |

客户端文件名只参与扩展名校验。服务端存储路径由随机任务 ID 生成，目录穿越字符串不能控制路径。

新任务返回 201：

```json
{
  "ok": true,
  "capture_job_id": "...",
  "duplicate": false,
  "state": "QUEUED",
  "warning": "",
  "server_received_at": "..."
}
```

同一内容重试返回 200 和原任务：

```json
{
  "ok": true,
  "capture_job_id": "原任务 ID",
  "duplicate": true,
  "state": "REVIEW_REQUIRED",
  "warning": "该图片已进入队列",
  "server_received_at": "..."
}
```

错误始终返回 JSON：

| HTTP | 含义 |
| --- | --- |
| 400 | 字段、元数据、空文件或请求格式错误 |
| 404 | session 不存在 |
| 409 | session 状态不允许，或同一 client ID 对应不同内容 |
| 413 | Content-Length 或图片内容超过限制 |
| 415 | MIME、扩展名或文件签名不受支持/不一致 |
| 500 | 内部登记失败；不得假装成功 |

客户端只有在 `ok=true` 且收到非空 `capture_job_id` 后，才可删除 IndexedDB 中的 Blob。

## 采集状态

### `GET /sessions/<session_id>/capture/status.json`

只读取路径中的 session。不存在返回 JSON 404。成功返回：

```json
{
  "ok": true,
  "session_id": "...",
  "session_state": "REVIEW_REQUIRED",
  "counts": {
    "total": 20,
    "queued": 2,
    "processing": 1,
    "review_required": 17,
    "confirmed": 0,
    "excluded": 0,
    "failed": 0,
    "mobile_total": 20
  },
  "recent": [
    {
      "capture_job_id": "...",
      "state": "REVIEW_REQUIRED",
      "source_type": "MOBILE_WEB_USB_CAMERA",
      "created_at": "...",
      "error_code": ""
    }
  ]
}
```

`recent` 最多 20 项，按创建时间倒序；响应不含本地路径、原图、识别候选或学生信息。
