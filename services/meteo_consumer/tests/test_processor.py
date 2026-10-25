import json

from src.processor import MessageProcessor


class FakeDB:
    def __init__(self, error: Exception | None = None) -> None:
        self.error = error
        self.calls: list[dict] = []

    def insert(self, row: dict) -> None:
        if self.error is not None:
            raise self.error

        self.calls.append(row)


def valid_payload() -> dict:
    return {
        "node_id": "lit-cordoba-01",
        "timestamp": "2026-10-25T07:00:00Z",
        "source": "real",
        "producer": "bme280",
        "schema_version": "1.0",
        "metrics": {
            "temperature_c": 22.8,
            "humidity_pct": 55.4,
            "pressure_hpa": 972.1,
            "sensor_uid": "bme280-01",
        },
    }


def test_valid_message_is_persisted_and_acked() -> None:
    db = FakeDB()
    processor = MessageProcessor(db)

    should_ack = processor.process(json.dumps(valid_payload()))

    assert should_ack is True
    assert len(db.calls) == 1
    assert db.calls[0]["producer"] == "bme280"


def test_invalid_json_is_acked_without_persisting() -> None:
    db = FakeDB()
    processor = MessageProcessor(db)

    should_ack = processor.process(b"{esto no es json")

    assert should_ack is True
    assert db.calls == []


def test_invalid_schema_is_acked_without_persisting() -> None:
    db = FakeDB()
    processor = MessageProcessor(db)

    payload = valid_payload()
    payload["source"] = "api_omixom"

    should_ack = processor.process(json.dumps(payload))

    assert should_ack is True
    assert db.calls == []


def test_database_error_withholds_ack() -> None:
    db = FakeDB(ConnectionError("meteo_data unavailable"))
    processor = MessageProcessor(db)

    should_ack = processor.process(json.dumps(valid_payload()))

    assert should_ack is False
    assert db.calls == []
