# Violence Detection UI Modernization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Modernize the existing Tkinter violence detection UI while preserving its workflow, and make report generation crash-safe.

**Architecture:** Keep the current `main/violence_detection` package. Harden `ReportGenerator` first so the dangerous workflow is safe, then update `DetectionGUI` into a responsive operator console with header, live view, action bar, metrics/status panel, and recent events summary.

**Tech Stack:** Python 3.12, Tkinter/ttk, OpenCV, Pillow, SQLite, ReportLab, existing detection pipeline.

---

## File Structure

- Modify: `main/violence_detection/report_generator.py`
  - Return structured report results.
  - Treat no-event and missing-screenshot states as controlled outcomes.
  - Keep PDF generation alive when individual screenshots are missing.

- Modify: `main/violence_detection/detection_gui.py`
  - Replace the current stacked layout with a modern responsive layout.
  - Add report button loading/disabled behavior.
  - Add recent events summary.
  - Preserve start, stop, test mode, expand, confidence, status, and live frame behavior.

- Modify: `main/violence_detection/main.py`
  - Pass DB path to GUI if needed for recent events, or rely on `AlarmManager`/`ReportGenerator` paths already passed through.

- Create: `tests/test_report_generator.py`
  - Test no-event behavior.
  - Test missing screenshots do not crash report generation.

- Create: `tests/test_alarm_manager.py`
  - Test screenshot/log path remains safe for valid dummy frames.

Note: This project currently does not appear to be a Git repository. Commit steps are included for workers in a Git checkout; if `git status` returns `fatal: not a git repository`, skip commit commands and continue with the next task.

---

### Task 1: Add Report Result Types And No-Event Safety

**Files:**
- Modify: `main/violence_detection/report_generator.py`
- Create: `tests/test_report_generator.py`

- [ ] **Step 1: Write failing tests for no-event report behavior**

Create `tests/test_report_generator.py` with:

```python
import os
import sqlite3

from main.violence_detection.report_generator import ReportGenerator


def init_db(path):
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                label TEXT,
                confidence REAL,
                screenshot_path TEXT,
                fps REAL,
                latency REAL
            )
            """
        )
        conn.commit()


def test_generate_returns_no_events_result(tmp_path):
    db_path = tmp_path / "events.db"
    report_dir = tmp_path / "pdfReports"
    init_db(db_path)

    generator = ReportGenerator(str(db_path), str(report_dir))
    result = generator.generate()

    assert result["success"] is False
    assert result["reason"] == "no_events"
    assert result["event_count"] == 0
    assert result["path"] is None
    assert "kayıtlı şiddet olayı yok" in result["message"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
python -m pytest tests/test_report_generator.py::test_generate_returns_no_events_result -v
```

Expected: FAIL because `generate()` currently raises `ValueError` instead of returning a structured result.

- [ ] **Step 3: Update `ReportGenerator.generate()` no-event branch**

In `main/violence_detection/report_generator.py`, replace:

```python
if not events:
    raise ValueError("Hiçbir şiddet olayı bulunmadı.")
```

with:

```python
if not events:
    self.last_report_path = None
    return {
        "success": False,
        "reason": "no_events",
        "message": "Rapor için kayıtlı şiddet olayı yok.",
        "path": None,
        "event_count": 0,
    }
```

At the end of successful PDF generation, after `doc.build(...)`, add:

```python
return {
    "success": True,
    "reason": "created",
    "message": f"Rapor oluşturuldu: {report_file}",
    "path": report_file,
    "event_count": event_count,
}
```

In the outer `except Exception as e:` block, replace `raise` with:

```python
return {
    "success": False,
    "reason": "error",
    "message": "Rapor oluşturulamadı. Ayrıntılar terminalde.",
    "path": None,
    "event_count": 0,
    "error": str(e),
}
```

- [ ] **Step 4: Run no-event test**

Run:

```bash
python -m pytest tests/test_report_generator.py::test_generate_returns_no_events_result -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add main/violence_detection/report_generator.py tests/test_report_generator.py
git commit -m "fix: make empty report generation safe"
```

If this is not a Git repository, skip this step.

---

### Task 2: Keep Reports Alive When Screenshots Are Missing

**Files:**
- Modify: `main/violence_detection/report_generator.py`
- Modify: `tests/test_report_generator.py`

- [ ] **Step 1: Add failing test for missing screenshot**

Append to `tests/test_report_generator.py`:

```python
def test_generate_succeeds_when_screenshot_is_missing(tmp_path):
    db_path = tmp_path / "events.db"
    report_dir = tmp_path / "pdfReports"
    missing_path = tmp_path / "missing.png"
    init_db(db_path)

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO events (timestamp, label, confidence, screenshot_path, fps, latency)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            ("2026-06-02 20:00:00", "Violence", 0.93, str(missing_path), 14.5, 0.04),
        )
        conn.commit()

    generator = ReportGenerator(str(db_path), str(report_dir))
    result = generator.generate()

    assert result["success"] is True
    assert result["event_count"] == 1
    assert result["path"] is not None
    assert os.path.exists(result["path"])
```

- [ ] **Step 2: Run test to verify current behavior**

Run:

```bash
python -m pytest tests/test_report_generator.py::test_generate_succeeds_when_screenshot_is_missing -v
```

Expected: PASS if current missing-image branch already avoids crashing; FAIL if another PDF path issue appears. If it passes, keep the test as regression coverage.

- [ ] **Step 3: Make missing screenshot text explicit**

In `main/violence_detection/report_generator.py`, inside the existing `else` branch for missing screenshots, use this paragraph text:

```python
elements.append(Paragraph(f"Görüntü bulunamadı: {screenshot_path}", styles["Normal"]))
print(f"Ekran görüntüsü eksik: {screenshot_path}")
```

- [ ] **Step 4: Run report generator tests**

Run:

```bash
python -m pytest tests/test_report_generator.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

Run:

```bash
git add main/violence_detection/report_generator.py tests/test_report_generator.py
git commit -m "test: cover missing screenshot report generation"
```

If this is not a Git repository, skip this step.

---

### Task 3: Add Crash-Safe GUI Report Workflow

**Files:**
- Modify: `main/violence_detection/detection_gui.py`

- [ ] **Step 1: Add report state fields**

In `DetectionGUI.__init__`, after existing state fields:

```python
self.report_running = False
self.recent_events = []
```

- [ ] **Step 2: Replace `generate_report()` with controlled button state**

Replace `DetectionGUI.generate_report` with:

```python
def generate_report(self):
    if self.report_running:
        return

    self.report_running = True
    self.report_button.config(state="disabled", text="Rapor Hazırlanıyor")
    self.status_label.config(text="Durum: Rapor hazırlanıyor")

    try:
        result = self.report_generator.generate()
        self._refresh_recent_events()

        if result.get("success"):
            messagebox.showinfo(
                "Rapor",
                f"{result.get('message')}\nOlay sayısı: {result.get('event_count', 0)}"
            )
        else:
            messagebox.showwarning("Rapor", result.get("message", "Rapor oluşturulamadı."))
    except Exception as e:
        print(f"Rapor oluşturma GUI hatası: {e}")
        messagebox.showerror("Hata", "Rapor oluşturulamadı. Ayrıntılar terminalde.")
    finally:
        self.report_running = False
        self.report_button.config(state="normal", text="Rapor Oluştur")
        self.status_label.config(text="Durum: Çalışıyor" if self.running else "Durum: Bekliyor")
```

- [ ] **Step 3: Add recent event refresh method**

Add this method to `DetectionGUI`:

```python
def _refresh_recent_events(self):
    try:
        import sqlite3

        db_path = self.report_generator.db_path
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT timestamp, confidence, screenshot_path
                FROM events
                WHERE label = 'Violence'
                ORDER BY id DESC
                LIMIT 5
                """
            )
            self.recent_events = cursor.fetchall()
    except Exception as e:
        print(f"Son olaylar okunamadı: {e}")
        self.recent_events = []

    self._render_recent_events()
```

- [ ] **Step 4: Add recent event render method**

Add this method to `DetectionGUI`:

```python
def _render_recent_events(self):
    if not hasattr(self, "recent_events_label"):
        return

    count = len(self.recent_events)
    if count == 0:
        text = "Kayıtlı şiddet olayı yok. Rapor oluşturulursa bilgi mesajı gösterilir."
    else:
        lines = [f"Son {count} olay:"]
        for timestamp, confidence, screenshot_path in self.recent_events:
            try:
                confidence_value = float(confidence)
            except (TypeError, ValueError):
                confidence_value = 0.0
            image_state = "görüntü var" if screenshot_path and os.path.exists(str(screenshot_path)) else "görüntü yok"
            lines.append(f"{timestamp} · {confidence_value:.2f} · {image_state}")
        text = "\n".join(lines)

    self.recent_events_label.config(text=text)
```

- [ ] **Step 5: Compile GUI**

Run:

```bash
python -m compileall main/violence_detection
```

Expected: command exits with code 0.

- [ ] **Step 6: Commit**

Run:

```bash
git add main/violence_detection/detection_gui.py
git commit -m "fix: make report button crash safe"
```

If this is not a Git repository, skip this step.

---

### Task 4: Replace UI Layout With Modern Responsive Structure

**Files:**
- Modify: `main/violence_detection/detection_gui.py`

- [ ] **Step 1: Add layout constants and breakpoint**

In `DetectionGUI.__init__`, after color setup, set:

```python
self.window_width = 980
self.window_height = 720
self.responsive_breakpoint = 860
```

Update the initial geometry block to use:

```python
width, height = self.window_width, self.window_height
```

- [ ] **Step 2: Update theme colors**

Replace the current palette assignment with:

```python
self.bg_color = "#F4F6F8"
self.panel_color = "#FFFFFF"
self.surface_color = "#F8FAFC"
self.text_color = "#17212B"
self.muted_text_color = "#64748B"
self.line_color = "#D8DEE6"
self.accent_color = "#2563EB"
self.alert_color = "#DC2626"
self.safe_color = "#16A34A"
self.dark_button_color = "#111827"
self.root.configure(bg=self.bg_color)
```

Keep `self.secondary_bg` for compatibility by setting:

```python
self.secondary_bg = self.panel_color
```

- [ ] **Step 3: Reconfigure ttk styles**

Replace style configuration with:

```python
style.configure("TButton", font=("Roboto", 11, "bold"), padding=10, borderwidth=0)
style.configure("Primary.TButton", font=("Roboto", 11, "bold"), padding=10)
style.configure("Secondary.TButton", font=("Roboto", 11), padding=10)
style.configure("TLabel", font=("Roboto", 11), foreground=self.text_color, background=self.bg_color)
style.configure("Title.TLabel", font=("Roboto", 20, "bold"), foreground=self.text_color, background=self.bg_color)
style.configure("Muted.TLabel", font=("Roboto", 10), foreground=self.muted_text_color, background=self.bg_color)
style.configure("Main.TFrame", background=self.bg_color)
style.configure("Panel.TFrame", background=self.panel_color, relief="flat")
style.configure("Metric.TFrame", background=self.surface_color, relief="flat")
```

- [ ] **Step 4: Replace top-level packed content with structured frames**

After the existing scrollable setup, build frames in this order:

```python
self.header_frame = ttk.Frame(self.main_frame, style="Main.TFrame")
self.header_frame.pack(fill="x", padx=18, pady=(18, 10))

self.content_frame = ttk.Frame(self.main_frame, style="Main.TFrame")
self.content_frame.pack(fill="both", expand=True, padx=18, pady=8)

self.video_column = ttk.Frame(self.content_frame, style="Main.TFrame")
self.info_column = ttk.Frame(self.content_frame, style="Main.TFrame")

self.action_frame = ttk.Frame(self.video_column, style="Panel.TFrame", padding=10)
self.metrics_frame = ttk.Frame(self.info_column, style="Panel.TFrame", padding=12)
self.status_frame = ttk.Frame(self.info_column, style="Panel.TFrame", padding=12)
self.recent_frame = ttk.Frame(self.info_column, style="Panel.TFrame", padding=12)
```

- [ ] **Step 5: Add header widgets**

Use:

```python
self.title_label = ttk.Label(self.header_frame, text="Şiddet Algılama Sistemi", style="Title.TLabel")
self.title_label.pack(anchor="w")
self.subtitle_label = ttk.Label(
    self.header_frame,
    text="Canlı kamera izleme · Webcam/RTSP · Model hazır",
    style="Muted.TLabel"
)
self.subtitle_label.pack(anchor="w", pady=(4, 0))
```

- [ ] **Step 6: Keep video canvas but modernize its container**

Use:

```python
self.canvas_frame = tk.Frame(
    self.video_column,
    bg=self.panel_color,
    bd=1,
    highlightbackground=self.line_color,
    highlightthickness=1
)
self.canvas_frame.pack(fill="both", expand=True)
self.canvas = tk.Canvas(
    self.canvas_frame,
    width=canvas_width,
    height=canvas_height,
    bg="#1F2937",
    highlightthickness=0
)
self.canvas.pack(fill="both", expand=True, padx=8, pady=8)
```

- [ ] **Step 7: Build action buttons in action bar**

Pack `self.action_frame` below the video:

```python
self.action_frame.pack(fill="x", pady=(10, 0))
```

Create the buttons with the existing icons and commands:

```python
self.start_button = ttk.Button(self.action_frame, text="Başlat", image=self.start_icon, compound="left", command=self.start, style="Primary.TButton")
self.stop_button = ttk.Button(self.action_frame, text="Durdur", image=self.stop_icon, compound="left", command=self.stop, state="disabled", style="Primary.TButton")
self.test_button = ttk.Button(self.action_frame, text="Test Modu", image=self.test_icon, compound="left", command=self.toggle_test_mode, style="Secondary.TButton")
self.expand_button = ttk.Button(self.action_frame, text="Büyüt", image=self.expand_icon, compound="left", command=self.toggle_expand, style="Secondary.TButton")
self.report_button = ttk.Button(self.action_frame, text="Rapor Oluştur", image=self.report_icon, compound="left", command=self.generate_report, style="Secondary.TButton")
```

Add them through a wrapping helper:

```python
self.action_buttons = [
    self.start_button,
    self.stop_button,
    self.test_button,
    self.expand_button,
    self.report_button,
]
for button in self.action_buttons:
    button.pack(side="left", padx=5, pady=5)
```

- [ ] **Step 8: Build metrics/status/recent widgets**

Create metric labels:

```python
self.metric_labels = {}
for key, title in [
    ("result", "Sonuç"),
    ("confidence", "Güven"),
    ("fps", "FPS"),
    ("latency", "Gecikme"),
]:
    frame = ttk.Frame(self.metrics_frame, style="Metric.TFrame", padding=8)
    title_label = ttk.Label(frame, text=title, style="Muted.TLabel")
    value_label = ttk.Label(frame, text="-", font=("Roboto", 12, "bold"), background=self.surface_color, foreground=self.text_color)
    title_label.pack(anchor="w")
    value_label.pack(anchor="w", pady=(4, 0))
    self.metric_labels[key] = value_label
```

Create status and recent labels:

```python
self.status_title_label = ttk.Label(self.status_frame, text="Durum", style="Muted.TLabel")
self.status_title_label.pack(anchor="w")
self.status_value_label = ttk.Label(self.status_frame, text="Şiddet Yok", font=("Roboto", 20, "bold"), background=self.panel_color, foreground=self.safe_color)
self.status_value_label.pack(anchor="w", pady=(4, 0))

self.recent_title_label = ttk.Label(self.recent_frame, text="Son olaylar", font=("Roboto", 12, "bold"), background=self.panel_color, foreground=self.text_color)
self.recent_title_label.pack(anchor="w")
self.recent_events_label = ttk.Label(
    self.recent_frame,
    text="Kayıtlı şiddet olayı yok. Rapor oluşturulursa bilgi mesajı gösterilir.",
    background=self.panel_color,
    foreground=self.muted_text_color,
    wraplength=260,
    justify="left"
)
self.recent_events_label.pack(anchor="w", pady=(8, 0))
```

- [ ] **Step 9: Add responsive layout method**

Add:

```python
def _apply_responsive_layout(self, event=None):
    width = self.root.winfo_width()

    self.video_column.grid_forget()
    self.info_column.grid_forget()

    if width >= self.responsive_breakpoint:
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.columnconfigure(1, weight=0)
        self.video_column.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        self.info_column.grid(row=0, column=1, sticky="nsew")
    else:
        self.content_frame.columnconfigure(0, weight=1)
        self.video_column.grid(row=0, column=0, sticky="nsew")
        self.info_column.grid(row=1, column=0, sticky="ew", pady=(12, 0))

    for index, frame in enumerate(self.metrics_frame.winfo_children()):
        frame.grid_forget()
        if width >= self.responsive_breakpoint:
            columns = 2
        elif width >= 560:
            columns = 2
        else:
            columns = 1
        frame.grid(row=index // columns, column=index % columns, sticky="ew", padx=4, pady=4)

    for column in range(2):
        self.metrics_frame.columnconfigure(column, weight=1)

    self.metrics_frame.pack(fill="x")
    self.status_frame.pack(fill="x", pady=(10, 0))
    self.recent_frame.pack(fill="x", pady=(10, 0))
```

Bind it at the end of `__init__`:

```python
self.root.bind("<Configure>", self._apply_responsive_layout)
self.root.after(100, self._apply_responsive_layout)
self.root.after(100, self._refresh_recent_events)
```

- [ ] **Step 10: Compile**

Run:

```bash
python -m compileall main/violence_detection
```

Expected: code 0.

- [ ] **Step 11: Commit**

Run:

```bash
git add main/violence_detection/detection_gui.py
git commit -m "feat: modernize detection UI layout"
```

If this is not a Git repository, skip this step.

---

### Task 5: Update Live Frame Rendering And Status Metrics

**Files:**
- Modify: `main/violence_detection/detection_gui.py`

- [ ] **Step 1: Avoid mutating the frame used by screenshot flow**

In `update_frame`, replace:

```python
cv2.putText(self.frame, timestamp, ...)
rgb_frame = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
```

with:

```python
display_frame = self.frame.copy()
cv2.putText(display_frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)
rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
```

- [ ] **Step 2: Update metric labels instead of old info labels**

In `update_frame`, replace label updates for `result_label`, `fps_label`, `latency_label`, and `confidence_label` with:

```python
if hasattr(self, "metric_labels"):
    self.metric_labels["result"].config(text=self.label)
    self.metric_labels["confidence"].config(text=f"{int(self.confidence * 100)}%")
    self.metric_labels["fps"].config(text=f"{self.fps:.1f}")
    self.metric_labels["latency"].config(text=f"{self.latency:.3f}s")
```

- [ ] **Step 3: Update status panel**

Add in `update_frame`:

```python
if hasattr(self, "status_value_label"):
    is_alert = self.label == "Violence"
    self.status_value_label.config(
        text="Şiddet Algılandı" if is_alert else "Şiddet Yok",
        foreground=self.alert_color if is_alert else self.safe_color,
    )
```

- [ ] **Step 4: Preserve alert frame blinking**

Keep:

```python
if self.label == "Violence" and self.confidence > 0.8:
    if not self.alert_frame_active:
        self.alert_frame_active = True
        self._blink_frame()
else:
    self.alert_frame_active = False
```

- [ ] **Step 5: Compile**

Run:

```bash
python -m compileall main/violence_detection
```

Expected: code 0.

- [ ] **Step 6: Commit**

Run:

```bash
git add main/violence_detection/detection_gui.py
git commit -m "feat: update live metrics and alert rendering"
```

If this is not a Git repository, skip this step.

---

### Task 6: Manual Verification Pass

**Files:**
- No planned code changes unless verification finds a defect.

- [ ] **Step 1: Run compile check**

Run:

```bash
python -m compileall main/violence_detection
```

Expected: code 0.

- [ ] **Step 2: Run tests**

Run:

```bash
python -m pytest tests -v
```

Expected: all tests pass.

- [ ] **Step 3: Launch GUI in test mode**

Run:

```bash
python -m main.violence_detection.main --test
```

Expected:

- Window opens.
- Start button begins camera loop.
- If webcam is not available, terminal logs the camera error without hiding the UI design verification.
- UI shows header, live view, action bar, metrics, status, and recent events.

- [ ] **Step 4: Resize manually**

Use the window manager to test:

- Around 980x720: video left, info right.
- Around 760x720: info panel below video.
- Around 520x720: action buttons wrap and metric cards do not overlap.

Expected: no clipped button text, no incoherent overlap, scrollbar remains usable.

- [ ] **Step 5: Test empty report behavior**

With an empty `events.db`, click `Rapor Oluştur`.

Expected:

- No crash.
- User sees `Rapor için kayıtlı şiddet olayı yok.`
- Report button returns to normal state.

- [ ] **Step 6: Test missing screenshot report behavior**

Insert a dummy violence row with a missing screenshot path:

```bash
python -c "import sqlite3; conn=sqlite3.connect('events.db'); conn.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, label TEXT, confidence REAL, screenshot_path TEXT, fps REAL, latency REAL)'); conn.execute('INSERT INTO events (timestamp,label,confidence,screenshot_path,fps,latency) VALUES (?,?,?,?,?,?)', ('2026-06-02 21:00:00','Violence',0.91,'missing.png',14.2,0.05)); conn.commit(); conn.close()"
```

Click `Rapor Oluştur`.

Expected:

- No crash.
- PDF is generated.
- Missing image is noted in the PDF.
- Success message includes path and event count.

- [ ] **Step 7: Commit verification fixes if any**

If manual verification required code changes, run:

```bash
git add main/violence_detection tests
git commit -m "fix: resolve UI verification issues"
```

If this is not a Git repository or no fixes were needed, skip this step.

---

## Self-Review

Spec coverage:

- UI remains recognizable: Tasks 4 and 5.
- Modern responsive operator console: Task 4.
- Report crash safety: Tasks 1, 2, and 3.
- Recent events/readiness: Tasks 3 and 4.
- No overlap/responsive verification: Task 6.
- Start/stop update loop preservation: Task 5 preserves current single-loop behavior from the previous fix; Task 6 verifies.

Placeholder scan:

- No `TBD`, `TODO`, or undefined future tasks are used.
- Each code-changing task includes concrete code snippets.

Type consistency:

- `ReportGenerator.generate()` returns a dictionary with `success`, `reason`, `message`, `path`, and `event_count`.
- `DetectionGUI.generate_report()` reads that dictionary consistently.
- `DetectionGUI._refresh_recent_events()` uses `self.report_generator.db_path`, which already exists in `ReportGenerator.__init__`.
