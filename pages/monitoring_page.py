"""
pages/monitoring_page.py
Monitoring page — layout direvisi mengikuti referensi.
Murni berfungsi sebagai sistem perekaman Data Logger per frame ke MySQL.
"""

from __future__ import annotations

import csv
from datetime import datetime

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QDoubleSpinBox,
    QSizePolicy,
    QScrollArea,
    QFileDialog,
    QMessageBox
)
from PySide6.QtCore import Qt, Signal, QTimer

from app_camera import AnkleCameraWidget
from widgets.metric_card import MetricCard
from widgets.status_badge import StatusBadge
from database.database_manager import DatabaseManager


class MonitoringPage(QWidget):
    navigate_back = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.db = DatabaseManager()
        self._respondent: dict = {}
        self._is_running = False
        self._elapsed_seconds = 0
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick_timer)
        
        self._session_angles = []
        
        self._build_ui()

    # ── UI Construction ─────────────────────────────────────────────────────
    def _build_ui(self):
        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        container.setObjectName("AppRoot")
        root = QVBoxLayout(container)
        root.setContentsMargins(32, 24, 32, 28)
        root.setSpacing(0)
        scroll.setWidget(container)

        page_layout = QVBoxLayout(self)
        page_layout.setContentsMargins(0, 0, 0, 0)
        page_layout.addWidget(scroll)

        nav_row = QHBoxLayout()
        back_btn = QPushButton("←  Kembali ke Daftar Responden")
        back_btn.setObjectName("BackBtn")
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.clicked.connect(self._on_back_clicked)
        nav_row.addWidget(back_btn)
        nav_row.addStretch()
        root.addLayout(nav_row)
        root.addSpacing(8)

        page_title_row = QHBoxLayout()
        page_title_lbl = QLabel("Monitoring Pengukuran")
        page_title_lbl.setObjectName("PageTitle")
        page_title_row.addWidget(page_title_lbl)
        page_title_row.addStretch()
        root.addLayout(page_title_row)
        root.addSpacing(20)

        info_card = QFrame()
        info_card.setObjectName("Card")
        info_layout = QHBoxLayout(info_card)
        info_layout.setContentsMargins(24, 18, 24, 18)
        info_layout.setSpacing(0)

        self.avatar_lbl = QLabel("B")
        self.avatar_lbl.setFixedSize(52, 52)
        self.avatar_lbl.setAlignment(Qt.AlignCenter)
        self.avatar_lbl.setStyleSheet(
            "background-color: #3E6E63; color: #FFFFFF; border-radius: 26px;"
            " font-size: 20px; font-weight: 700;"
        )
        info_layout.addWidget(self.avatar_lbl)
        info_layout.addSpacing(20)

        details_col = QVBoxLayout()
        details_col.setSpacing(4)
        self.respondent_name = QLabel("—")
        self.respondent_name.setStyleSheet(
            "font-size: 18px; font-weight: 700; color: #1A2340; background: transparent;"
        )
        self.respondent_meta = QLabel("—")
        self.respondent_meta.setStyleSheet(
            "font-size: 13px; color: #6B7A99; background: transparent;"
        )
        details_col.addWidget(self.respondent_name)
        details_col.addWidget(self.respondent_meta)
        info_layout.addLayout(details_col)
        info_layout.addStretch()

        status_col = QVBoxLayout()
        status_col.setAlignment(Qt.AlignCenter)
        status_label = QLabel("STATUS")
        status_label.setObjectName("SectionLabel")
        self.status_badge = StatusBadge("Normal", large=True)
        status_col.addWidget(status_label, alignment=Qt.AlignCenter)
        status_col.addSpacing(4)
        status_col.addWidget(self.status_badge, alignment=Qt.AlignCenter)
        info_layout.addLayout(status_col)
        info_layout.addSpacing(32)

        session_col = QVBoxLayout()
        session_col.setAlignment(Qt.AlignCenter)
        session_label_title = QLabel("SESI")
        session_label_title.setObjectName("SectionLabel")
        self.session_label = QLabel("#001")
        self.session_label.setStyleSheet(
            "font-size: 20px; font-weight: 800; color: #3E6E63; background: transparent;"
        )
        session_col.addWidget(session_label_title, alignment=Qt.AlignCenter)
        session_col.addSpacing(4)
        session_col.addWidget(self.session_label, alignment=Qt.AlignCenter)
        info_layout.addLayout(session_col)

        root.addWidget(info_card)
        root.addSpacing(20)

        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(16)

        self.card_sudut = MetricCard(label="Sudut Ankle", value="—", unit="°")
        self.card_waktu = MetricCard(label="Waktu Tempuh", value="00:00", unit="s")

        jarak_card = QFrame()
        jarak_card.setObjectName("Card")
        jarak_layout = QVBoxLayout(jarak_card)
        jarak_layout.setContentsMargins(20, 16, 20, 16)
        jarak_layout.setSpacing(6)

        jarak_title = QLabel("JARAK TEMPUH")
        jarak_title.setObjectName("SectionLabel")
        jarak_layout.addWidget(jarak_title)

        jarak_input_row = QHBoxLayout()
        jarak_input_row.setSpacing(6)
        self.jarak_input = QDoubleSpinBox()
        self.jarak_input.setRange(0.0, 999.9)
        self.jarak_input.setSingleStep(0.1)
        self.jarak_input.setValue(0.0)
        self.jarak_input.setDecimals(1)
        self.jarak_input.setSuffix("  m")
        self.jarak_input.setFixedHeight(38)
        self.jarak_input.setStyleSheet(
            "font-size: 15px; font-weight: 700; color: #1A2340;"
        )
        jarak_input_row.addWidget(self.jarak_input, stretch=1)
        jarak_layout.addLayout(jarak_input_row)

        metrics_row.addWidget(self.card_sudut, stretch=1)
        metrics_row.addWidget(self.card_waktu, stretch=1)
        metrics_row.addWidget(jarak_card, stretch=1)

        root.addLayout(metrics_row)
        root.addSpacing(20)

        cam_header_row = QHBoxLayout()
        cam_header = QLabel("Live Camera Feed")
        cam_header.setStyleSheet(
            "font-size: 13px; font-weight: 700; color: #6B7A99; background: transparent;"
        )
        cam_header_row.addWidget(cam_header)
        cam_header_row.addStretch()

        self.start_btn = QPushButton("▶  Start")
        self.start_btn.setObjectName("SuccessBtn")
        self.start_btn.setFixedHeight(40)
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.clicked.connect(self._on_start)

        self.stop_btn = QPushButton("⏹  Stop")
        self.stop_btn.setObjectName("DangerBtn")
        self.stop_btn.setFixedHeight(40)
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._on_stop)

        self.submit_btn = QPushButton("✔  Submit")
        self.submit_btn.setObjectName("PrimaryBtn")
        self.submit_btn.setFixedHeight(40)
        self.submit_btn.setCursor(Qt.PointingHandCursor)
        self.submit_btn.setEnabled(False)
        self.submit_btn.clicked.connect(self._on_submit)

        self.export_btn = QPushButton("⬇  Export")
        self.export_btn.setObjectName("GhostBtn")
        self.export_btn.setFixedHeight(40)
        self.export_btn.setCursor(Qt.PointingHandCursor)
        self.export_btn.setEnabled(True) 
        self.export_btn.clicked.connect(self._on_export)

        cam_header_row.addWidget(self.start_btn)
        cam_header_row.addWidget(self.stop_btn)
        cam_header_row.addWidget(self.submit_btn)
        cam_header_row.addWidget(self.export_btn)

        root.addLayout(cam_header_row)
        root.addSpacing(8)

        self.status_strip = QLabel("● Sesi belum dimulai")
        self.status_strip.setStyleSheet(
            "font-size: 11px; color: #9AA3B8; background: transparent;"
        )
        root.addWidget(self.status_strip)
        root.addSpacing(10)

        # ── Indeks Kamera (Silakan ubah angka 0 menjadi 2 jika perlu) ────────
        self.camera = AnkleCameraWidget(camera_source=0, embedded=True)
        self.camera.setMinimumSize(400, 380)
        self.camera.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.camera.angle_updated.connect(self._on_angle_updated)
        root.addWidget(self.camera, stretch=1)

    # ── Public API ───────────────────────────────────────────────────────────
    def set_respondent(self, data: dict):
        self._respondent = data
        name = data.get("nama", "—")
        umur = data.get("umur", "—")
        jk = data.get("jenis_kelamin", "—")
        status = data.get("status", "Normal")

        initial = name[0].upper() if name else "?"
        self.avatar_lbl.setText(initial)

        avatar_color = "#3E6E63" if status.lower() == "normal" else "#C0503F"
        self.avatar_lbl.setStyleSheet(
            f"background-color: {avatar_color}; color: #FFFFFF; border-radius: 26px;"
            " font-size: 20px; font-weight: 700;"
        )

        self.respondent_name.setText(name)
        self.respondent_meta.setText(f"{umur} tahun  •  {jk}")
        self.status_badge.set_status(status)

        self._reset_session()
        self.refresh_session_label()

    def refresh_session_label(self):
        uid = self._respondent.get("uid")
        if uid:
            total_sesi = self.db.get_session_count(uid)
            sesi_sekarang = total_sesi + 1
            self.session_label.setText(f"#{sesi_sekarang:03d}")

    # ── Session Control ───────────────────────────────────────────────────────
    def _on_start(self):
        self._is_running = True
        self._elapsed_seconds = 0
        self._session_angles.clear()
        
        self._timer.start(1000)
        self.camera.start_camera()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.submit_btn.setEnabled(False)
        self.export_btn.setEnabled(False)
        
        self.status_strip.setText("🔴 Sesi berjalan...")
        self.status_strip.setStyleSheet(
            "font-size: 11px; color: #C0503F; background: transparent;"
        )
        self.card_sudut.set_value("—")

    def _on_stop(self):
        self._is_running = False
        self._timer.stop()
        
        # Mencegah Blocking pada Main UI Thread
        self.status_strip.setText("⏳ Menghentikan hardware kamera...")
        self.status_strip.setStyleSheet("font-size: 11px; color: #D9A05B; background: transparent;")
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()
        
        self.camera.stop_camera()
        
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        
        if self._session_angles:
            self.submit_btn.setEnabled(True)
            self.export_btn.setEnabled(True)
            self.status_strip.setText("✅ Sesi dihentikan. Siap di-submit ke database.")
            self.status_strip.setStyleSheet(
                "font-size: 11px; color: #4C8F5E; background: transparent;"
            )
        else:
            self.submit_btn.setEnabled(False)
            self.export_btn.setEnabled(True)
            self.status_strip.setText("⚠️ Sesi dihentikan. Tidak ada data sudut terekam.")
            self.status_strip.setStyleSheet(
                "font-size: 11px; color: #D9A05B; background: transparent;"
            )

    def _on_submit(self):
        uid = self._respondent.get("uid")
        total_frames = len(self._session_angles)
        
        # Proteksi agar tidak ZeroDivisionError saat submit buffer kosong
        if not uid or total_frames == 0:
            self.status_strip.setText("❌ Error: Tidak ada frame sudut yang terekam.")
            self.status_strip.setStyleSheet("font-size: 11px; color: #C0503F; background: transparent;")
            return
            
        jarak = self.jarak_input.value()
        # Proteksi nilai waktu agar tidak 0 (minimal 1 detik untuk kalkulasi logger per-frame)
        waktu = max(1, self._elapsed_seconds) 
        
        avg_angle = sum(self._session_angles) / total_frames
        max_angle = max(self._session_angles)
        min_angle = min(self._session_angles)

        sesi_ke = int(self.session_label.text().replace("#", ""))

        # Proses Logging Database
        sesi_berhasil = self.db.save_session_with_logs(
            uid=uid,
            sesi_ke=sesi_ke,
            jarak=jarak,
            waktu_total=waktu,
            avg_angle=avg_angle,
            max_angle=max_angle,
            min_angle=min_angle,
            list_sudut=self._session_angles
        )

        if sesi_berhasil:
            self.submit_btn.setEnabled(False)
            self.refresh_session_label() 
            self._session_angles.clear() # Reset logger bersih setelah submit
            
            self.status_strip.setText("📤 Sukses! Seluruh raw data logger sesi berhasil disimpan ke MySQL.")
            self.status_strip.setStyleSheet("font-size: 11px; color: #3E6E63; background: transparent;")
        else:
            self.status_strip.setText("❌ Gagal memperbarui data logger ke database MySQL.")
            self.status_strip.setStyleSheet("font-size: 11px; color: #C0503F; background: transparent;")
            
        self.start_btn.setEnabled(True)
        
    def _on_export(self):
        uid = self._respondent.get("uid")
        nama = self._respondent.get("nama", "Responden")
        
        if not uid:
            QMessageBox.warning(self, "Peringatan", "Tidak ada responden yang aktif.")
            return

        raw_logs = self.db.get_raw_gait_logs(uid)
        
        if not raw_logs:
            QMessageBox.information(self, "Info", f"Belum ada rekaman raw data logger untuk {nama} yang bisa diekspor.")
            return

        date_str = datetime.now().strftime("%Y%m%d")
        safe_name = nama.replace(" ", "_")
        default_filename = f"Raw_Gait_Logger_{safe_name}_{date_str}.csv"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Ekspor Raw Data Logger ke CSV",
            default_filename,
            "CSV Files (*.csv);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file, delimiter=',')
                    
                    writer.writerow([
                        "UID Responden",
                        "Nama Responden",
                        "Sesi Ke-",
                        "Frame Ke-",
                        "Waktu Relatif (Detik)",
                        "Sudut Ankle Terukur (°)",
                        "Timestamp Perekaman"
                    ])
                    
                    for log in raw_logs:
                        writer.writerow([
                            uid,
                            nama,
                            log.get('sesi_ke', ''),
                            log.get('frame_ke', ''),
                            f"{log.get('waktu_relatif', 0):.3f}",
                            f"{log.get('sudut_ankle', 0):.1f}", 
                            log.get('waktu_ambil', '')
                        ])

                self.status_strip.setText(f"✅ Raw data sukses diekspor ke: {file_path}")
                self.status_strip.setStyleSheet("font-size: 11px; color: #3E6E63; background: transparent;")
                QMessageBox.information(self, "Ekspor Berhasil", f"Seluruh raw data per frame berhasil disimpan di:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Error Ekspor", f"Terjadi kesalahan saat menulis file CSV:\n{str(e)}")

    def _reset_session(self):
        self._is_running = False
        self._elapsed_seconds = 0
        self._session_angles.clear()
        self._timer.stop()
        self.camera.stop_camera()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.submit_btn.setEnabled(False)
        self.export_btn.setEnabled(True)
        self.card_sudut.set_value("—")
        self.card_waktu.set_value("00:00")
        self.status_strip.setText("● Sesi belum dimulai")
        self.status_strip.setStyleSheet(
            "font-size: 11px; color: #9AA3B8; background: transparent;"
        )

    def _tick_timer(self):
        self._elapsed_seconds += 1
        minutes = self._elapsed_seconds // 60
        seconds = self._elapsed_seconds % 60
        self.card_waktu.set_value(f"{minutes:02d}:{seconds:02d}")

    # ── Camera integration ──────────────────────────────────────────────────
    def _on_angle_updated(self, angle, side_label):
        if angle is None:
            self.card_sudut.set_value("—")
        else:
            self.card_sudut.set_value(f"{angle:.1f}")
            if self._is_running:
                self._session_angles.append(angle)

    def _on_back_clicked(self):
        self.camera.stop_camera()
        self.navigate_back.emit()