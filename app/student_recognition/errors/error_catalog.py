"""Error catalog: metadata for every :class:`ErrorCode`.

Each error code has exactly one :class:`CatalogEntry` describing its category,
severity, default (Chinese) message, and behavioral flags used by the grading
gates:

* ``blocking``          – whether the code blocks progression to official grading.
* ``requires_review``   – whether the code must be resolved in the Review Queue.
* ``can_teacher_override`` – whether a teacher may override the issue.

This catalog is consulted by :mod:`error_policy` and :mod:`error_message`.
It is the authoritative source of default messages; never embed free-form
reason strings in business code (constitution §1 B6).
"""

from dataclasses import dataclass
from typing import Dict

from app.student_recognition.errors.error_codes import (
    CATEGORY_BUNDLE,
    CATEGORY_DRAFT_REVIEW,
    CATEGORY_GRADING_GATE,
    CATEGORY_IDENTITY,
    CATEGORY_IMAGE,
    CATEGORY_INTERNAL,
    CATEGORY_OMR,
    CATEGORY_PAGE,
    CATEGORY_ROI,
    CATEGORY_TEMPLATE,
    ErrorCode,
)


@dataclass(frozen=True)
class CatalogEntry:
    """Metadata describing a single error code."""

    code: ErrorCode
    category: str
    severity: str  # "blocking" | "review" | "warning"
    default_message: str
    blocking: bool
    requires_review: bool
    can_teacher_override: bool


def _e(
    code: ErrorCode,
    category: str,
    severity: str,
    default_message: str,
    blocking: bool,
    requires_review: bool,
    can_teacher_override: bool,
) -> CatalogEntry:
    return CatalogEntry(
        code=code,
        category=category,
        severity=severity,
        default_message=default_message,
        blocking=blocking,
        requires_review=requires_review,
        can_teacher_override=can_teacher_override,
    )


# fmt: off
_CATALOG_LIST: list[CatalogEntry] = [
    # ---- Image ----
    _e(ErrorCode.IMG_BLUR_TOO_HIGH, CATEGORY_IMAGE, "blocking", "图像模糊度过高，无法可靠识别。", True, True, True),
    _e(ErrorCode.IMG_TOO_DARK, CATEGORY_IMAGE, "blocking", "图像过暗，无法可靠识别。", True, True, True),
    _e(ErrorCode.IMG_TOO_BRIGHT, CATEGORY_IMAGE, "blocking", "图像过亮或过曝，无法可靠识别。", True, True, True),
    _e(ErrorCode.IMG_LOW_CONTRAST, CATEGORY_IMAGE, "blocking", "图像对比度过低，无法可靠识别。", True, True, True),
    _e(ErrorCode.IMG_SHADOW_TOO_STRONG, CATEGORY_IMAGE, "blocking", "图像阴影过重，影响识别。", True, True, True),
    _e(ErrorCode.IMG_TOO_SMALL, CATEGORY_IMAGE, "blocking", "图像分辨率过低，无法可靠识别。", True, True, True),
    _e(ErrorCode.IMG_UNSUPPORTED_FORMAT, CATEGORY_IMAGE, "blocking", "不支持的图像格式。", True, True, True),
    _e(ErrorCode.IMG_UPLOAD_CORRUPTED, CATEGORY_IMAGE, "blocking", "上传图像损坏，无法解码。", True, True, True),

    # ---- Page ----
    _e(ErrorCode.PAGE_NOT_FOUND, CATEGORY_PAGE, "blocking", "未检测到答题卡页面。", True, True, True),
    _e(ErrorCode.PAGE_QUAD_INVALID, CATEGORY_PAGE, "blocking", "页面四边形定位无效。", True, True, True),
    _e(ErrorCode.PAGE_COVERAGE_TOO_SMALL, CATEGORY_PAGE, "blocking", "页面覆盖面积过小，可能未对准。", True, True, True),
    _e(ErrorCode.PAGE_ASPECT_RATIO_INVALID, CATEGORY_PAGE, "blocking", "页面宽高比异常。", True, True, True),
    _e(ErrorCode.PAGE_PERSPECTIVE_TOO_EXTREME, CATEGORY_PAGE, "blocking", "页面透视畸变过大。", True, True, True),
    _e(ErrorCode.PAGE_NORMALIZATION_FAILED, CATEGORY_PAGE, "blocking", "页面透视归一化失败。", True, True, True),

    # ---- Template ----
    _e(ErrorCode.TEMPLATE_MISSING, CATEGORY_TEMPLATE, "blocking", "缺少对应模板，无法定位选项。", True, True, True),
    _e(ErrorCode.TEMPLATE_VERSION_MISSING, CATEGORY_TEMPLATE, "blocking", "模板版本缺失。", True, True, True),
    _e(ErrorCode.TEMPLATE_VERSION_MISMATCH, CATEGORY_TEMPLATE, "blocking", "模板版本与作业不匹配。", True, True, True),
    _e(ErrorCode.TEMPLATE_PAGE_MISSING, CATEGORY_TEMPLATE, "blocking", "模板缺少该页定义。", True, True, True),
    _e(ErrorCode.TEMPLATE_ROI_OUT_OF_BOUNDS, CATEGORY_TEMPLATE, "blocking", "模板 ROI 超出图像范围。", True, True, True),
    _e(ErrorCode.TEMPLATE_OPTION_CELL_MISSING, CATEGORY_TEMPLATE, "blocking", "模板缺少选项格定义。", True, True, True),
    _e(ErrorCode.TEMPLATE_IDENTITY_ROI_MISSING, CATEGORY_TEMPLATE, "blocking", "模板缺少身份区域定义。", True, True, True),
    _e(ErrorCode.TEMPLATE_CALIBRATION_ANCHOR_INVALID, CATEGORY_TEMPLATE, "blocking", "标定锚点无效（数量/坐标/模式不合法）。", True, True, True),
    _e(ErrorCode.TEMPLATE_COORDINATE_SYSTEM_INVALID, CATEGORY_TEMPLATE, "blocking", "坐标系统非法（必须为 normalized / top_left / ratio）。", True, True, True),
    _e(ErrorCode.TEMPLATE_ROI_INVALID, CATEGORY_TEMPLATE, "blocking", "ROI 非法（宽高须为正、坐标须为有限数）。", True, True, True),
    _e(ErrorCode.TEMPLATE_DUPLICATE_QUESTION_NO, CATEGORY_TEMPLATE, "blocking", "题号重复。", True, True, True),
    _e(ErrorCode.TEMPLATE_INVALID_OPTION_LABEL, CATEGORY_TEMPLATE, "blocking", "选项标签非法（须为字符串且属于选项集）。", True, True, True),
    _e(ErrorCode.TEMPLATE_SINGLE_CHOICE_MISSING_OPTIONS, CATEGORY_TEMPLATE, "blocking", "单选题缺少 A/B/C/D 选项。", True, True, True),
    _e(ErrorCode.TEMPLATE_MULTI_CHOICE_MISSING_OPTIONS, CATEGORY_TEMPLATE, "blocking", "多选题缺少选项定义。", True, True, True),
    _e(ErrorCode.TEMPLATE_QUESTION_BLOCK_EMPTY, CATEGORY_TEMPLATE, "blocking", "题目块为空，无可用选项。", True, True, True),
    _e(ErrorCode.TEMPLATE_ROI_OVERLAP_WARNING, CATEGORY_TEMPLATE, "warning", "ROI 重叠过量，请检查布局。", False, False, False),
    _e(ErrorCode.TEMPLATE_DUPLICATE_PAGE_ID, CATEGORY_TEMPLATE, "blocking", "模板页 ID 重复。", True, True, True),
    _e(ErrorCode.TEMPLATE_DUPLICATE_PAGE_NO, CATEGORY_TEMPLATE, "blocking", "模板页号重复。", True, True, True),
    _e(ErrorCode.TEMPLATE_VERSION_CONFLICT, CATEGORY_TEMPLATE, "blocking", "同版本模板已存在，禁止覆盖旧版本。", True, True, True),
    _e(ErrorCode.TEMPLATE_DRAFT_NOT_FINALIZED, CATEGORY_TEMPLATE, "blocking", "草稿未经验证，不能用于识别。", True, True, True),

    # ---- ROI ----
    _e(ErrorCode.ROI_OUT_OF_BOUNDS, CATEGORY_ROI, "blocking", "ROI 越界，拒绝裁剪。", True, True, True),
    _e(ErrorCode.ROI_EMPTY_CROP, CATEGORY_ROI, "blocking", "ROI 裁剪结果为空。", True, True, True),
    _e(ErrorCode.ROI_TOO_SMALL, CATEGORY_ROI, "review", "ROI 裁剪区域过小，需人工确认。", False, True, True),
    _e(ErrorCode.ROI_CROP_FAILED, CATEGORY_ROI, "blocking", "ROI 裁剪失败。", True, True, True),

    # ---- OMR ----
    _e(ErrorCode.OMR_WEAK_MARK, CATEGORY_OMR, "review", "检测到弱涂选项，需人工确认。", False, True, True),
    _e(ErrorCode.OMR_EMPTY_MARK, CATEGORY_OMR, "review", "未检测到明确涂写，可能为未作答。", False, True, True),
    _e(ErrorCode.OMR_MULTI_MARK_SINGLE_CHOICE, CATEGORY_OMR, "review",
       "单选题检测到多个明显涂写选项，需要人工确认。", False, True, True),
    _e(ErrorCode.OMR_AMBIGUOUS_MULTI_CHOICE, CATEGORY_OMR, "review", "多选题识别存在歧义，需人工确认。", False, True, True),
    _e(ErrorCode.OMR_BORDER_NOISE_HIGH, CATEGORY_OMR, "review", "选项边框噪声较高，可能影响识别。", False, True, True),
    _e(ErrorCode.OMR_ERASURE_DETECTED, CATEGORY_OMR, "review", "检测到擦除痕迹，需人工确认。", False, True, True),
    _e(ErrorCode.OMR_LOW_CONFIDENCE, CATEGORY_OMR, "review", "OMR 识别置信度过低，需人工确认。", False, True, True),
    _e(ErrorCode.OMR_OPTION_CELL_MISSING, CATEGORY_OMR, "blocking", "选项格缺失，无法读取该选项。", True, True, True),

    # ---- Identity ----
    _e(ErrorCode.IDENTITY_MISSING, CATEGORY_IDENTITY, "blocking", "身份缺失，无法确认学生。", True, True, True),
    _e(ErrorCode.IDENTITY_LOW_CONFIDENCE, CATEGORY_IDENTITY, "review", "身份识别置信度低，需人工确认。", False, True, True),
    _e(ErrorCode.IDENTITY_CONFLICT, CATEGORY_IDENTITY, "blocking",
       "识别到的学号与名单姓名不一致，需要人工处理。", True, True, True),
    _e(ErrorCode.IDENTITY_DUPLICATE, CATEGORY_IDENTITY, "blocking", "检测到重复身份，需人工处理。", True, True, True),
    _e(ErrorCode.IDENTITY_ROSTER_NOT_FOUND, CATEGORY_IDENTITY, "blocking", "学号在名单中未找到。", True, True, True),
    _e(ErrorCode.IDENTITY_NAME_ONLY, CATEGORY_IDENTITY, "review", "仅识别到姓名，缺少学号，需人工确认。", False, True, True),
    _e(ErrorCode.IDENTITY_STUDENT_ID_ONLY_UNMATCHED, CATEGORY_IDENTITY, "blocking",
       "学号与名单不匹配，无法确认身份。", True, True, True),

    # ---- Draft / Review ----
    _e(ErrorCode.DRAFT_HAS_BLOCKING_ERRORS, CATEGORY_DRAFT_REVIEW, "blocking", "识别草稿存在阻断性错误，不能确认。", True, False, False),
    _e(ErrorCode.DRAFT_HAS_UNRESOLVED_REVIEW, CATEGORY_DRAFT_REVIEW, "review", "识别草稿存在未解决复核项。", False, True, True),
    _e(ErrorCode.REVIEW_ITEM_UNRESOLVED, CATEGORY_DRAFT_REVIEW, "review", "存在未解决复核项，不能进入正式批改。", False, True, False),
    _e(ErrorCode.TEACHER_CONFIRMATION_REQUIRED, CATEGORY_DRAFT_REVIEW, "blocking", "需要教师确认后才能继续。", True, False, False),
    _e(ErrorCode.TEACHER_OVERRIDE_REQUIRES_NOTE, CATEGORY_DRAFT_REVIEW, "blocking", "教师覆盖必须填写备注说明。", True, False, False),

    # ---- Bundle ----
    _e(ErrorCode.BUNDLE_MISSING_PAGE, CATEGORY_BUNDLE, "blocking", "提交缺少某一页，无法聚合。", True, True, True),
    _e(ErrorCode.BUNDLE_DUPLICATE_PAGE, CATEGORY_BUNDLE, "blocking", "提交存在重复页。", True, True, True),
    _e(ErrorCode.BUNDLE_IDENTITY_CONFLICT, CATEGORY_BUNDLE, "blocking", "多页之间身份冲突。", True, True, True),
    _e(ErrorCode.BUNDLE_TEMPLATE_VERSION_MISMATCH, CATEGORY_BUNDLE, "blocking", "多页模板版本不一致。", True, True, True),
    _e(ErrorCode.BUNDLE_PAGE_ORDER_UNKNOWN, CATEGORY_BUNDLE, "review", "多页顺序未知，需人工确认。", False, True, True),

    # ---- Grading Gate ----
    _e(ErrorCode.GRADING_DRAFT_NOT_CONFIRMED, CATEGORY_GRADING_GATE, "blocking",
       "识别草稿尚未确认，不能进入正式批改。", True, False, False),
    _e(ErrorCode.GRADING_IDENTITY_NOT_CONFIRMED, CATEGORY_GRADING_GATE, "blocking", "身份未确认，不能进入正式批改。", True, False, False),
    _e(ErrorCode.GRADING_BLOCKING_ERRORS_EXIST, CATEGORY_GRADING_GATE, "blocking", "存在阻断性错误，不能进入正式批改。", True, False, False),
    _e(ErrorCode.GRADING_UNRESOLVED_REVIEW_ITEMS, CATEGORY_GRADING_GATE, "blocking",
       "存在未解决复核项，不能生成正式报告。", True, False, False),
    _e(ErrorCode.GRADING_EXAM_HAS_DUPLICATE_STUDENT, CATEGORY_GRADING_GATE, "blocking",
       "考试中存在重复学生，不能生成正式报告。", True, False, False),
    _e(ErrorCode.GRADING_EXAM_HAS_MISSING_STUDENTS, CATEGORY_GRADING_GATE, "blocking",
       "考试存在缺失学生，需教师确认是否继续。", True, True, True),
    _e(ErrorCode.GRADING_ANSWER_KEY_NOT_ACCEPTED, CATEGORY_GRADING_GATE, "blocking",
       "答案密钥未 accepted，不能进入正式批改。", True, False, False),

    # ---- Internal fallback ----
    _e(ErrorCode.INTERNAL_UNKNOWN_ERROR, CATEGORY_INTERNAL, "blocking", "发生未知内部错误，需要排查。", True, True, False),
]
# fmt: on

CATALOG: Dict[ErrorCode, CatalogEntry] = {entry.code: entry for entry in _CATALOG_LIST}


def get_entry(code: ErrorCode) -> CatalogEntry:
    """Return the catalog entry for ``code``.

    Unknown codes are mapped to :attr:`ErrorCode.INTERNAL_UNKNOWN_ERROR` so the
    caller always receives a usable entry (constitution §18, conservative default).
    """
    if code in CATALOG:
        return CATALOG[code]
    return CATALOG[ErrorCode.INTERNAL_UNKNOWN_ERROR]
