"""Parseo de reportes .xlsx exportados manualmente desde new.omixom.com
(estación "APRHi - Lab. Hidráulica-UNC", Camino B -- ver README.md).

⚠️ COLUMN_MAP es un mejor esfuerzo, no está confirmado contra un reporte real
todavía (pendiente la muestra que se ofreció compartir -- ver plan de sesión).
Ajustar acá en cuanto se tenga un .xlsx real: es el único lugar del módulo que
conoce los nombres de columna crudos del reporte.
"""

import os
import shutil
import unicodedata
from datetime import datetime
from pathlib import Path

import openpyxl

from .models import OmixomReading


class ReportParseError(Exception):
    """El archivo no se pudo leer o no tiene ninguna columna reconocible."""


# Nombres de columna esperables en español, tal como suelen exportar estas
# plataformas -- TODO(fede): confirmar/corregir con un reporte real de la
# estación Lab. Hidráulica-UNC. Las claves están normalizadas (sin tildes,
# minúsculas) -- ver `_normalize_header`.
COLUMN_MAP: dict[str, str] = {
    "fecha": "measured_at",
    "fecha y hora": "measured_at",
    "temperatura": "temperature_c",
    "temperatura (c)": "temperature_c",
    "humedad": "humidity_pct",
    "humedad relativa": "humidity_pct",
    "presion": "pressure_hpa",
    "presion atmosferica": "pressure_hpa",
    "lluvia": "precipitation_mm",
    "precipitacion": "precipitation_mm",
    "viento velocidad": "wind_speed_kmh",
    "velocidad viento": "wind_speed_kmh",
    "viento direccion": "wind_direction_deg",
    "direccion viento": "wind_direction_deg",
}


def _normalize_header(raw: str) -> str:
    text = unicodedata.normalize("NFKD", str(raw)).encode("ascii", "ignore").decode("ascii")
    return text.strip().lower()


def _to_float(value: object) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_int(value: object) -> int | None:
    parsed = _to_float(value)
    return None if parsed is None else int(parsed)


def _parse_timestamp(value: object) -> datetime | None:
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        for fmt in ("%d/%m/%Y %H:%M", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S"):
            try:
                return datetime.strptime(value.strip(), fmt)
            except ValueError:
                continue
    return None


def parse_report(path: Path) -> list[OmixomReading]:
    try:
        workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    except Exception as error:  # openpyxl no documenta un tipo de excepción único
        raise ReportParseError(f"No se pudo abrir {path.name}: {error}") from error

    sheet = workbook.active
    rows = sheet.iter_rows(values_only=True)
    try:
        header_row = next(rows)
    except StopIteration:
        raise ReportParseError(f"{path.name} está vacío.")

    column_index_to_field = {}
    for index, header in enumerate(header_row):
        if header is None:
            continue
        field = COLUMN_MAP.get(_normalize_header(header))
        if field:
            column_index_to_field[index] = field

    if "measured_at" not in column_index_to_field.values():
        raise ReportParseError(
            f"{path.name}: no se encontró una columna de fecha reconocida "
            f"(headers vistos: {list(header_row)}). Revisar COLUMN_MAP."
        )

    readings: list[OmixomReading] = []
    for row in rows:
        values: dict[str, object] = {}
        for index, field in column_index_to_field.items():
            if index < len(row):
                values[field] = row[index]

        measured_at = _parse_timestamp(values.get("measured_at"))
        if measured_at is None:
            continue  # fila sin timestamp parseable -- se salta, no se aborta el archivo

        readings.append(
            OmixomReading(
                measured_at=measured_at,
                temperature_c=_to_float(values.get("temperature_c")),
                humidity_pct=_to_float(values.get("humidity_pct")),
                pressure_hpa=_to_float(values.get("pressure_hpa")),
                precipitation_mm=_to_float(values.get("precipitation_mm")),
                wind_speed_kmh=_to_float(values.get("wind_speed_kmh")),
                wind_direction_deg=_to_int(values.get("wind_direction_deg")),
            )
        )

    workbook.close()
    return readings


def find_pending_reports(watch_dir: str) -> list[Path]:
    """Archivos .xlsx directo en watch_dir -- no baja a processed/ ni failed/."""
    base = Path(watch_dir)
    if not base.is_dir():
        return []
    return sorted(p for p in base.glob("*.xlsx") if p.is_file())


def move_report(path: Path, destination_dir: str) -> None:
    os.makedirs(destination_dir, exist_ok=True)
    shutil.move(str(path), os.path.join(destination_dir, path.name))
