# westbot_v6 Ultimate

`westbot_v6 Ultimate` is an enterprise-grade browser automation platform for The West game ecosystem. It combines intelligent browser control, network-aware task discovery, persistent queue management, and a responsive modern UI to deliver scalable, maintainable automation for developers, contributors, maintainers, and AI-assisted workflows.

This project is designed as a modular automation framework with strong thread-safe execution, database-backed learned insights, and an extensible architecture that supports future migration paths, including Playwright, distributed queueing, plugin layers, and AI-driven automation.

---

## Project Purpose

`westbot_v6 Ultimate` exists to automate game tasks, capture browser activity, and convert in-game interactions into persistent automation artifacts. It is optimized for:

- automated task scheduling,
- browser-based task injection,
- network-level learning of jobs/towns,
- maintaining safe, thread-aware execution,
- storing learned automation records in SQLite,
- exposing a polished UI for interactive and unattended operation.

The system is intentionally architected to be both automation-first and maintainability-first, enabling contributions from developers, reverse engineers, and automation engineers.

---

## Architecture Philosophy

This project follows a strict separation of concerns:

- `core/` contains automation orchestration, browser control, queue management, and state recovery.
- `ui/` renders the management console and user controls without embedding domain logic.
- `models/` defines serialization, validation, and task payload shapes.
- `database/` stores learned job/town data in SQLite with thread-safe access.
- `js/` injects browser-side helpers into the target game environment.
- `config.json` is the default runtime configuration anchor.

Key guiding principles:

- modular design
- thread-safe execution
- asynchronous browser monitoring
- durable persistence
- explicit automation boundaries
- future-proof extensibility

---

## Project Features

- Browser automation with Selenium-backed Chrome control
- Automatic browser reconnect and recovery
- Scheduler with task polling and wake events
- Queue management with ordering, pause/resume, and persistence
- JS injection system for in-game action capture
- Task persistence via JSON config and SQLite learnings
- UI logging and status presentation
- Thread-safe execution using locks and events
- Modern dark-themed PySide6 interface
- Dynamic tabs for queue, game queue, job database, and settings
- Automation engine with retry, cooldown, and failure handling
- Error recovery workflow for stale elements and crashes
- Modular architecture prepared for Playwright migration
- Low-CPU scheduler tick design
- API abstraction layer conceptualized for future expansion

---

## Tech Stack

- Python 3.12+
- Selenium 4.x
- PySide6 GUI framework
- `webdriver-manager` for managed Chrome driver installation
- `colorlog` for enriched console logging
- `threading` for worker threads and synchronization
- `collections.deque` for queue storage
- JSON storage for config and persistent queue state
- SQLite for structured learned record persistence
- Optional future support for:
  - Playwright
  - pydantic data validation
  - cryptography-based secure credential storage

---

## Project Structure

```
westbot_v6/
├── assets/
│   └── themes/
│       └── dark.qss
├── core/
│   ├── browser_manager.py
│   ├── injector_manager.py
│   ├── logger_manager.py
│   ├── network_sniffer.py
│   ├── parser_engine.py
│   ├── queue_manager.py
│   ├── storage_manager.py
│   └── task_executor.py
├── database/
│   └── database_manager.py
├── js/
│   └── injector.js
├── models/
│   ├── job_model.py
│   ├── job_models.py
│   ├── task_models.py
│   └── town_model.py
├── ui/
│   ├── main_window.py
│   └── tabs/
│       ├── game_queue_tab.py
│       ├── jobs_database_tab.py
│       ├── queue_tab.py
│       └── settings_tab.py
├── config.json
├── jobs_database.json
├── main.py
├── requirements.txt
├── spusti.bat
├── westbot_v6.db
├── westbot_v6.log
└── README.md
```

### File Responsibilities

- `main.py`
  - Bootstraps the full application.
  - Instantiates storage, logger, browser manager, queue manager, network sniffer, task executor, database manager, injector manager, and UI.
  - Starts background services and application event loop.

- `config.json`
  - Default runtime configuration.
  - Stores browser, scheduler, logging, UI, credentials, database, and persisted queue settings.

- `requirements.txt`
  - Defines Python dependencies required by the project.

- `assets/themes/dark.qss`
  - Provides the dark UI stylesheet for PySide6.
  - Controls widget look and feel across the interface.

- `core/browser_manager.py`
  - Controls Selenium Chrome lifecycle.
  - Manages CDP connections, performance log access, and JS injection monitoring.
  - Handles login, navigation, and browser recovery.
  - Emits listeners on browser state changes.

- `core/injector_manager.py`
  - Loads `js/injector.js`.
  - Injects browser-side controls into the game environment.
  - Reads and consumes job event payloads from `window.localStorage`.

- `core/logger_manager.py`
  - Builds the central logger.
  - Configures console and rotating file handlers.
  - Supports colored output when available.

- `core/network_sniffer.py`
  - Reads browser performance logs.
  - Detects network requests related to tasks.
  - Creates or updates learned job/town records.
  - Syncs discovery with SQLite persistence.

- `core/parser_engine.py`
  - Parses request and response payloads from browser traffic.
  - Normalizes `window=task&action=add` flows.
  - Extracts job and town metadata for learned automation.

- `core/queue_manager.py`
  - Maintains an in-memory task queue.
  - Applies thread-safe access using `RLock`.
  - Provides listener notifications for UI and automation.

- `core/storage_manager.py`
  - Loads and saves configuration atomically.
  - Persists queue state and learned JSON artifacts.
  - Provides credentials and database path utilities.

- `core/task_executor.py`
  - Houses the automation thread.
  - Dispatches tasks from queue to browser actions.
  - Applies retry, cooldown, and task lifecycle state updates.
  - Communicates with browser and injection subsystems.

- `database/database_manager.py`
  - Manages SQLite schema for learned jobs and towns.
  - Performs upsert operations for captured records.
  - Notifies listeners on data changes.

- `js/injector.js`
  - Runs inside the browser page.
  - Detects job windows using MutationObserver.
  - Injects START and ADD buttons.
  - Stores selected actions in `localStorage`.

- `models/task_models.py`
  - Defines `TaskModel`, `TaskStatus`, and `TaskType`.
  - Implements serialization and deserialization.
  - Provides immutable metadata and lifecycle state.

- `models/job_model.py`
  - Defines the runtime job record object.
  - Converts database rows into structured records.

- `models/job_models.py`
  - Defines a job definition payload shape.
  - Supports dictionary mapping to JSON compatible forms.

- `models/town_model.py`
  - Defines the learned town movement record.
  - Stores travel metadata and walk-time estimates.

- `ui/main_window.py`
  - Orchestrates the main PySide6 application window.
  - Builds topbar login controls, tab navigation, and status bar.
  - Delegates refresh and persistence to tabs and core services.

- `ui/tabs/queue_tab.py`
  - Displays the current automation queue.
  - Supports remove, pause/resume, and reorder.

- `ui/tabs/game_queue_tab.py`
  - Shows detected server queue tasks.
  - Exposes injected job events for manual enqueueing.

- `ui/tabs/jobs_database_tab.py`
  - Reports learned job and town records.
  - Enables manual capture of visible tasks.
  - Allows queue additions from historical data.

- `ui/tabs/settings_tab.py`
  - Exposes runtime configuration controls.
  - Saves changes to `config.json`.

---

## Core Module Documentation

### `core/browser_manager.py`

**Responsibilities**
- Launches and manages Selenium Chrome sessions.
- Configures CDP for network and page control.
- Injects browser scripts and extracts DOM metadata.
- Supports login automation and navigation.

**Internal Logic**
- Uses `webdriver.ChromeOptions` and `ChromeDriverManager`.
- Enables performance logging and CDP `Network` events.
- Launches a dedicated monitor thread for window and injection state.
- Supports script execution wrappers with robust catch handlers.

**Lifecycle**
- `start()` initializes the browser and monitor.
- `_start_monitor()` runs a background thread.
- `_monitor_loop()` polls the browser every 1.5 seconds.
- `shutdown()` teardown is safe and idempotent.

**Thread Behavior**
- Monitor thread uses `threading.Event` for graceful stopping.
- Browser operations are protected from invalid handle states.
- Notification listeners are invoked safely from the monitor thread.

**Future Scalability**
- Can be refactored into a generic browser adapter interface.
- Supports migration to Playwright or multi-browser/multi-tab orchestration.
- Ideal location for session pooling and remote browser support.

**Interaction Flow**
- `TaskExecutor` calls `execute_script()`, `login()`, `navigate_to()`.
- `NetworkSniffer` reads browser logs and response bodies.
- `InjectorManager` receives reinjection from `BrowserManager`.
- UI components call browser introspection helpers.

---

### `core/queue_manager.py`

**Responsibilities**
- Stores automation tasks.
- Enforces queue capacity and order.
- Provides event notifications for queue changes.

**Internal Logic**
- Uses `collections.deque` for efficient task insertion/removal.
- Uses `threading.RLock` to protect concurrent access.
- Maintains a listener registry for reactive UI updates.

**Lifecycle**
- Loads persisted queue from `config.json` at startup.
- Persists queue every time it mutates.
- Provides task lifecycle transitions: pause, resume, complete, fail.

**Thread Behavior**
- All external methods acquire the lock.
- `wait_for_update()` uses `threading.Event` to wake task execution.

**Future Scalability**
- Can evolve into a distributed queue worker with `queue.Queue` or message bus.
- Could support task sharding, priorities, and weighted queues.

**Interaction Flow**
- `TaskExecutor` consumes tasks via `get_next_task()`.
- UI tabs display queue contents and issue control actions.
- `StorageManager` persists queue state atomically.

---

### `core/scheduler.py` (Conceptual)

**Current Equivalent**
- Core scheduling logic is currently implemented in `core/task_executor.py`.
- The scheduler determines when the automation thread should run and how often.

**Responsibilities**
- Tick-based scheduling.
- Sleep and wake semantics.
- Adapting interval based on load.

**Future Role**
- A dedicated `core/scheduler.py` would centralize interval control, priority promotion, and distributed scheduling.
- It would separate scheduling from execution to support multi-threaded workers.

---

### `core/storage_manager.py`

**Responsibilities**
- Manages configuration lifecycle.
- Persists queue state and learned JSON artifacts.
- Provides secure storage access for credentials and database path.

**Internal Logic**
- Uses atomic temporary file writes to avoid partial config corruption.
- Normalizes missing config fields with fallback dictionaries.
- Keeps `RLock` protection around all read/write file paths.

**Lifecycle**
- Loads config on initialization.
- Writes updates through `save_config()`.
- Initializes default template if config does not exist.

**Thread Behavior**
- All file operations are protected with `RLock`.
- Config reads and writes are safe across UI thread and worker threads.

**Future Scalability**
- Can be extended to use encrypted config storage.
- A migration path exists toward YAML, TOML, or remote configuration services.

**Interaction Flow**
- `QueueManager` loads and saves queue state.
- `TaskExecutor` reads scheduler and browser settings.
- `SettingsTab` writes UI and runtime settings.
- `MainWindow` retrieves saved credentials.

---

### `core/logger_manager.py`

**Responsibilities**
- Builds and configures the logging subsystem.
- Supplies both console and file logging.

**Internal Logic**
- Uses Python `logging` module.
- Supports optional `colorlog` for terminal output.
- Writes rotating logs with 5 MB max size and 5 backups.

**Lifecycle**
- Instantiated once at startup.
- Shared logger is passed into every core and UI component.

**Future Scalability**
- Can be extended to structured JSON logs.
- Supports remote log aggregation, Sentry, or telemetry pipelines.

**Interaction Flow**
- All modules import the same logger instance.
- Error handling and diagnostics are centralized through standard logging APIs.

---

### `core/automation_thread.py` (Conceptual)

**Current Equivalent**
- The automation thread is implemented inside `core/task_executor.py`.

**Responsibilities**
- Drives the automation loop.
- Ensures tasks execute sequentially and safely.
- Applies sleep, retry, and backoff strategies.

**Thread Behavior**
- Runs as daemon thread.
- Uses `threading.Event` for wake/sleep semantics.
- Protects browser interaction from blocking the UI thread.

**Future Role**
- Dedicated module would separate thread orchestration from task execution.
- Supports multiple worker threads and concurrency limits.

---

### `core/state_monitor.py` (Conceptual)

**Responsibilities**
- Tracks browser and application state.
- Detects disconnected, loading, ingame, queue-full, and logout conditions.
- Provides a central state model for recovery and UI.

**Current Behavior**
- `BrowserManager` inspects browser handles and reinjection.
- `TaskExecutor` checks browser availability and queue fullness.

**Future Role**
- A dedicated state monitor would standardize state transition handling.
- It would provide explicit state objects and update signals.

---

### `core/error_recovery.py` (Conceptual)

**Responsibilities**
- Implements retries, reconnects, queue restoration, and crash recovery.
- Handles stale browser elements and timeouts.

**Current Behavior**
- `TaskExecutor` retries failed tasks and marks them appropriately.
- `BrowserManager` auto-recovers when configured.
- `InjectorManager` handles malformed payloads safely.

**Future Role**
- A dedicated recovery module would centralize policy and state healing.
- It could expose pluggable recovery strategies and metrics.

---

### `core/api_layer.py` (Conceptual)

**Responsibilities**
- Defines clean abstraction between UI, core automation, and browser services.
- Provides an interface for future remote access, web APIs, or IPC.

**Current Behavior**
- Interface-like behavior is distributed across `TaskExecutor`, `BrowserManager`, and `DatabaseManager`.

**Future Role**
- `core/api_layer.py` would isolate business logic from surface channels.
- It would enable remote orchestration, web dashboards, and RESTful control.

---

## Model Documentation

### `models/task_models.py`

**Purpose**
- Defines the canonical task domain model for automation.

**Dataclass Usage**
- Uses `@dataclass` for immutable-like semantics with convenience methods.
- Encapsulates task metadata, status, attempts, retry limits, cooldown, and timing fields.

**Serialization**
- `to_dict()` converts task state to JSON-serializable dictionaries.
- `from_dict()` reconstructs tasks from persisted payloads.

**Persistence**
- Tasks are persisted as JSON objects inside `config.json`.
- Persistence supports queue restoration after restart.

**Validation**
- `from_dict()` enforces required fields and casts values safely.
- `TaskType` and `TaskStatus` enums normalize state.

**Queue Compatibility**
- Task objects are designed for queue lifecycle management.
- `remaining`, `repeat_count`, and `status` support scheduling semantics.

---

### `models/app_state_models.py`

**Planned Purpose**
- This file is not present in the current release but is a recommended future location for application state models.
- It should contain definitions for browser session state, UI state snapshots, and queue/state transition objects.

**Recommended Responsibilities**
- store UI and runtime state.
- define disconnected/loading/ingame state enums.
- provide shared state contracts for UI and core.

---

## UI Documentation

### Top Bar

- Username input
- Password input
- Start Browser button
- Login button

These controls allow the operator to initialize the browser session and authenticate into the game.

### Sidebar

- Implemented as a tabbed navigation area using `QTabWidget`.
- Provides access to each functional area without embedding business logic in the view.

### Dynamic Content Area

- Each tab has its own content and refresh contract.
- `MainWindow` manages the main layout and status bar.
- The content area is updated through periodic refresh operations and event-driven callbacks.

### Refresh System

- A `QTimer` triggers UI refresh every 1.2 seconds.
- The timer calls `refresh()` on each tab.
- All refresh logic runs on the main thread to preserve Qt safety.

### Tabs

#### Queue Tab
- Displays queue entries and task metadata.
- Supports remove, pause/resume, and reorder actions.
- Reads directly from `QueueManager`.

#### Game Queue Tab
- Displays detected game queue content from browser script execution.
- Shows injected job actions from the browser environment.
- Allows manual enqueueing of injected job payloads into the automation queue.

#### Jobs Database Tab
- Displays captured jobs and towns from learned automation history.
- Supports search, type filtering, capture, and queue addition.
- Integrates with `DatabaseManager` for persistence.

#### Settings Tab
- Exposes runtime configuration controls.
- Persists changes through `StorageManager`.
- Controls browser, scheduler, logging, and UI settings.

---

## Queue Engine Documentation

### Scheduler Architecture

- The queue engine is a producer/consumer pattern anchored by `QueueManager` and `TaskExecutor`.
- `QueueManager` persists and orders tasks.
- The scheduler logic is driven by a polling interval in `TaskExecutor`.

### Task Lifecycle

- Tasks enter the queue in `PENDING` status.
- `TaskExecutor` transitions tasks to:
  - `RUNNING`
  - `COMPLETED`
  - `FAILED`
  - `PAUSED`
- The system supports multiple attempts and automatic retry semantics.

### Repeat System

- Tasks support `repeat_count` and `remaining`.
- A single task can execute multiple times until `remaining` reaches zero.

### Cooldown System

- Configurable cooldown behavior is available via `cooldown_seconds`.
- Randomized delay backoffs are used to reduce load and mimic human timing.

### Persistence

- Queue state is persisted to `config.json` on every mutation.
- Completed tasks are kept until explicitly cleared.
- The queue restores automatically on restart.

### Priorities

- Tasks include a `priority` field.
- Current implementation does not fully enforce priority-driven scheduling, but the field exists for future scheduler expansion.

### Recovery

- The queue engine supports task failure handling, retries, and status diagnostics.

### Future Distributed Queue Support

- The architecture is designed to migrate to remote queue brokers and worker clusters.
- A dedicated `core/scheduler.py` and `core/api_layer.py` will enable the next phase.

---

## Automation System Documentation

### Automation Thread

- The automation engine runs in a daemon background thread via `TaskExecutor`.
- It does not block the UI thread.
- It is supervised by a stop event and wake event.

### Scheduler Ticks

- The execution loop polls at the configured interval.
- When no task is available, the thread waits on the wake event.
- New tasks or queue changes trigger the wake event.

### Event-Driven Execution

- `QueueManager` emits events when tasks change.
- `TaskExecutor` wakes up immediately when queue state updates.
- This reduces idle CPU consumption.

### Reconnect Handling

- `BrowserManager` detects lost browser handles and can restart the browser.
- `auto_reconnect` is configurable in `config.json`.

### Safe Browser Execution

- Browser actions are guarded with driver presence checks.
- Script execution failures are caught and reported.
- The engine avoids undefined browser state by validating driver availability before each action.

### Low CPU Architecture

- The automation thread uses timed waits instead of busy loops.
- `time.sleep` is scaled by the configured delay multiplier.
- Task execution avoids aggressive polling.

### Anti-Freeze Design

- GUI updates are isolated from the automation thread.
- The UI refreshes through Qt timers on the main event loop.
`
# pythontasker
"# pythontasker" 
