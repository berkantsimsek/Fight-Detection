import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main.violence_detection.report_generator import ReportGenerator


def init_db(path):
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE events (
                id INTEGER PRIMARY KEY,
                timestamp TEXT,
                label TEXT,
                confidence REAL,
                screenshot_path TEXT,
                fps REAL,
                latency REAL
            )
            """
        )


def test_generate_returns_no_events_result(tmp_path):
    db_path = tmp_path / "events.db"
    report_dir = tmp_path / "reports"
    init_db(db_path)

    generator = ReportGenerator(str(db_path), str(report_dir))

    result = generator.generate()

    assert result["success"] is False
    assert result["reason"] == "no_events"
    assert result["event_count"] == 0
    assert result["path"] is None
    assert result["last_report_path"] is None
    assert "kayıtlı şiddet olayı yok" in result["message"]


def test_generate_succeeds_when_screenshot_is_missing(tmp_path, capsys):
    db_path = tmp_path / "events.db"
    report_dir = tmp_path / "reports"
    missing_screenshot = tmp_path / "missing.png"
    init_db(db_path)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO events (
                timestamp, label, confidence, screenshot_path, fps, latency
            ) VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                "2026-06-02 20:00:00",
                "Violence",
                0.91,
                str(missing_screenshot),
                24.0,
                0.043,
            ),
        )

    generator = ReportGenerator(str(db_path), str(report_dir))

    result = generator.generate()

    assert result["success"] is True
    assert result["reason"] == "created"
    assert result["event_count"] == 1
    assert os.path.exists(result["path"])
    assert result["last_report_path"] == result["path"]
    captured = capsys.readouterr()
    assert "Ekran görüntüsü eksik" in captured.out
