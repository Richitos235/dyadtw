# AI Rules & Technical Standards - WestBot v6

This document defines the architectural boundaries, tech stack, and library usage rules for the `westbot_v6` project. All AI-generated code and manual contributions must adhere to these standards.

## Tech Stack

- **Python 3.12+**: The core language for all backend and orchestration logic.
- **Selenium 4.x**: Primary engine for browser automation, DOM interaction, and CDP (Chrome DevTools Protocol) access.
- **PySide6 (Qt for Python)**: The exclusive framework for the Graphical User Interface (GUI).
- **SQLite**: Used for structured, persistent storage of learned game data (jobs, towns).
- **JSON Persistence**: Used for application configuration (`config.json`) and transient queue state.
- **Threading**: Native Python `threading` for background automation, network sniffing, and monitoring.
- **Webdriver Manager**: Automated lifecycle management for the Chrome binary and driver.
- **Colorlog**: Enhanced terminal logging for development diagnostics.

## Library Usage Rules

### 1. Browser Automation
- **Library**: `selenium`.
- **Rule**: Use Selenium for all browser-side interactions. Do not introduce Playwright or Puppeteer unless a project-wide migration is explicitly requested.
- **Rule**: Access network traffic via Selenium's `performance` logs and CDP commands (`Network.enable`, `Network.getResponseBody`).

### 2. User Interface
- **Library**: `PySide6`.
- **Rule**: All UI components must reside in `ui/`.
- **Rule**: Use `.qss` files (Qt Style Sheets) for styling. Do not hardcode complex styles in Python.
- **Rule**: Maintain the tab-based architecture. New features should be implemented as new tabs or widgets within existing tabs.

### 3. Data & Persistence
- **Library**: `sqlite3` (Standard Library) and `json`.
- **Rule**: Use SQLite for "Learned" data that grows over time (Jobs, Towns).
- **Rule**: Use JSON via `StorageManager` for application settings and the automation queue.
- **Rule**: All database operations must be thread-safe using `RLock`.

### 4. Models & Data Structures
- **Library**: `dataclasses`.
- **Rule**: Define all domain entities (Tasks, Jobs, Towns) as Python dataclasses in the `models/` directory.
- **Rule**: Include `to_dict()` and `from_dict()` (or `from_row()`) methods for serialization.

### 5. Concurrency & Threading
- **Library**: `threading`.
- **Rule**: Background workers (TaskExecutor, NetworkSniffer) must run as `daemon` threads.
- **Rule**: Use `threading.Event` for signaling and graceful shutdowns.
- **Rule**: Never perform blocking I/O or long-running browser tasks on the main UI thread.

### 6. Logging
- **Library**: Centralized `LoggerManager`.
- **Rule**: Do not use `print()`. Use `self.logger.info()`, `debug()`, or `exception()`.
- **Rule**: Ensure logs are directed to both the console (colored) and the `westbot_v6.log` file.

## Architectural Constraints

- **Separation of Concerns**: The `core/` must remain agnostic of the UI. It should communicate via listeners/callbacks.
- **Thread Safety**: Any resource shared between the UI thread and the Automation thread (like the Queue) must be protected by an `RLock`.
- **Atomic Writes**: Configuration changes must be written atomically (write to `.tmp` then rename) to prevent corruption.