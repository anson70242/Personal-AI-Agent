# 🧠 Agent Service (The Brain)

This directory contains the core logic of the Personal AI Agent. It is a **FastAPI** application that serves as the "Controller" between the user (via Nginx), the memory (PostgreSQL), and the intelligence (vLLM).

## 📂 Project Structure & File Descriptions

The code is organized using a **Modular Architecture** to separate concerns (Database, Logic, API, Validation).

### 1. Core Logic
* **`main.py`**
    * **Role:** The Entry Point.
    * **Functionality:**
        * Initializes the FastAPI app.
        * Defines API Routes (`/chat/completions`, `/sessions`).
        * Manages Application Lifecycle (Startup/Shutdown events).
        * Initializes the Background Scheduler for auto-cleanup.
        * Orchestrates the flow: Request -> DB Save -> History Fetch -> vLLM Call -> Response Save.
    * **Key Tech:** Uses `httpx` for **asynchronous** calls to vLLM to prevent blocking.

* **`crud.py` (Create, Read, Update, Delete)**
    * **Role:** Database Interactions.
    * **Functionality:** Contains all functions that directly touch the database.
        * `get_or_create_session`: Manages conversation IDs.
        * `save_message`: Writes User/AI messages to PostgreSQL.
        * `get_chat_history`: Retrieves past messages for context.
        * `cleanup_expired_sessions`: Deletes old data.

* **`rag.py` (Retrieval-Augmented Generation)**
    * **Role:** Knowledge Retrieval (Placeholder).
    * **Functionality:** Designed to handle vector database connections and document retrieval in the future. Currently empty/reserved.

### 2. Data & Validation
* **`database.py`**
    * **Role:** Database Configuration.
    * **Functionality:**
        * Sets up the SQLAlchemy Engine and Session.
        * Defines **ORM Models** (`DbSession`, `DbMessage`) that map Python classes to SQL tables.

* **`schemas.py`**
    * **Role:** Data Validation (Pydantic).
    * **Functionality:** Defines the expected structure for API requests and responses.
        * Ensures incoming JSON has the correct fields (`role`, `content`, `model`).
        * Prevents bad data from crashing the app.

### 3. Infrastructure
* **`Dockerfile`**
    * **Role:** Container Definition.
    * **Functionality:** Builds a lightweight Python 3.10 environment, installs dependencies, and runs the Uvicorn server.

* **`requirements.txt`**
    * **Role:** Dependency List.
    * **Key Libraries:**
        * `fastapi`, `uvicorn`: Web Server.
        * `sqlalchemy`, `psycopg2-binary`: Database ORM & Driver.
        * `httpx`: Async HTTP client (for vLLM).
        * `apscheduler`: For background cleanup tasks.

---

## ⚙️ Environment Variables

This service relies on the following environment variables (passed via `docker-compose.yml`):

| Variable | Description |
| :--- | :--- |
| `GPU_SERVER_IP` | IP address of the vLLM backend. |
| `LLM_API_KEY` | Secret key for authenticating with vLLM. |
| `POSTGRES_USER` | Database username. |
| `POSTGRES_PASSWORD` | Database password. |
| `POSTGRES_DB` | Database name (e.g., `agent_memory`). |
| `POSTGRES_HOST` | Hostname of the DB service (usually `db`). |

---

## 🚀 How to Run (via Docker)

This service is meant to be run as part of the Docker Compose stack.

**Rebuild and Start:**
```bash
# From the project root
docker-compose up --build -d agent_service
```

**Check Logs:**
```bash
docker-compose logs -f agent_service
```