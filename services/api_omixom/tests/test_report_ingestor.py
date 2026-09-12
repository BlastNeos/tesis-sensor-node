from datetime import datetime
from pathlib import Path

import openpyxl
import pytest

from src.report_ingestor import (
    ReportParseError,
    find_pending_reports,
    move_report,
    parse_report,
)


def _write_report(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(headers)
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def test_parses_known_columns_and_skips_rows_without_timestamp(tmp_path: Path) -> None:
    report = tmp_path / "reporte.xlsx"
    _write_report(
        report,
        headers=["Fecha", "Temperatura", "Humedad", "Presion", "Lluvia", "Viento Velocidad", "Viento Direccion"],
        rows=[
            ["20/08/2026 12:00", 18.5, 62, 1013.2, 0.0, 11.0, 270],
            [None, 99, 99, 99, 99, 99, 99],  # sin fecha -- se descarta
            ["20/08/2026 12:10", 18.7, 61, 1013.0, 0.0, 12.5, 275],
        ],
    )

    readings = parse_report(report)

    assert len(readings) == 2
    assert readings[0].measured_at == datetime(2026, 8, 20, 12, 0)
    assert readings[0].temperature_c == 18.5
    assert readings[0].wind_direction_deg == 270


def test_unrecognized_columns_raise_clear_error(tmp_path: Path) -> None:
    report = tmp_path / "reporte_raro.xlsx"
    _write_report(report, headers=["ColumnaX", "ColumnaY"], rows=[[1, 2]])

    with pytest.raises(ReportParseError, match="no se encontró una columna de fecha"):
        parse_report(report)


def test_empty_file_raises_clear_error(tmp_path: Path) -> None:
    report = tmp_path / "vacio.xlsx"
    workbook = openpyxl.Workbook()
    workbook.save(report)

    with pytest.raises(ReportParseError, match="vacío"):
        parse_report(report)


def test_find_pending_reports_only_lists_xlsx_at_top_level(tmp_path: Path) -> None:
    (tmp_path / "a.xlsx").touch()
    (tmp_path / "b.xlsx").touch()
    (tmp_path / "no_es_reporte.txt").touch()
    processed = tmp_path / "processed"
    processed.mkdir()
    (processed / "c.xlsx").touch()  # ya procesado, no debe listarse

    found = find_pending_reports(str(tmp_path))

    assert {p.name for p in found} == {"a.xlsx", "b.xlsx"}


def test_find_pending_reports_missing_dir_returns_empty() -> None:
    assert find_pending_reports("/no/existe/esta/carpeta") == []


def test_move_report_creates_destination_and_moves_file(tmp_path: Path) -> None:
    report = tmp_path / "reporte.xlsx"
    report.write_text("contenido")
    destination = tmp_path / "processed"

    move_report(report, str(destination))

    assert not report.exists()
    assert (destination / "reporte.xlsx").exists()
