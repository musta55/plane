# Plane — Student Setup Guide

This guide gets Plane running on your machine for local development. When you're done you'll have:

- **Backend** (Django API + Celery workers + Postgres/Redis/RabbitMQ/MinIO) running in **Docker**
- **Frontend** (web + admin apps) running natively with **pnpm**
- The app at **http://localhost:3000**, pre-loaded with a demo workspace you can log into

Plan for **~30–45 minutes** the first time (most of it is Docker image builds and dependency installs that only happen once).

The commands are the **same on macOS and Windows** unless a step is explicitly marked **macOS** or **Windows**.

---

## 1. Prerequisites

Install these first. Versions below are the minimums we've verified.

| Tool               | Min version                                          | Check with                                      |
| ------------------ | ---------------------------------------------------- | ----------------------------------------------- |
| **Docker Desktop** | 4.x (Compose v2)                                     | `docker --version` and `docker compose version` |
| **Node.js**        | **22.18.0** or newer (22 LTS or 24 both fine)        | `node --version`                                |
| **pnpm**           | 11.3.0 — **managed for you**, don't install globally | `pnpm --version`                                |
| **Git**            | any recent                                           | `git --version`                                 |

### Installing on macOS

- **Docker Desktop:** download from docker.com, or `brew install --cask docker`. Then **open Docker Desktop from Applications** so the engine starts.
- **Node.js:** `brew install node` (or use `nvm`), or download the macOS installer from nodejs.org.
- **Git:** already present on most Macs; otherwise `brew install git` or run `xcode-select --install`.
- Use the built-in **Terminal** (zsh) for every command below — no extra shell needed.

### Installing on Windows

- **Docker Desktop:** install it with the **WSL2 backend** (the installer sets this up; it may require enabling WSL2 and a reboot). Then launch Docker Desktop.
- **Node.js:** download the Windows installer from nodejs.org (or `winget install OpenJS.NodeJS.LTS`).
- **Git:** install **Git for Windows** — it includes **Git Bash**, which you'll use to run `setup.sh`.

### Both platforms

**Give Docker enough memory:** Docker Desktop → **Settings → Resources** → **≥ 4 GB RAM** (6–8 GB is smoother).

**Enable Corepack once** (ships with Node; it provides the correct pinned pnpm automatically):

```bash
corepack enable
```

> **Windows:** if `corepack enable` prints an `EPERM` permission error, run it once from an **Administrator** terminal — or just ignore it; pnpm still resolves the pinned version and everything below works.

**Confirm Docker is running** (whale icon steady in the menu bar / tray) before the backend steps:

```bash
docker info
```

---

## 2. Get the code

Clone the course fork (your instructor will give you the URL), then `cd` into it.

```bash
git clone <course-fork-url> plane
cd plane
```

## 3. One-time setup (environment files + dependencies)

Run the setup script from the repo root:

- **macOS:** in Terminal — `./setup.sh`
- **Windows:** in **Git Bash** — `bash setup.sh`

This does three things:

1. Copies `.env.example` → `.env` for the root and each app (`web`, `api`, `space`, `admin`, `live`).
2. Generates a Django `SECRET_KEY` into `apps/api/.env`.
3. Runs `pnpm install` (installs all frontend dependencies — this is the slow part, a few minutes).

You should see `Environment setup completed successfully!` at the end. The `.env` files are git-ignored and safe to keep local.

---

## 4. Start the backend (Docker)

From the repo root:

```bash
docker compose -f docker-compose-local.yml up -d --build
```

- **First run** builds the API image and downloads Postgres/Redis/RabbitMQ/MinIO — expect several minutes.
- A one-shot **migrator** container applies all database migrations, then the **api** container starts and registers the instance.

**Wait for the API to be ready**, then verify (should print `HTTP 200`):

```bash
curl -s -o /dev/null -w "API: HTTP %{http_code}\n" http://localhost:8000/api/instances/
```

If it returns `000` / connection-refused for the first minute or two, the migrator is still running — wait and retry. Watch progress with:

```bash
docker compose -f docker-compose-local.yml logs -f api
```

(`Ctrl-C` to stop watching; the containers keep running.)

---

## 5. Start the frontend (pnpm)

In a **second terminal**, from the repo root:

```bash
pnpm dev
```

Wait until it prints something like `web:dev  Local: http://localhost:3000`. This runs the dev servers with hot-reload:

| App              | URL                             | What it is                                                                         |
| ---------------- | ------------------------------- | ---------------------------------------------------------------------------------- |
| **Web**          | **http://localhost:3000**       | The Plane product — **this is where you work.**                                    |
| Admin (God-mode) | http://localhost:3001/god-mode/ | Instance administration only (auth config, feature flags). Not for day-to-day use. |

Leave `pnpm dev` running while you develop.

---

## 6. Create an account & log in

Open **http://localhost:3000** — the web app (**not** 3001). A fresh install starts with an **empty database**, so choose one of these:

### Option A — seed a ready-to-use demo account (recommended)

This creates a login **and** a workspace already populated with issues, cycles, modules, and pages, so you can explore the full app right away. From the repo root, with the backend running (see step 7 for details):

```bash
docker compose -f docker-compose-local.yml exec -T api \
  python manage.py shell --settings=plane.settings.local < seed_demo.py
```

Then log in at **http://localhost:3000** with:

- **Email:** `demo@plane.local`
- **Password:** `Demo12345!`

### Option B — sign up your own account

On http://localhost:3000, register any email + password. You'll start with an **empty** workspace and create your own projects.

> **Note:** there's **no mail server configured**, so verification emails, magic links, and workspace invites won't be delivered — which is exactly why Option A (the seeded account) exists.

---

## 7. Seed / reset the demo data

The seed script at the repo root creates the `demo` account and one fully-populated project (and re-running it **resets** that data). With the backend running, from the repo root:

```bash
docker compose -f docker-compose-local.yml exec -T api \
  python manage.py shell --settings=plane.settings.local < seed_demo.py
```

Edit `seed_demo.py` to change the email/password or how much sample data it creates.

---

## 8. Run the tests

The Django/pytest suite runs in its own isolated Docker stack. From the repo root:

```bash
# full suite
docker compose -f docker-compose-test.yml up --build --abort-on-container-exit --exit-code-from api-tests

# just the fast unit tests
docker compose -f docker-compose-test.yml run --rm api-tests pytest -m unit

# tear down the test stack when done
docker compose -f docker-compose-test.yml down -v
```

The expected baseline is **all tests passing**. See `apps/api/tests/RUNNING_TESTS.md` for details.

---

## 9. Stop / reset

```bash
# stop the frontend: Ctrl-C in the `pnpm dev` terminal

# stop the backend (keeps your database and seeded data):
docker compose -f docker-compose-local.yml down

# stop the backend AND wipe the database (start fresh; re-run steps 4 + 7 after):
docker compose -f docker-compose-local.yml down -v
```

To resume later, just re-run steps 4 and 5 (no `--build` needed unless dependencies changed).

---

## Troubleshooting

**I only see a "create account" button / signup fails — I'm on port 3001.**
That's the God-mode admin panel, not the product. Use **http://localhost:3000** and log in with the demo credentials above. (You _can_ sign into 3001 with the same demo account — it's an instance admin — but you rarely need to.)

**The API never comes up / logs are stuck on "Waiting for database migrations to complete…".**
The migrator failed. Check `docker compose -f docker-compose-local.yml logs migrator`, then restart cleanly:

```bash
docker compose -f docker-compose-local.yml down
docker compose -f docker-compose-local.yml up -d
```

**`pnpm dev` crashes on Windows** with an `EPERM` rename, `ERR_PNPM_ABORTED_REMOVE_MODULES_DIR_NO_TTY`, or exit code `3221226505`.
This is pnpm's pre-run dependency check colliding with itself under Windows. The fork sets `verifyDepsBeforeRun: false` in `pnpm-workspace.yaml` to prevent it — confirm that line is present, then re-run `pnpm dev`. One-off workaround: `CI=true pnpm dev`. (This is rarely hit on macOS.)

**File uploads / profile avatars fail** with a MinIO/S3 connection error.
Local file storage points at MinIO. If uploads don't work, set `AWS_S3_ENDPOINT_URL=http://plane-minio:9000` in `apps/api/.env`, then `docker compose -f docker-compose-local.yml restart api`. Core features (issues, cycles, modules, pages) work regardless.

**"Port is already in use" (3000, 3001, 8000, 5432, …).**
Another program (or a previous run) holds the port. Stop it, or stop a stale stack with `docker compose -f docker-compose-local.yml down`. On macOS you can find the culprit with `lsof -i :3000`.

**macOS: `docker: command not found` after installing Docker Desktop.**
Open the **Docker Desktop app** at least once (it installs the CLI and starts the engine), then open a new Terminal window.

**macOS (Apple Silicon): an image fails with an architecture/`exec format` error.**
Enable Docker Desktop → **Settings → General → "Use Rosetta for x86/amd64 emulation"**, then re-run the compose command.

**Windows: build scripts fail with weird path errors.**
Your clone path probably contains a space or apostrophe. Move the repo to a clean path like `C:\dev\plane` and re-run `bash setup.sh`.

---

## Command cheat-sheet

```bash
./setup.sh          # macOS  (Windows: bash setup.sh)   one-time: env files + deps
docker compose -f docker-compose-local.yml up -d --build   # start backend
pnpm dev                                                   # start frontend (web :3000, admin :3001)
docker compose -f docker-compose-local.yml logs -f api     # watch API logs
docker compose -f docker-compose-test.yml up --build --abort-on-container-exit --exit-code-from api-tests  # tests
docker compose -f docker-compose-local.yml down            # stop backend (keep data)
```

Login: **http://localhost:3000** → `demo@plane.local` / `Demo12345!`
