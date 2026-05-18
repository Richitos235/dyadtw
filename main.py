from pathlib import Path

from PySide6.QtWidgets import QApplication

from core.browser_manager import BrowserManager
from core.injector_manager import InjectorManager
from core.logger_manager import LoggerManager
from core.network_sniffer import NetworkSniffer
from core.parser_engine import ParserEngine
from core.queue_manager import QueueManager
from core.storage_manager import StorageManager
from core.task_executor import TaskExecutor
from core.api_server import ApiServer
from database.database_manager import DatabaseManager
from ui.main_window import MainWindow


def main() -> None:
    root_folder = Path(__file__).resolve().parent
    storage = StorageManager(root_folder)
    storage.create_default_config()
    logger_manager = LoggerManager(root_folder / "westbot_v6.log", storage.config.get("logging", {}).get("level", "INFO"))
    logger = logger_manager.get_logger()

    browser_manager = BrowserManager(root_folder, storage, logger)
    database_manager = DatabaseManager(storage.get_database_path(), logger)
    parser_engine = ParserEngine(logger)
    network_sniffer = NetworkSniffer(browser_manager, parser_engine, database_manager, logger)
    injector_manager = InjectorManager(root_folder / "js" / "injector.js", browser_manager, logger)
    queue_manager = QueueManager(storage, logger)
    task_executor = TaskExecutor(queue_manager, browser_manager, injector_manager, storage, logger)

    # Initialize and start the Audit API Server
    api_server = ApiServer(database_manager, logger)
    api_server.start()

    browser_manager.set_injector(injector_manager)
    network_sniffer.start()
    task_executor.start()

    app = QApplication([])
    app_window = MainWindow(
        storage=storage,
        logger=logger,
        queue_manager=queue_manager,
        browser_manager=browser_manager,
        task_executor=task_executor,
        injector_manager=injector_manager,
        database_manager=database_manager,
    )
    app_window.show()
    app.exec()


if __name__ == "__main__":
    main()