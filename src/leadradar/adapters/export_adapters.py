"""Export adapters — convert lead data to downloadable file formats.

These are pure conversion functions with no database or HTTP dependencies.
They accept generic dict rows so that the service layer controls field extraction
and the adapters only concern themselves with format rendering.
"""

from __future__ import annotations

import csv
import io
from typing import Any, Protocol

from openpyxl import Workbook


_EXPORT_COLUMNS = [
    "organization_name",
    "lead_status",
    "grade",
    "total_score",
    "customer_type",
    "recommended_package",
    "budget_bucket",
    "signal_type",
    "budget_amount",
    "source_url",
    "evidence_text",
]


class ExportAdapter(Protocol):
    """Protocol for export format adapters."""

    def render(self, rows: list[dict[str, Any]]) -> str | bytes: ...
    def content_type(self) -> str: ...
    def filename(self) -> str: ...


class CsvExportAdapter:
    """Render leads as UTF-8 CSV with BOM for Excel compatibility."""

    def render(self, rows: list[dict[str, Any]]) -> str:
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=_EXPORT_COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in _EXPORT_COLUMNS})
        return buf.getvalue()

    def content_type(self) -> str:
        return "text/csv; charset=utf-8-sig"

    def filename(self) -> str:
        return "leads.csv"


class XlsxExportAdapter:
    """Render leads as Excel workbook."""

    def render(self, rows: list[dict[str, Any]]) -> bytes:
        wb = Workbook()
        ws = wb.active
        ws.title = "线索列表"
        ws.append(_EXPORT_COLUMNS)
        for row in rows:
            ws.append([row.get(c, "") for c in _EXPORT_COLUMNS])
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    def content_type(self) -> str:
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    def filename(self) -> str:
        return "leads.xlsx"
