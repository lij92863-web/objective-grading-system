import dataclasses
import html
import json
import mimetypes
import re
from pathlib import Path
from typing import Mapping

from app.capture.mobile_web_camera_source import MobileCaptureError
from app.product.capture.mobile_capture_service import MobileCaptureServiceError
from app.roster.roster_validator import RosterImportState

from .facade import ProductFacade, ProductPaths


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATE_ROOT = PROJECT_ROOT / "web" / "templates" / "product"


@dataclasses.dataclass(frozen=True)
class UploadedFile:
    filename: str
    content: bytes
    content_type: str = ""


@dataclasses.dataclass(frozen=True)
class WebResponse:
    status: int
    content_type: str
    body: bytes
    headers: Mapping[str, str] = dataclasses.field(default_factory=dict)


class ProductWebController:
    def __init__(
        self,
        data_root: Path | None = None,
        template_root: Path = TEMPLATE_ROOT,
    ) -> None:
        root = Path(data_root) if data_root else PROJECT_ROOT / "data" / "local_app"
        self.facade = ProductFacade(ProductPaths(
            root=root,
            database=root / "product.sqlite3",
            incoming=root / "incoming",
            exports=root / "exports",
        ))
        self.template_root = template_root

    def handles(self, path: str) -> bool:
        return (
            path == "/"
            or path.startswith("/classes")
            or path.startswith("/sessions")
            or path.startswith("/mobile-capture")
        )

    def get(self, path: str) -> WebResponse | None:
        if path == "/mobile-capture/health.json":
            return self._json({
                "ok": True,
                "service": "objective-grading-mobile-capture",
                "transport": "adb-reverse-compatible",
                "real_recognition_enabled": False,
            })
        match = re.fullmatch(r"/sessions/([^/]+)/capture/status\.json", path)
        if match:
            try:
                return self._json(self.facade.mobile_capture_status(match.group(1)))
            except MobileCaptureServiceError as exc:
                return self._json_error(str(exc), exc.status, exc.code)
        if path == "/":
            return self._page("home.html", title="客观题批改本地工作台")
        if path == "/classes":
            return self._page(
                "classes.html",
                title="班级管理",
                items=self._class_items(),
            )
        if path == "/classes/new":
            return self._page("class_new.html", title="添加班级")
        match = re.fullmatch(r"/classes/([^/]+)", path)
        if match:
            return self._class_detail(match.group(1))
        match = re.fullmatch(r"/classes/([^/]+)/roster/import", path)
        if match:
            return self._page(
                "roster_import.html",
                title="导入班级名单",
                class_id=html.escape(match.group(1)),
            )
        if path == "/sessions":
            return self._page(
                "sessions.html",
                title="考试会话",
                items=self._session_items(),
            )
        if path == "/sessions/new":
            return self._page(
                "session_new.html",
                title="新建批改",
                class_options=self._class_options(),
            )
        match = re.fullmatch(r"/sessions/([^/]+)", path)
        if match:
            return self._session_detail(match.group(1))
        match = re.fullmatch(r"/sessions/([^/]+)/capture", path)
        if match:
            return self._capture_page(match.group(1))
        match = re.fullmatch(r"/sessions/([^/]+)/review", path)
        if match:
            return self._review_page(match.group(1))
        match = re.fullmatch(r"/sessions/([^/]+)/finalize", path)
        if match:
            return self._finalize_page(match.group(1))
        match = re.fullmatch(r"/sessions/([^/]+)/exports/final_scores\.csv", path)
        if match:
            return self._final_csv(match.group(1))
        return None

    def post(
        self,
        path: str,
        fields: Mapping[str, str],
        files: Mapping[str, UploadedFile],
    ) -> WebResponse | None:
        mobile_match = re.fullmatch(r"/sessions/([^/]+)/capture/mobile-web", path)
        if mobile_match:
            upload = files.get("image")
            if upload is None:
                return self._json_error("请选择图片。", 400, "IMAGE_REQUIRED")
            try:
                outcome = self.facade.capture_mobile_web(
                    mobile_match.group(1),
                    upload.filename,
                    upload.content,
                    upload.content_type,
                    dict(fields),
                )
            except MobileCaptureError as exc:
                return self._json_error(str(exc), exc.status, exc.code)
            except Exception:
                return self._json_error(
                    "图片登记失败，请保留手机中的待上传照片并重试。",
                    500,
                    "CAPTURE_REGISTRATION_FAILED",
                )
            return self._json({
                "ok": True,
                "capture_job_id": outcome.capture_job_id,
                "duplicate": outcome.duplicate,
                "state": outcome.state,
                "warning": outcome.warning,
                "server_received_at": outcome.server_received_at,
            }, 200 if outcome.duplicate else 201)
        try:
            if path == "/classes":
                classroom = self.facade.create_class(
                    fields.get("class_name", ""),
                    fields.get("grade_name", ""),
                    fields.get("school_year", ""),
                )
                return self._redirect(f"/classes/{classroom.class_id}")
            match = re.fullmatch(r"/classes/([^/]+)/roster/(?:import|confirm-mapping)", path)
            if match:
                upload = files.get("roster")
                if upload is None:
                    raise ValueError("请选择名单文件")
                result = self.facade.import_roster(
                    match.group(1),
                    upload.filename,
                    upload.content,
                    fields.get("student_no_column", ""),
                    fields.get("name_column", ""),
                    fields.get("class_column", ""),
                )
                if result.state is RosterImportState.COLUMN_MAPPING_REQUIRED:
                    return self._page(
                        "roster_mapping.html",
                        status=409,
                        title="请选择名单列",
                        class_id=html.escape(match.group(1)),
                        headers=self._header_options(result.headers),
                    )
                if result.state is RosterImportState.BLOCKED:
                    return self._error("；".join(issue.message for issue in result.blocking), 409)
                return self._redirect(f"/classes/{match.group(1)}")
            if path == "/sessions":
                session = self.facade.create_session(
                    fields.get("exam_name", ""),
                    fields.get("class_id", ""),
                )
                return self._redirect(f"/sessions/{session.session_id}")
            match = re.fullmatch(r"/sessions/([^/]+)/assets", path)
            if match:
                upload = files.get("asset")
                if upload is None:
                    raise ValueError("请选择材料文件")
                self.facade.add_asset(
                    match.group(1),
                    fields.get("asset_type", "OTHER"),
                    upload.filename,
                    upload.content,
                )
                return self._redirect(f"/sessions/{match.group(1)}")
            match = re.fullmatch(r"/sessions/([^/]+)/capture/(upload|browser-camera)", path)
            if match:
                upload = files.get("image")
                if upload is None:
                    raise ValueError("请选择图片")
                self.facade.capture_upload(
                    match.group(1),
                    upload.filename,
                    upload.content,
                    browser_camera=match.group(2) == "browser-camera",
                )
                return self._redirect(f"/sessions/{match.group(1)}/review")
            match = re.fullmatch(r"/sessions/([^/]+)/capture/watch-folder", path)
            if match:
                self.facade.scan_folder(match.group(1), fields.get("folder", ""))
                return self._redirect(f"/sessions/{match.group(1)}/review")
            match = re.fullmatch(r"/sessions/([^/]+)/review/([^/]+)/resolve", path)
            if match:
                self.facade.resolve_issue(match.group(2), dict(fields))
                return self._redirect(f"/sessions/{match.group(1)}/review")
            match = re.fullmatch(r"/sessions/([^/]+)/finalize", path)
            if match:
                decision, result = self.facade.finalize(match.group(1))
                if result is None:
                    return self._error("发布仍被阻断：" + "；".join(decision.blockers), 409)
                return self._redirect(
                    f"/sessions/{match.group(1)}/exports/final_scores.csv"
                )
        except (ValueError, RuntimeError) as exc:
            return self._error(str(exc), 409)
        return None

    def _class_detail(self, class_id: str) -> WebResponse:
        classroom = self.facade.classes.get_class(class_id)
        if classroom is None:
            return self._error("班级不存在", 404)
        rows = "".join(
            f"<tr><td>{html.escape(item.student_no)}</td><td>{html.escape(item.name)}</td></tr>"
            for item in self.facade.rosters.list_students(class_id)
        ) or '<tr><td colspan="2">尚未导入名单</td></tr>'
        return self._page(
            "class_detail.html",
            title=html.escape(classroom.class_name),
            class_id=html.escape(class_id),
            student_rows=rows,
        )

    def _session_detail(self, session_id: str) -> WebResponse:
        session = self.facade.sessions.get_session(session_id)
        if session is None:
            return self._error("考试会话不存在", 404)
        assets = "".join(
            f"<li>{html.escape(item.asset_type.value)}：{html.escape(item.original_filename)}（{html.escape(item.status)}）</li>"
            for item in self.facade.assets.list_assets(session_id)
        ) or "<li>尚未上传材料</li>"
        return self._page(
            "session_detail.html",
            title=html.escape(session.exam_name),
            session_id=html.escape(session_id),
            state=html.escape(session.state.value),
            assets=assets,
        )

    def _capture_page(self, session_id: str) -> WebResponse:
        jobs = "".join(
            f"<li>{html.escape(job.capture_job_id[:8])}：{html.escape(job.state.value)}</li>"
            for job in self.facade.queue.list_jobs(session_id)
        ) or "<li>队列为空</li>"
        return self._page(
            "capture.html",
            title="采集图片",
            session_id=html.escape(session_id),
            jobs=jobs,
        )

    def _review_page(self, session_id: str) -> WebResponse:
        issues = self.facade.review.list_issues(session_id, include_closed=True)
        cards = "".join(self._issue_card(session_id, issue) for issue in issues)
        return self._page(
            "review.html",
            title="复核中心",
            session_id=html.escape(session_id),
            issues=cards or "<p>没有未处理问题。</p>",
        )

    def _finalize_page(self, session_id: str) -> WebResponse:
        decision = self.facade.final_scores.gate.evaluate(session_id)
        blockers = "".join(f"<li>{html.escape(item)}</li>" for item in decision.blockers)
        return self._page(
            "finalize.html",
            title="最终发布",
            session_id=html.escape(session_id),
            gate=html.escape(decision.state.value),
            blockers=blockers or "<li>确认发布后即可生成最终成绩。</li>",
        )

    def _final_csv(self, session_id: str) -> WebResponse:
        path = self.facade.paths.exports / session_id / "final_scores.csv"
        if not path.is_file():
            return self._error("最终成绩尚未生成", 404)
        return WebResponse(
            200,
            "text/csv; charset=utf-8",
            path.read_bytes(),
            {"Content-Disposition": 'attachment; filename="final_scores.csv"'},
        )

    def _issue_card(self, session_id, issue) -> str:
        if issue.state not in {"OPEN", "IN_PROGRESS", "BLOCKED"}:
            return (
                f'<article><h3>{html.escape(issue.teacher_message)}</h3>'
                f'<p>处理状态：{html.escape(issue.state)}</p></article>'
            )
        identity = issue.issue_type.startswith("IDENTITY_")
        maximum = issue.question_max_score
        score_control = (
            f'<p>本题满分：{maximum:g} 分</p>'
            f'<label>手动得分：<input name="manual_score" type="number" '
            f'min="0" max="{maximum:g}" step="any"></label>'
            if maximum is not None else
            '<p>本题满分不可用，不能手动给分。</p>'
        )
        controls = (
            '<input name="student_no" placeholder="学号">'
            '<input name="name" placeholder="姓名">'
            '<label><input type="checkbox" name="confirm_name" value="yes">确认姓名匹配</label>'
            '<input name="reason" placeholder="临时学生原因（如适用）">'
            if identity else
            '<select name="action"><option value="MANUAL_SCORE">手动给分</option>'
            '<option value="MARK_WRONG">标记错误</option><option value="MARK_BLANK">标记空白</option>'
            '<option value="WAIVE">放弃该题</option><option value="EXCLUDE">排除试卷</option></select>'
            f'{score_control}'
            '<input name="reason" required placeholder="处理原因">'
        )
        primary = (
            f'<article><h3>{html.escape(issue.teacher_message)}</h3>'
            f'<form method="post" action="/sessions/{html.escape(session_id)}/review/{html.escape(issue.issue_id)}/resolve">'
            f'<input type="hidden" name="issue_type" value="{html.escape(issue.issue_type)}">'
            f'{controls}<button>保存处理</button></form></article>'
        )
        if not identity:
            return primary
        exclusion = (
            f'<form method="post" action="/sessions/{html.escape(session_id)}/review/{html.escape(issue.issue_id)}/resolve">'
            f'<input type="hidden" name="issue_type" value="{html.escape(issue.issue_type)}">'
            '<input type="hidden" name="exclude_capture" value="yes">'
            '<input name="reason" required placeholder="排除原因，例如重复拍摄">'
            '<button>排除该答卷</button></form>'
        )
        return primary.replace("</article>", exclusion + "</article>")

    def _class_items(self) -> str:
        return "".join(
            f'<li><a href="/classes/{item.class_id}">{html.escape(item.class_name)}</a></li>'
            for item in self.facade.classes.list_classes()
        ) or "<li>还没有班级</li>"

    def _session_items(self) -> str:
        return "".join(
            f'<li><a href="/sessions/{item.session_id}">{html.escape(item.exam_name)}</a> · {html.escape(item.state.value)}</li>'
            for item in self.facade.sessions.list_sessions()
        ) or "<li>还没有考试会话</li>"

    def _class_options(self) -> str:
        return "".join(
            f'<option value="{item.class_id}">{html.escape(item.class_name)}</option>'
            for item in self.facade.classes.list_classes()
        )

    @staticmethod
    def _header_options(headers) -> str:
        return "".join(
            f'<option value="{html.escape(header)}">{html.escape(header)}</option>'
            for header in headers
        )

    def _page(self, template_name: str, status: int = 200, **values) -> WebResponse:
        template = (self.template_root / template_name).read_text(encoding="utf-8")
        for key, value in values.items():
            template = template.replace("{{" + key + "}}", str(value))
        return WebResponse(status, "text/html; charset=utf-8", template.encode("utf-8"))

    def _error(self, message: str, status: int) -> WebResponse:
        return self._page(
            "error.html",
            status=status,
            title="操作未完成",
            message=html.escape(message),
        )

    @staticmethod
    def _json(payload: dict[str, object], status: int = 200) -> WebResponse:
        return WebResponse(
            status,
            "application/json; charset=utf-8",
            json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            {"Cache-Control": "no-store"},
        )

    def _json_error(self, message: str, status: int, code: str) -> WebResponse:
        return self._json(
            {"ok": False, "message": message, "error_code": code},
            status,
        )

    @staticmethod
    def _redirect(location: str) -> WebResponse:
        return WebResponse(303, "text/plain; charset=utf-8", b"", {"Location": location})
