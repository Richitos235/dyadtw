from pathlib import Path

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from core.browser_manager import BrowserManager
from core.injector_manager import InjectorManager
from core.queue_manager import QueueManager
from core.storage_manager import StorageManager
from core.task_executor import TaskExecutor
from database.database_manager import DatabaseManager
from ui.tabs.game_queue_tab import GameQueueTab
from ui.tabs.jobs_database_tab import JobsDatabaseTab
from ui.tabs.queue_tab import QueueTab
from ui.tabs.settings_tab import SettingsTab


class MainWindow(QMainWindow):
    def __init__(
        self,
        storage: StorageManager,
        logger,
        queue_manager: QueueManager,
        browser_manager: BrowserManager,
        task_executor: TaskExecutor,
        injector_manager: InjectorManager,
        database_manager: DatabaseManager,
    ) -> None:
        super().__init__()
        self.storage = storage
        self.logger = logger
        self.queue_manager = queue_manager
        self.browser_manager = browser_manager
        self.task_executor = task_executor
        self.injector_manager = injector_manager
        self.database_manager = database_manager
        self.setWindowTitle("WestBot v6")
        self.resize(1300, 900)
        self._build_ui()
        self._load_saved_credentials()
        self._apply_theme()
        self._start_refresh_timer()

    def _build_ui(self) -> None:
        container = QWidget(self)
        self.setCentralWidget(container)
        layout = QVBoxLayout(container)
        control_row = QHBoxLayout()

        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)

        self.browser_button = QPushButton("Start Browser")
        self.browser_button.clicked.connect(self._on_start_browser)
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self._on_login)

        control_row.addWidget(self.username_input)
        control_row.addWidget(self.password_input)
        control_row.addWidget(self.browser_button)
        control_row.addWidget(self.login_button)

        layout.addLayout(control_row)

        self.tab_widget = QTabWidget(self)
        self.queue_tab = QueueTab(self.queue_manager, self.logger)
        self.game_queue_tab = GameQueueTab(self.queue_manager, self.browser_manager, self.injector_manager, self.logger)
        self.jobs_database_tab = JobsDatabaseTab(self.queue_manager, self.database_manager, self.browser_manager, self.logger)
        self.settings_tab = SettingsTab(self.storage, self.logger)

        self.tab_widget.addTab(self.queue_tab, "Queue")
        self.tab_widget.addTab(self.game_queue_tab, "Game Queue")
        self.tab_widget.addTab(self.jobs_database_tab, "Jobs Database")
        self.tab_widget.addTab(self.settings_tab, "Settings")

        layout.addWidget(self.tab_widget)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("WestBot v6 ready")

    def _apply_theme(self) -> None:
        theme = self.storage.config.get("ui", {}).get("theme", "dark")
        style_file = Path(__file__).resolve().parent.parent / "assets" / "themes" / f"{theme}.qss"
        if style_file.exists():
            self.setStyleSheet(style_file.read_text(encoding="utf-8"))

    def _start_refresh_timer(self) -> None:
        timer = QTimer(self)
        timer.timeout.connect(self._refresh_views)
        timer.start(1200)

    def _refresh_views(self) -> None:
        self.queue_tab.refresh()
        self.game_queue_tab.refresh()
        self.jobs_database_tab.refresh()
        self.settings_tab.refresh()

    def _on_start_browser(self) -> None:
        if self.browser_manager.start():
            self.status_bar.showMessage("Browser ready")
            self.logger.info("Browser started from UI")
        else:
            self.status_bar.showMessage("Browser failed to start")

    def _load_saved_credentials(self) -> None:
        credentials = self.storage.get_credentials()
        self.username_input.setText(credentials.get("username", ""))
        self.password_input.setText(credentials.get("password", ""))

    def _on_login(self) -> None:
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        if not username or not password:
            self.status_bar.showMessage("Username and password are required")
            return
        if self.browser_manager.start() and self.browser_manager.login(username, password):
            self.storage.save_credentials(username, password)
            self.status_bar.showMessage("Logged in successfully")
            self.logger.info("User logged in through UI")
        else:
            self.status_bar.showMessage("Login failed")
