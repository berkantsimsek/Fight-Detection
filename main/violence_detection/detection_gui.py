import os
import subprocess
import sqlite3
import sys
import time
import tkinter as tk
from tkinter import messagebox, ttk

import cv2
from PIL import Image, ImageTk


class DetectionGUI:
    def __init__(self, root, canvas_width, canvas_height, detector, alarm_manager, report_generator):
        self.root = root
        self.root.title("Şiddet Algılama Sistemi")
        self.running = False
        self.frame = None
        self.label = "Şiddet Yok"
        self.confidence = 0.0
        self.fps = 0.0
        self.latency = 0.0
        self.alert_frame_active = False
        self.detector = detector
        self.alarm_manager = alarm_manager
        self.report_generator = report_generator
        self.is_expanded = False
        self.original_canvas_size = (canvas_width, canvas_height)
        self.update_job = None
        self.report_running = False
        self.recent_events = []
        self.responsive_breakpoint = 900
        self.action_columns = None

        self.bg_color = "#F4F6F8"
        self.panel_color = "#FFFFFF"
        self.surface_color = "#F8FAFC"
        self.video_bg_color = "#1F2937"
        self.text_color = "#17212B"
        self.muted_text_color = "#64748B"
        self.line_color = "#D8DEE6"
        self.accent_color = "#2563EB"
        self.alert_color = "#DC2626"
        self.safe_color = "#16A34A"
        self.warning_color = "#B45309"
        self.root.configure(bg=self.bg_color)

        self._center_window(980, 720)
        self._configure_styles()
        self._load_icons()
        self._build_layout(canvas_width, canvas_height)

        self.root.bind("<Control-e>", lambda event: self.toggle_expand())
        self.root.bind("<Configure>", self._apply_responsive_layout)
        self.root.after(100, self._apply_responsive_layout)
        self.root.after(150, self._refresh_recent_events)

    def _center_window(self, width, height):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(520, 560)

    def _configure_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Main.TFrame", background=self.bg_color)
        style.configure("Panel.TFrame", background=self.panel_color, relief="flat")
        style.configure("Surface.TFrame", background=self.surface_color, relief="flat")
        style.configure("TLabel", font=("Roboto", 11), foreground=self.text_color, background=self.bg_color)
        style.configure("Panel.TLabel", font=("Roboto", 11), foreground=self.text_color, background=self.panel_color)
        style.configure("Surface.TLabel", font=("Roboto", 11), foreground=self.text_color, background=self.surface_color)
        style.configure("Muted.TLabel", font=("Roboto", 10), foreground=self.muted_text_color, background=self.bg_color)
        style.configure("PanelMuted.TLabel", font=("Roboto", 10), foreground=self.muted_text_color, background=self.panel_color)
        style.configure("SurfaceMuted.TLabel", font=("Roboto", 10), foreground=self.muted_text_color, background=self.surface_color)
        style.configure("Title.TLabel", font=("Roboto", 20, "bold"), foreground=self.text_color, background=self.bg_color)
        style.configure("MetricValue.TLabel", font=("Roboto", 13, "bold"), foreground=self.text_color, background=self.surface_color)
        style.configure("StatusValue.TLabel", font=("Roboto", 21, "bold"), foreground=self.safe_color, background=self.panel_color)
        style.configure("Primary.TButton", font=("Roboto", 11, "bold"), padding=(12, 10))
        style.configure("Secondary.TButton", font=("Roboto", 11), padding=(12, 10))

    def _load_icons(self):
        base_path = os.path.dirname(__file__)
        self.start_icon = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "play.png")).resize((24, 24)))
        self.stop_icon = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "stop.png")).resize((24, 24)))
        self.test_icon = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "gear.png")).resize((24, 24)))
        self.expand_icon = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "expand.png")).resize((24, 24)))
        self.shrink_icon = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "shrink.png")).resize((24, 24)))
        self.report_icon = ImageTk.PhotoImage(Image.open(os.path.join(base_path, "report.png")).resize((24, 24)))

    def _build_layout(self, canvas_width, canvas_height):
        self.shell_frame = ttk.Frame(self.root, style="Main.TFrame")
        self.shell_frame.pack(fill="both", expand=True)

        self.scroll_canvas = tk.Canvas(self.shell_frame, bg=self.bg_color, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self.shell_frame, orient="vertical", command=self.scroll_canvas.yview)
        self.scroll_canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.scroll_canvas.pack(side="left", fill="both", expand=True)

        self.main_frame = ttk.Frame(self.scroll_canvas, style="Main.TFrame")
        self.main_window = self.scroll_canvas.create_window((0, 0), window=self.main_frame, anchor="nw")
        self.main_frame.bind("<Configure>", self._update_scroll_region)
        self.scroll_canvas.bind("<Configure>", self._resize_scroll_window)
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<Button-4>", self._on_mousewheel)
        self.root.bind_all("<Button-5>", self._on_mousewheel)

        self.header_frame = ttk.Frame(self.main_frame, style="Main.TFrame")
        self.header_frame.pack(fill="x", padx=18, pady=(18, 10))
        self.title_label = ttk.Label(self.header_frame, text="Şiddet Algılama Sistemi", style="Title.TLabel")
        self.title_label.pack(anchor="w")
        self.subtitle_label = ttk.Label(
            self.header_frame,
            text="Canlı kamera izleme · Webcam/RTSP · Model hazır",
            style="Muted.TLabel",
        )
        self.subtitle_label.pack(anchor="w", pady=(4, 0))

        self.content_frame = ttk.Frame(self.main_frame, style="Main.TFrame")
        self.content_frame.pack(fill="both", expand=True, padx=18, pady=8)

        self.video_column = ttk.Frame(self.content_frame, style="Main.TFrame")
        self.info_column = ttk.Frame(self.content_frame, style="Main.TFrame")

        self.canvas_frame = tk.Frame(
            self.video_column,
            bg=self.panel_color,
            bd=0,
            highlightbackground=self.line_color,
            highlightthickness=1,
        )
        self.canvas_frame.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(
            self.canvas_frame,
            width=canvas_width,
            height=canvas_height,
            bg=self.video_bg_color,
            highlightthickness=0,
        )
        self.canvas.pack(fill="both", expand=True, padx=8, pady=8)

        self.action_frame = ttk.Frame(self.video_column, style="Panel.TFrame", padding=10)
        self.action_frame.pack(fill="x", pady=(10, 0))
        self._build_action_buttons()

        self.metrics_frame = ttk.Frame(self.info_column, style="Panel.TFrame", padding=12)
        self.status_panel = ttk.Frame(self.info_column, style="Panel.TFrame", padding=12)
        self.recent_frame = ttk.Frame(self.info_column, style="Panel.TFrame", padding=12)
        self._build_metrics_panel()
        self._build_status_panel()
        self._build_recent_panel()

    def _build_action_buttons(self):
        self.start_button = ttk.Button(
            self.action_frame,
            text="Başlat",
            image=self.start_icon,
            compound="left",
            command=self.start,
            style="Primary.TButton",
        )
        self.stop_button = ttk.Button(
            self.action_frame,
            text="Durdur",
            image=self.stop_icon,
            compound="left",
            command=self.stop,
            state="disabled",
            style="Primary.TButton",
        )
        self.test_button = ttk.Button(
            self.action_frame,
            text="Test Modu",
            image=self.test_icon,
            compound="left",
            command=self.toggle_test_mode,
            style="Secondary.TButton",
        )
        self.expand_button = ttk.Button(
            self.action_frame,
            text="Büyüt",
            image=self.expand_icon,
            compound="left",
            command=self.toggle_expand,
            style="Secondary.TButton",
        )
        self.report_button = ttk.Button(
            self.action_frame,
            text="Rapor Oluştur",
            image=self.report_icon,
            compound="left",
            command=self.generate_report,
            style="Secondary.TButton",
        )
        self.view_reports_button = ttk.Button(
            self.action_frame,
            text="Raporu Görüntüle",
            image=self.report_icon,
            compound="left",
            command=self.show_reports_modal,
            style="Secondary.TButton",
        )
        self.action_buttons = [
            self.start_button,
            self.stop_button,
            self.test_button,
            self.expand_button,
            self.report_button,
            self.view_reports_button,
        ]

    def _build_metrics_panel(self):
        ttk.Label(self.metrics_frame, text="Sistem Bilgileri", style="PanelMuted.TLabel").grid(
            row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(0, 8)
        )
        self.metric_labels = {}
        for index, (key, title) in enumerate(
            [
                ("result", "Sonuç"),
                ("confidence", "Güven"),
                ("fps", "FPS"),
                ("latency", "Gecikme"),
            ],
            start=1,
        ):
            frame = ttk.Frame(self.metrics_frame, style="Surface.TFrame", padding=9)
            title_label = ttk.Label(frame, text=title, style="SurfaceMuted.TLabel")
            value_label = ttk.Label(frame, text="-", style="MetricValue.TLabel")
            title_label.pack(anchor="w")
            value_label.pack(anchor="w", pady=(4, 0))
            self.metric_labels[key] = value_label
            frame.grid(row=(index - 1) // 2 + 1, column=(index - 1) % 2, sticky="ew", padx=4, pady=4)

        self.metrics_frame.columnconfigure(0, weight=1)
        self.metrics_frame.columnconfigure(1, weight=1)

    def _build_status_panel(self):
        self.status_label = ttk.Label(self.status_panel, text="Durum: Bekliyor", style="PanelMuted.TLabel")
        self.status_label.pack(anchor="w")
        self.status_value_label = ttk.Label(self.status_panel, text="Şiddet Yok", style="StatusValue.TLabel")
        self.status_value_label.pack(anchor="w", pady=(5, 0))
        self.confidence_bar = tk.Canvas(self.status_panel, height=10, bg=self.panel_color, highlightthickness=0)
        self.confidence_bar.pack(fill="x", pady=(10, 0))
        self.confidence_track = self.confidence_bar.create_rectangle(0, 0, 1, 10, fill="#E2E8F0", outline="")
        self.confidence_fill = self.confidence_bar.create_rectangle(0, 0, 1, 10, fill=self.safe_color, outline="")
        self.confidence_bar.bind("<Configure>", lambda event: self._draw_confidence_bar())

    def _build_recent_panel(self):
        ttk.Label(self.recent_frame, text="Son olaylar", style="Panel.TLabel", font=("Roboto", 12, "bold")).pack(
            anchor="w"
        )
        self.recent_events_label = ttk.Label(
            self.recent_frame,
            text="Kayıtlı şiddet olayı yok. Rapor oluşturulursa bilgi mesajı gösterilir.",
            style="PanelMuted.TLabel",
            justify="left",
            wraplength=260,
        )
        self.recent_events_label.pack(anchor="w", pady=(8, 0))

    def _apply_responsive_layout(self, event=None):
        width = self.root.winfo_width()

        self.video_column.grid_forget()
        self.info_column.grid_forget()

        if width >= self.responsive_breakpoint:
            self.content_frame.columnconfigure(0, weight=1)
            self.content_frame.columnconfigure(1, weight=0)
            self.content_frame.rowconfigure(0, weight=1)
            self.content_frame.rowconfigure(1, weight=0)
            self.video_column.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
            self.info_column.grid(row=0, column=1, sticky="new")
            self.recent_events_label.configure(wraplength=260)
        else:
            self.content_frame.columnconfigure(0, weight=1)
            self.content_frame.columnconfigure(1, weight=0)
            self.content_frame.rowconfigure(0, weight=1)
            self.content_frame.rowconfigure(1, weight=0)
            self.video_column.grid(row=0, column=0, sticky="nsew")
            self.info_column.grid(row=1, column=0, sticky="ew", pady=(12, 0))
            self.recent_events_label.configure(wraplength=max(260, width - 80))

        self.metrics_frame.pack(fill="x")
        self.status_panel.pack(fill="x", pady=(10, 0))
        self.recent_frame.pack(fill="x", pady=(10, 0))
        self._layout_action_buttons(width)

    def _layout_action_buttons(self, width):
        columns = 6 if width >= 1060 else 3 if width >= 640 else 2
        if columns == self.action_columns:
            return
        self.action_columns = columns
        for button in self.action_buttons:
            button.grid_forget()
        for column in range(6):
            self.action_frame.columnconfigure(column, weight=0)
        for index, button in enumerate(self.action_buttons):
            button.grid(row=index // columns, column=index % columns, sticky="ew", padx=5, pady=5)
        for column in range(columns):
            self.action_frame.columnconfigure(column, weight=1)

    def start(self):
        if not self.running:
            self.running = True
            self.start_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.status_label.config(text="Durum: Çalışıyor")
            if self.update_job is None:
                self.update_frame()

    def stop(self):
        self.running = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.status_label.config(text="Durum: Durduruldu")
        self.canvas.delete("all")
        self.frame = None
        if self.update_job is not None:
            self.root.after_cancel(self.update_job)
            self.update_job = None

    def toggle_test_mode(self):
        current_mode = self.detector.test_mode
        self.detector.set_test_mode(not current_mode)
        self.test_button.config(text="Test Modu OFF" if not current_mode else "Test Modu ON")
        self.status_label.config(text=f"Durum: {'Test Aktif' if not current_mode else 'Çalışıyor'}")

    def toggle_expand(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.expand_button.config(text="Küçült", image=self.shrink_icon)
            new_width = int(self.original_canvas_size[0] * 1.5)
            new_height = int(self.original_canvas_size[1] * 1.5)
            self.canvas.config(width=new_width, height=new_height)
            self.root.geometry(f"{new_width + 420}x{new_height + 260}")
        else:
            self.expand_button.config(text="Büyüt", image=self.expand_icon)
            self.canvas.config(width=self.original_canvas_size[0], height=self.original_canvas_size[1])
            self._center_window(980, 720)
        self.root.after(50, self._apply_responsive_layout)

    def update_frame(self):
        self.update_job = None
        if self.running and self.frame is not None:
            display_frame = self.frame.copy()
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(
                display_frame,
                timestamp,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
                cv2.LINE_AA,
            )

            rgb_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
            canvas_width = max(1, self.canvas.winfo_width())
            canvas_height = max(1, self.canvas.winfo_height())
            resized_frame = cv2.resize(rgb_frame, (canvas_width, canvas_height))
            img = Image.fromarray(resized_frame)
            imgtk = ImageTk.PhotoImage(image=img)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
            self.canvas.imgtk = imgtk

            if self.label == "Violence" and self.confidence > 0.8:
                if not self.alert_frame_active:
                    self.alert_frame_active = True
                    self._blink_frame()
            else:
                self.alert_frame_active = False

            self._update_metrics()

        if self.running:
            self.update_job = self.root.after(30, self.update_frame)

    def _update_metrics(self):
        is_alert = self.label == "Violence"
        status_text = "Şiddet Algılandı" if is_alert else "Şiddet Yok"
        status_color = self.alert_color if is_alert else self.safe_color

        self.metric_labels["result"].config(text=self.label)
        self.metric_labels["confidence"].config(text=f"{int(self.confidence * 100)}%")
        self.metric_labels["fps"].config(text=f"{self.fps:.1f}")
        self.metric_labels["latency"].config(text=f"{self.latency:.3f}s")
        self.status_value_label.config(text=status_text, foreground=status_color)
        self._draw_confidence_bar()

    def _draw_confidence_bar(self):
        width = max(1, self.confidence_bar.winfo_width())
        fill_width = max(1, int(width * max(0.0, min(1.0, self.confidence))))
        fill_color = self.alert_color if self.label == "Violence" else self.safe_color
        self.confidence_bar.coords(self.confidence_track, 0, 0, width, 10)
        self.confidence_bar.coords(self.confidence_fill, 0, 0, fill_width, 10)
        self.confidence_bar.itemconfig(self.confidence_fill, fill=fill_color)

    def _blink_frame(self):
        if self.alert_frame_active and self.running:
            self.canvas.create_rectangle(
                0,
                0,
                self.canvas.winfo_width(),
                self.canvas.winfo_height(),
                outline=self.alert_color,
                width=5,
                tags="alert",
            )
            self.root.after(500, lambda: self.canvas.delete("alert"))
            self.root.after(1000, self._blink_frame)

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
                    f"{result.get('message')}\nOlay sayısı: {result.get('event_count', 0)}",
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

    def show_reports_modal(self):
        reports = self._list_pdf_reports()
        modal = tk.Toplevel(self.root)
        modal.title("Raporlar")
        modal.transient(self.root)
        modal.grab_set()
        modal.configure(bg=self.bg_color)
        modal.geometry(self._modal_geometry(620, 420))
        modal.minsize(420, 300)

        container = ttk.Frame(modal, style="Main.TFrame", padding=16)
        container.pack(fill="both", expand=True)

        ttk.Label(container, text="Görüntülenebilecek Raporlar", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            container,
            text="Bir rapor seçip aç butonuna basın ya da listedeki rapora çift tıklayın.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(4, 12))

        list_frame = ttk.Frame(container, style="Panel.TFrame")
        list_frame.pack(fill="both", expand=True)
        listbox = tk.Listbox(
            list_frame,
            height=10,
            activestyle="dotbox",
            bg=self.panel_color,
            fg=self.text_color,
            selectbackground=self.accent_color,
            selectforeground="#FFFFFF",
            highlightthickness=1,
            highlightbackground=self.line_color,
            relief="flat",
            font=("Roboto", 10),
        )
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for report in reports:
            size_kb = max(1, report.stat().st_size // 1024)
            modified = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(report.stat().st_mtime))
            listbox.insert("end", f"{report.name}  ·  {modified}  ·  {size_kb} KB")

        if reports:
            listbox.selection_set(0)
            listbox.activate(0)
        else:
            listbox.insert("end", "Henüz PDF raporu yok.")
            listbox.config(state="disabled")

        button_frame = ttk.Frame(container, style="Main.TFrame")
        button_frame.pack(fill="x", pady=(12, 0))

        def open_selected(event=None):
            if not reports:
                return
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Rapor", "Lütfen açılacak raporu seçin.")
                return
            self._open_pdf_report(reports[selection[0]])
            modal.destroy()

        ttk.Button(button_frame, text="Aç", command=open_selected, style="Primary.TButton").pack(side="left")
        ttk.Button(button_frame, text="Kapat", command=modal.destroy, style="Secondary.TButton").pack(side="right")
        listbox.bind("<Double-Button-1>", open_selected)
        modal.bind("<Escape>", lambda event: modal.destroy())
        modal.wait_window()

    def _modal_geometry(self, width, height):
        self.root.update_idletasks()
        x = self.root.winfo_rootx() + max(0, (self.root.winfo_width() - width) // 2)
        y = self.root.winfo_rooty() + max(0, (self.root.winfo_height() - height) // 2)
        return f"{width}x{height}+{x}+{y}"

    def _list_pdf_reports(self):
        report_dir = self.report_generator.report_path
        if not os.path.isabs(report_dir):
            report_dir = os.path.abspath(report_dir)
        if not os.path.isdir(report_dir):
            return []
        reports = [
            os.path.join(report_dir, name)
            for name in os.listdir(report_dir)
            if name.lower().endswith(".pdf")
        ]
        reports.sort(key=lambda path: os.path.getmtime(path), reverse=True)
        from pathlib import Path
        return [Path(path) for path in reports]

    def _open_pdf_report(self, report_path):
        try:
            path = str(report_path)
            if sys.platform.startswith("win"):
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            print(f"Rapor açılamadı: {e}")
            messagebox.showerror("Rapor", "Rapor varsayılan PDF görüntüleyici ile açılamadı.")

    def _refresh_recent_events(self):
        try:
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

    def _render_recent_events(self):
        if not hasattr(self, "recent_events_label"):
            return

        if not self.recent_events:
            text = "Kayıtlı şiddet olayı yok. Rapor oluşturulursa bilgi mesajı gösterilir."
        else:
            lines = [f"Son {len(self.recent_events)} olay:"]
            for timestamp, confidence, screenshot_path in self.recent_events:
                try:
                    confidence_value = float(confidence)
                except (TypeError, ValueError):
                    confidence_value = 0.0
                image_state = "görüntü var" if screenshot_path and os.path.exists(str(screenshot_path)) else "görüntü yok"
                lines.append(f"{timestamp} · {confidence_value:.2f} · {image_state}")
            text = "\n".join(lines)

        self.recent_events_label.config(text=text)

    def _update_scroll_region(self, event=None):
        self.scroll_canvas.configure(scrollregion=self.scroll_canvas.bbox("all"))

    def _resize_scroll_window(self, event):
        self.scroll_canvas.itemconfigure(self.main_window, width=event.width)

    def _on_mousewheel(self, event):
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            delta = -1 * int(event.delta / 120)
        self.scroll_canvas.yview_scroll(delta, "units")
