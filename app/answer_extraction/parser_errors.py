from __future__ import annotations


class DocumentParseError(ValueError):
    pass


class UnsupportedDocumentError(DocumentParseError):
    pass


class CorruptDocumentError(DocumentParseError):
    pass
