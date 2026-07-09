from __future__ import annotations

import unittest

from app.answer_extraction.parser_errors import DocumentParseError, UnsupportedDocumentError, CorruptDocumentError


class DocxParserFailurePolicyV3Tests(unittest.TestCase):
    def test_document_parse_error_is_value_error(self):
        self.assertTrue(issubclass(DocumentParseError, ValueError))

    def test_unsupported_document_error(self):
        err = UnsupportedDocumentError("unsupported format")
        self.assertIsInstance(err, DocumentParseError)

    def test_corrupt_document_error(self):
        err = CorruptDocumentError("file is corrupt")
        self.assertIsInstance(err, DocumentParseError)

    def test_error_message_preserved(self):
        err = DocumentParseError("test message")
        self.assertEqual(str(err), "test message")

    def test_can_catch_as_value_error(self):
        try:
            raise CorruptDocumentError("bad file")
        except ValueError:
            pass
        else:
            self.fail("Should have been caught as ValueError")

    def test_can_catch_specifically(self):
        try:
            raise UnsupportedDocumentError("bad type")
        except UnsupportedDocumentError:
            pass
        else:
            self.fail("Should have been caught as UnsupportedDocumentError")

    def test_hierarchy_order(self):
        self.assertTrue(issubclass(CorruptDocumentError, DocumentParseError))
        self.assertTrue(issubclass(UnsupportedDocumentError, DocumentParseError))
        self.assertTrue(issubclass(DocumentParseError, ValueError))


if __name__ == "__main__":
    unittest.main()
