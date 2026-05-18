from typing import Dict

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from core.storage_manager import StorageManager


class SettingsTab(QWidget):
    def __init__(self, storage: StorageManager, logger) -> None:
        super().__init__()
        self.storage = storage
        self.logger = logger
        self._build_ui()
        self.refresh()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.headless_checkbox = QCheckBox("Run browser headless")
        self.delay_spin = QSpinBox()
        self.delay_spin.setRange(1, 10)
        self.delay_spin.setSuffix("x")
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 10)
        self.max_queue_spin = QSpinBox()
        self.max_queue_spin.setRange(1, 50)
        self.logging_level = QComboBox()
        self.logging_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.theme_selector = QComboBox()
        self.theme_selector.addItems(["dark"])

        form.addRow(QLabel("Browser Headless:"), self.headless_checkbox)
        form.addRow(QLabel("Delay multiplier:"), self.delay_spin)
        form.addRow(QLabel("Scheduler interval (s):"), self.interval_spin)
        form.addRow(QLabel("Max queue length:"), self.max_queue_spin)
        form.addRow(QLabel("Log level:"), self.logging_level)
        form.addRow(QLabel("UI theme:"), self.theme_selector)

        button_row = QHBoxLayout()
        save_button = QPushButton("Save Settings")
        save_button.clicked.connect(self._save_settings)
        button_row.addWidget(save_button)

        layout.addLayout(form)
        layout.addLayout(button_row)

    def refresh(self) -> None:
        config = self.storage.config
        browser_settings = config.get("browser", {})
        scheduler_settings = config.get("scheduler", {})
        ui_settings = config.get("ui", {})

        self.headless_checkbox.setChecked(bool(browser_settings.get("headless", False)))
        self.delay_spin.setValue(int(browser_settings.get("delay_multiplier", 1.0)))
        self.interval_spin.setValue(int(scheduler_settings.get("poll_interval_seconds", 2)))
        self.max_queue_spin.setValue(int(scheduler_settings.get("max_queue_length", 12)))
        self.logging_level.setCurrentText(config.get("logging", {}).get("level", "DEBUG"))
        self.theme_selector.setCurrentText(ui_settings.get("theme", "dark"))

    def _save_settings(self) -> None:
        config = self.storage.config
        config["browser"]["headless"] = self.headless_checkbox.isChecked()
        config["browser"]["delay_multiplier"] = float(self.delay_spin.value())
        config["scheduler"]["poll_interval_seconds"] = int(self.interval_spin.value())
        config["scheduler"]["max_queue_length"] = int(self.max_queue_spin.value())
        config["logging"]["level"] = self.logging_level.currentText()
        config["ui"]["theme"] = self.theme_selector.currentText()
        self.storage.save_config()
        self.logger.info("Settings saved")
