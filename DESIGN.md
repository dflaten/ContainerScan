# ContainerScan

A self-hosted, locally-run web service for managing QR codes linked to physical containers. Scan a QR code with any phone camera and instantly view the container's contents in a browser — no app required.

---

## Table of Contents

- [Overview](#overview)
- [Development vs Deployment Scope](#development-vs-deployment-scope)
- [Goals & Non-Goals](#goals--non-goals)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Data Model](#data-model)
- [API Endpoints](#api-endpoints)
- [User Stories](#user-stories)
- [User Flows](#user-flows)
- [QR Code Content](#qr-code-content)
- [Frontend Views](#frontend-views)
- [Docker Compose Layout](#docker-compose-layout)
- [Project Structure](#project-structure)
- [Print Layout](#print-layout)
- [Implementation Phases](#implementation-phases)
- [Build Task List](#build-task-list)
- [Assumptions & Constraints](#assumptions--constraints)

---

## Overview

**ContainerScan** lets you:

- Generate and print QR codes before a container is fully documented
- Each container is assigned a unique **4-character container code** displayed prominently on its label
- Upload and associate images with each container
- Write and update rich descriptions per container
- Assign containers to rooms for location tracking
- Apply colour labels that render as a background behind printed QR codes
- Search across all containers by name, description, room, label, or container code
- Search by what is inside a container and recover its 4-character container code quickly
- Scan a QR code with any device and view the container's contents via a mobile browser
- Run everything locally on your LAN — no internet access required

ContainerScan is intentionally LAN-only in its initial version: the frontend, API, and scan views are reachable only from the local network and are not intended to be exposed to the public internet.

---

## Development vs Deployment Scope

This design document covers both the long-term target architecture and the current implementation plan, but those are not the same thing operationally.

- The current working phase is **development-focused**. Commands, scripts, and tooling added early in the project are allowed to optimize for local developer productivity, fast iteration, and testing.
- Early project commands may assume a developer machine, a checked-out repository, and direct use of Docker Compose, `uv`, npm, or Make targets.
- The final **server/runtime workflow** is a separate concern and is intentionally deferred until the application features and deployment requirements are stable enough to justify hardening.
- Production-style startup commands, service management, backup procedures, host setup steps, and repeatable LAN deployment instructions will be defined later as part of deployment-focused work, especially task `21` (**LAN Deployment Documentation**).
- Until that later phase is complete, development commands should not be treated as the final operational contract for running ContainerScan on its target server.

---

## Goals & Non-Goals

| | Detail |
|---|---|
| ✅ Goal | Create and manage QR codes for physical containers |
| ✅ Goal | Auto-generate a unique 4-character container code per container for quick identification |
| ✅ Goal | Upload and update images per container |
| ✅ Goal | Editable description field per container |
| ✅ Goal | Assign containers to rooms |
| ✅ Goal | Apply colour labels (rendered behind QR codes on print) |
| ✅ Goal | Full-text search across containers including by container code |
| ✅ Goal | Search by contents and retrieve the container's 4-character code from results |
| ✅ Goal | Print-ready QR code output |
| ✅ Goal | Mobile browser scanning (no native app needed) |
| ✅ Goal | Fully local, LAN-only access |
| ❌ Non-Goal | Internet or cloud access |
| ❌ Non-Goal | User authentication (single-user local tool) |
| ❌ Non-Goal | Video or barcode support |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Ubuntu Host Machine                │
│                                                     │
│  ┌──────────────────────────────────────────────┐   │
│  │              Docker Compose Stack            │   │
│  │                                              │   │
│  │  ┌─────────────┐      ┌──────────────────┐  │   │
│  │  │  FastAPI     │      │   PostgreSQL      │  │   │
│  │  │  Backend     │◄────►│   Database        │  │   │
│  │  │  :8000       │      │   :5432           │  │   │
│  │  └──────┬──────┘      └──────────────────┘  │   │
│  │         │                                    │   │
│  │  ┌─────────────┐      ┌──────────────────┐  │   │
│  │  │  SvelteKit   │      │  /images volume  │  │   │
│  │  │  Frontend    │      │  (local storage) │  │   │
│  │  │  via Nginx   │      └──────────────────┘  │   │
│  │  └──────┬──────┘                             │   │
│  │         │                                    │   │
│  │  ┌──────▼──────┐                             │   │
│  │  │    Nginx     │                             │   │
│  │  │     :80      │                             │   │
│  │  └─────────────┘                             │   │
│  └──────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
         ▲                        ▲
         │ Admin browser          │ Phone browser (QR scan)
         │ (manage containers)    │ (view container contents)
```

> **No native iOS app is needed.** The phone camera scans the QR code and opens a mobile-optimised page in Safari or Chrome directly.

---

## Tech Stack

| Layer | Technology | Reason |
|---|---|---|
| Backend | Python / FastAPI + uv | Lightweight API stack with modern Python dependency management |
| Frontend | SvelteKit + Skeleton UI | File-based routing, strong defaults for admin + scan views, fast path to a polished UI |
| Database | PostgreSQL | Full-text search support via `tsvector`, structured metadata |
| Image storage | Docker volume (local filesystem) | Simple, no cloud dependency |
| QR generation | `qrcode` Python library | Mature, print-quality output with colour and text rendering |
| Containerisation | Docker + Docker Compose | Clean deployment on Ubuntu |
| Reverse proxy | Nginx | Expose a single stable LAN origin for frontend, scan pages, and API |

---

## Data Model

### `rooms`

| Column | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Unique room identifier |
| `name` | VARCHAR | Room name (e.g. "Garage", "Attic", "Spare Bedroom") |
| `created_at` | TIMESTAMP | Creation date |

### `labels`

| Column | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Unique label identifier |
| `name` | VARCHAR | Label name (e.g. "Tools", "Seasonal", "Fragile") |
| `colour` | VARCHAR | Hex colour code (e.g. `#FF5733`) |
| `created_at` | TIMESTAMP | Creation date |

### `containers`

| Column | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Unique container identifier |
| `code` | CHAR(5) | Auto-generated unique 4-character container code with a middle dash (e.g. `KX-B7`), immutable after creation |
| `name` | VARCHAR | Human-readable label; defaults to a generated placeholder such as `Container KX-B7` until edited |
| `description` | TEXT | Editable free-text description of contents |
| `room_id` | UUID (FK) | Optional assigned room → `rooms.id` |
| `label_id` | UUID (FK) | Optional assigned colour label → `labels.id` |
| `created_at` | TIMESTAMP | Creation date |
| `updated_at` | TIMESTAMP | Last updated date |
| `search_vector` | TSVECTOR | PostgreSQL full-text search index (name + description + code) |

> The `code` column is a unique, auto-generated 4-character uppercase alphanumeric code with a dash in the middle (for example `KX-B7`) assigned at container creation. It is indexed for fast lookup, included in search, and remains stable for the life of the container so printed labels do not become misleading.

> Container creation is intentionally **label-first**: the system must be able to create a container record with only a generated code and placeholder name so the QR label can be printed before the user has packed the box or recorded its contents.

### `images`

| Column | Type | Description |
|---|---|---|
| `id` | UUID (PK) | Unique image identifier |
| `container_id` | UUID (FK) | Links to `containers` |
| `filename` | VARCHAR | Stored filename on disk |
| `uploaded_at` | TIMESTAMP | Upload date |
| `is_primary` | BOOLEAN | Marks the main exterior/storage-location photo for the container |
| `caption` | VARCHAR | Optional image caption |
| `sort_order` | INTEGER | Display order within the container |

> The first image associated with a container is intended to be the **primary exterior photo**: a picture of the outside of the container showing where it is physically stored. Additional images are intended to capture the contents inside the container.

> The UI should make this explicit during container creation and image management so users understand that the first uploaded image is for the container exterior/storage location, while later images can document contents.

> **Full-text search** is implemented using PostgreSQL's `tsvector` column on `containers`, updated via a trigger on `INSERT` and `UPDATE`. This enables fast search across container names, descriptions, and codes without a separate search engine.

> In user-facing flows, the 4-character `code` is the practical identifier people use to locate and recognize a container. Users must be able to search either by that code directly or by the contents of the container and recover the code from the search results.

---

## API Endpoints

### Room Management

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/rooms` | List all rooms |
| `POST` | `/api/rooms` | Create a new room |
| `PUT` | `/api/rooms/{id}` | Rename a room |
| `DELETE` | `/api/rooms/{id}` | Delete a room |

### Label Management

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/labels` | List all labels |
| `POST` | `/api/labels` | Create a new label (name + hex colour) |
| `PUT` | `/api/labels/{id}` | Update label name or colour |
| `DELETE` | `/api/labels/{id}` | Delete a label |

### Container Management

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/containers` | List all containers (supports `?search=`, `?room_id=`, `?label_id=`, `?code=`) |
| `POST` | `/api/containers` | Create a new container (code auto-generated) |
| `GET` | `/api/containers/{id}` | Get container details + images |
| `GET` | `/api/containers/code/{code}` | Look up a container directly by container code |
| `PUT` | `/api/containers/{id}` | Update name, description, room, or label |
| `DELETE` | `/api/containers/{id}` | Delete container and its images |

### Image Management

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/containers/{id}/images` | Upload image(s) to a container |
| `PUT` | `/api/images/{id}` | Update caption or sort order |
| `DELETE` | `/api/images/{id}` | Remove a specific image |

### QR Code

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/containers/{id}/qr` | Download print-ready QR PNG (with label colour background and container code header) |
| `GET` | `/scan/{id}` | Public scan landing page (mobile-optimised) |

> Search is handled through `GET /api/containers` with `search`, `room_id`, `label_id`, and `code` query parameters. A separate `/api/search` endpoint is not required.

---

## User Stories

1. As a homeowner, I want to generate a container code and QR label before I have packed the box so that I can label physical containers first.
2. As a homeowner, I want newly generated labels to appear in the system immediately so that I can come back later and finish documenting them.
3. As a homeowner, I want to assign a container to a room so that I know where it is stored.
4. As a homeowner, I want to apply a colour label to a container so that related containers are easier to recognise at a glance.
5. As a homeowner, I want to write and edit a description for a container so that I can record what is inside without opening it.
6. As a homeowner, I want to upload multiple photos for a container so that I can visually confirm its contents from my phone or desktop browser.
7. As a homeowner, I want to reorder and caption container images so that the most useful photos appear first and have context.
8. As a homeowner, I want to search containers by keyword or container code so that I can find a specific box quickly.
9. As a homeowner, I want to search by what is inside a container and see the container's 4-character code in the results so that I can identify the right box without scanning it first.
10. As a homeowner, I want to filter containers by room or colour label so that I can narrow down large lists efficiently.
11. As a homeowner, I want to open a container detail page and edit its metadata so that the system stays accurate over time.
12. As a homeowner, I want to download a print-ready QR label for a container so that I can attach it to the physical box.
13. As a homeowner, I want to print multiple QR labels on a single sheet so that label creation is efficient.
14. As a person scanning a container, I want a QR code to open a mobile-friendly page on my local network so that I can inspect the container without installing an app.
15. As a person scanning a container, I want to see the container code, name, room, description, and images immediately so that I can confirm I have the right container.
16. As the system owner, I want the application to stay local-network-only so that my data is not exposed to the public internet.

---

## User Flows

### Creating a Container

1. Open the admin UI at `http://containerscan.local` (or another LAN hostname mapped to the server)
2. Click **Generate Label**
3. Optionally enter a quick name, room, or colour label if those details are already known
4. Click **Generate Container Label** — a unique container code is automatically assigned and stored immediately
5. Open the new container detail view and click **Download QR Label**
6. Print and attach the label to the physical container

### Filling in a Container Later

1. After the box is packed, open the container from the dashboard or scan its QR code
2. Update the name if needed and add the description of what is inside
3. Assign the room and colour label if they were not known earlier
4. Upload the exterior/storage-location photo first
5. Upload any additional contents photos after that
6. Save changes — the QR code URL and container code remain unchanged

### Printing a QR Code

1. Open a container from the admin list
2. Click **Download QR Code** → saves a PNG with:
   - The container code displayed at the top in large bold text
   - The label colour as the tile background
   - The container name and room printed below the QR code
3. Print and attach to the physical container

### Updating a Container

1. Open a container from the admin list or search results
2. Edit the description, swap the room or label, add/remove/reorder images
3. Click **Save** — the QR code URL and container code remain unchanged; no reprinting needed

### Searching for Items

1. Use the search bar at the top of the admin UI
2. Type any keyword describing what is in the container, or type the 4-character container code directly
3. Optionally filter results by **room** or **colour label** using the sidebar filters
4. Review the matching results, each of which shows the container's 4-character code prominently
5. Click a result to open the container detail page

### Scanning a QR Code

1. Point your phone camera at the QR code on the container
2. Phone opens `http://containerscan.local/scan/{container-id}`
3. Browser displays:
   - Container code and container name (with label colour as a header background)
   - Room location
   - Description
   - Full-resolution scrollable image gallery

---

## QR Code Content

Each QR code encodes a local URL:

```
http://containerscan.local/scan/{container-uuid}
```

### QR Label Layout

Each printed QR label is rendered as a tile with three visual layers:

```
┌─────────────────────┐
│       KX-B7         │  ← container code (large, bold, centred)
├─────────────────────┤
│                     │
│     [QR CODE]       │  ← QR code module
│                     │
├─────────────────────┤
│   Garage Box 3      │  ← Container name
│   📍 Garage         │  ← Room name
└─────────────────────┘
        ████           ← Label colour background behind entire tile
```

- The **container code** appears at the top of every label in large bold text
- The **label colour** fills the entire tile background
- The **container name** and **room** appear below the QR code
- The code allows quick verbal or visual identification without scanning (e.g. "which box is this?" → "it's KX-B7")

> **Important:** Use a stable LAN hostname for QR generation, such as `containerscan.local`, backed by a DHCP reservation or static lease on your router. Printed QR codes should point at a stable origin, not a development port.

---

## Frontend Views

### Admin View (`/`)

- Primary CTA focused on generating labels before boxes are fully documented
- Search bar (real-time full-text search including container code)
- Filter sidebar: filter by room, filter by colour label
- Separate emphasis for containers that still need details after label generation
- Container grid/list with thumbnail preview, 4-letter code badge, room badge, and colour label indicator
- Search results must surface the 4-character container code clearly so users can identify a box from its contents without opening it
- Create, edit, and delete containers
- Inline room and label management
- Built with Skeleton primitives and themed to favour legibility on desktop while remaining touch-friendly on tablets

### Container Detail / Edit View (`/containers/{id}`)

- Container code displayed prominently (read-only)
- Download QR label action kept visible near the top of the screen
- Editable name field
- Editable description (multi-line text area)
- Room selector dropdown, optional until the user knows the storage location
- Colour label selector (colour swatches), optional until chosen
- Image upload and reordering
- The first image slot should be clearly labeled as the primary exterior/storage-location photo
- Additional image slots should be presented as contents photos
- Individual image delete and caption edit
- Clear guidance for newly generated containers that have not been documented yet

### Scan View (`/scan/{id}`)

- Mobile-first, minimal UI
- Header bar filled with the container's label colour
- Container code and container name displayed prominently
- Room location badge
- Description text
- Swipeable image gallery
- No navigation to admin functions
- Server-rendered first load so a phone scan works cleanly even on slower local devices

### Print Sheet View (`/print`)

- Select multiple containers to include
- Renders QR codes in a grid (e.g. 4×2 per A4 page)
- Each tile shows the container code at the top, QR code in the middle, name and room at the bottom
- Each tile background filled with the container's assigned label colour
- Uses `window.print()` with a print-specific CSS stylesheet to hide all UI chrome

---

## Docker Compose Layout

```yaml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: containerscan
      POSTGRES_USER: cs_user
      POSTGRES_PASSWORD: cs_pass
    volumes:
      - db_data:/var/lib/postgresql/data

  backend:
    build: ./backend
    environment:
      DATABASE_URL: postgresql://cs_user:cs_pass@db:5432/containerscan
      IMAGE_STORAGE_PATH: /app/images
      PUBLIC_BASE_URL: http://containerscan.local
    volumes:
      - image_data:/app/images
    depends_on:
      - db

  frontend:
    build: ./frontend
    environment:
      ORIGIN: http://containerscan.local
      INTERNAL_API_URL: http://backend:8000

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./deploy/nginx.conf:/etc/nginx/conf.d/default.conf:ro
    depends_on:
      - frontend
      - backend

volumes:
  db_data:
  image_data:
```

---

## Project Structure

The tree below represents the intended project layout. As of `2026-05-06`, the repository includes the scaffold, backend foundation files, shared schemas, reference-data routers, QR and scan support, and the first set of admin frontend routes including the dashboard, container creation flow, and container detail/edit screen.

```
containerscan/
├── docker-compose.yml
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── main.py                  # FastAPI app entry point
│   ├── models.py                # SQLAlchemy models
│   ├── schemas.py               # Pydantic schemas
│   ├── routers/
│   │   ├── containers.py
│   │   ├── images.py
│   │   ├── rooms.py
│   │   ├── labels.py
│   │   └── qr.py
│   ├── services/
│   │   └── search.py            # shared search/filter query logic used by container listing
│   └── utils/
│       ├── qr_generator.py      # qrcode lib wrapper — renders label tile with colour
│       │                        # background, 4-letter code header, name and room footer
│       └── code_generator.py    # generates and validates unique dashed container codes (CHAR(5),
│                                # uppercase alpha, collision-checked against DB)
├── frontend/
    ├── Dockerfile
    ├── package.json
    ├── src/
    │   ├── app.html
    │   ├── lib/
    │   │   ├── api/
    │   │   ├── components/
    │   │   └── stores/
    │   ├── routes/
    │   │   ├── +layout.svelte
    │   │   ├── +page.svelte              # Admin dashboard
    │   │   ├── containers/
    │   │   │   └── [id]/
    │   │   │       ├── +page.server.ts
    │   │   │       └── +page.svelte
    │   │   ├── print/
    │   │   │   └── +page.svelte
    │   │   └── scan/
    │   │       └── [id]/
    │   │           ├── +page.server.ts
    │   │           └── +page.svelte
    │   └── app.css
    └── svelte.config.js
└── deploy/
    └── nginx.conf
```

---

## Print Layout

The **Print Sheet** view:

- Renders multiple QR codes in a grid (e.g. 4×2 per A4 page)
- Each tile displays the **container code** at the top in large bold text
- Fills the background of each QR code tile with the container's assigned label colour
- Prints the container name and room below each QR code
- Uses `window.print()` with a print-specific CSS stylesheet to hide all UI chrome
- Colour backgrounds and container codes aid quick visual identification when scanning a shelf of containers

---

## Implementation Phases

### Current Progress Snapshot

As of `2026-05-06`, the repository has completed the backend foundation, QR and scan support, the frontend bootstrap, the admin dashboard, and the first container-management screens:

- Build task `1` is complete: repository scaffold, Docker Compose, Dockerfiles, and Nginx config exist.
- Build task `2` is complete: FastAPI app bootstrap, config loading, database session wiring, and `/api/health` are in place.
- Build task `3` is complete: SQLAlchemy models, Alembic setup, initial migration, constraints, indexes, and `search_vector` triggers exist.
- Build task `4` is complete: unique dashed container code generation utility and tests for format and collision handling are implemented.
- Build task `5` is complete: room CRUD API routes, shared schemas, validation, and backend tests are implemented.
- Build task `6` is complete: label CRUD API routes, hex-colour validation, and backend tests are implemented.
- Build task `7` is complete: container create, list, detail, update, delete, and code-lookup routes are implemented with room/label validation and backend tests.
- Build task `8` is complete: `GET /api/containers` now supports combined `search`, `room_id`, `label_id`, and `code` filters with backend tests.
- Build task `9` is complete: image upload, storage, serving, primary-image semantics, and image-metadata update/delete operations are implemented.
- Build task `10` is complete: QR rendering and print-ready label PNG generation are implemented.
- Build task `11` is complete: the backend serves the read-only scan data path and mobile scan page.
- Build task `12` is complete: the SvelteKit frontend bootstrap, shared API helpers, layout shell, and global theme foundation are in place.
- Build task `13` is complete: the admin dashboard supports live container listing, search, room/label filters, and empty/error/loading states.
- Build task `14` is complete: the create-container flow supports room/label selection, optional initial image upload, and dashboard refresh after creation.
- Build task `15` is complete: the container detail screen supports metadata editing, QR download access, and image upload/update/delete management.
- Development support is improved with a repeatable seed script and a follow-up migration that upgrades older four-character container codes to the current dashed five-character format.

| Phase | Deliverable |
|---|---|
| 1 | Docker Compose stack + PostgreSQL schema (including `rooms`, `labels`, `tsvector`, unique immutable `code` column) + FastAPI skeleton |
| 2 | Room and label CRUD API |
| 3 | Container CRUD API + unique container code generation on create |
| 4 | QR code generation with colour background and container code header |
| 5 | Image upload, storage, reordering, and serving |
| 6 | Full-text search via `GET /api/containers` (including code field) with room and label filters |
| 7 | SvelteKit + Skeleton admin UI (create, edit, search, filter, download QR) |
| 8 | Mobile scan view (`/scan/{id}`) with label colour header and code displayed |
| 9 | Print sheet layout with colour backgrounds and code headers |
| 10 | Polish: drag-and-drop upload, inline room/label creation, delete confirmation, print styling |

---

## Build Task List

### Recommended Build Order

Use the task list in this order to minimize blocked work and rework.

| Order | Task | Depends On | Effort | Why It Comes Here |
|---|---|---|---|---|
| 1 | Repository and Compose Scaffold | None | S | Establishes the runnable project and service boundaries. |
| 2 | FastAPI App Bootstrap | 1 | S | Gives the backend a usable entry point before feature work starts. |
| 3 | Database Schema and Migration Setup | 1, 2 | M | Defines the persistent model that almost all later tasks rely on. |
| 4 | Unique Container Code Generation | 3 | S | Locks in code rules early because QR and search depend on them. |
| 5 | Room CRUD API | 2, 3 | S | Low-risk reference data that unblocks container forms. |
| 6 | Label CRUD API | 2, 3 | S | Another reference-data slice needed for container creation and print styling. |
| 7 | Container CRUD API | 2, 3, 4, 5, 6 | M | Core system behavior and the base for almost every frontend route. |
| 8 | Search and Filtering | 3, 7 | M | Extends container listing once basic CRUD exists. |
| 9 | Image Upload and Storage | 2, 3, 7 | M | Adds file handling after the core entity lifecycle is stable. |
| 10 | QR Code Rendering | 4, 7 | M | Depends on stable IDs and codes, but can be built before the frontend. |
| 11 | Public Scan View Data Path | 7, 9, 10 | S | Validates the read-only QR destination before UI polish. |
| 12 | SvelteKit Frontend Bootstrap | 1 | S | Can start earlier, but is most useful once backend contracts are clearer. |
| 13 | Admin Dashboard UI | 7, 8, 12 | M | Needs stable listing/search APIs to avoid churn. |
| 14 | Create Container Flow | 5, 6, 7, 12 | M | Depends on reference-data endpoints and container create behavior. |
| 15 | Container Detail and Edit UI | 5, 6, 7, 9, 10, 12 | M | Needs most backend features in place to be worth implementing. |
| 16 | Mobile Scan View UI | 11, 12 | S | Thin read-only UI once the scan data path is working. |
| 17 | Print Sheet UI | 7, 10, 12 | M | Depends on QR output and container selection data. |
| 18 | Nginx Reverse Proxy Configuration | 1, 2, 12 | S | Best done once both apps can run, before end-to-end LAN testing. |
| 19 | File Cleanup and Delete Semantics | 7, 9 | S | Important integrity work after the first happy path exists. |
| 20 | Testing and Verification | 4 through 19 | M | Broad verification is most efficient once the main slices exist. |
| 21 | LAN Deployment Documentation | 1 through 20 | S | Finalizes the system for repeatable local deployment. |

Effort guide:

- `S`: a small task, usually less than half a day.
- `M`: a medium task, usually half a day to two days.
- `L`: a large task, usually multiple days and worth splitting further.

### Dependency Notes

- Tasks `1` through `4` define the platform and data contract. Do not skip ahead until those are stable.
- Tasks `5` through `11` are the backend feature core and should be completed before serious frontend polish.
- Tasks `12` through `17` are the user-facing application layer and can overlap once backend contracts stop moving.
- Tasks `18` through `21` are hardening and deployment work and should happen before you rely on the system day to day.

### Suggested Milestones

1. Backend foundation complete: tasks `1` through `8`.
2. QR and media workflow complete: tasks `9` through `11`.
3. Admin and scan UI complete: tasks `12` through `17`.
4. Deployment-ready local release: tasks `18` through `21`.

### Starter Checklist

Use this as the first working week plan.

#### Day 1: Create the Running Skeleton

- Complete task `1` by creating `backend/`, `frontend/`, `deploy/`, and `docker-compose.yml`.
- Add minimal Dockerfiles for FastAPI and SvelteKit.
- Initialize the backend as a `uv` project with a `pyproject.toml`.
- Add a basic Nginx config that proxies `/api/` to the backend and everything else to the frontend.
- Confirm all containers can start, even if the app pages are still placeholders.

#### Day 2: Stand Up the Backend Base

- Complete task `2` by creating the FastAPI entry point, router registration pattern, config loading, and a health endpoint.
- Decide on the backend package layout before adding feature code.
- Make sure the backend container serves a simple JSON response through Nginx.

#### Day 3: Define the Database Contract

- Start tasks `3` and `4`.
- Add SQLAlchemy, Alembic, and initial models for `rooms`, `labels`, `containers`, and `images` via `uv add`.
- Implement the immutable dashed container code generation strategy before any container CRUD routes exist.
- Create the first migration and verify PostgreSQL schema creation.

#### Day 4: Build Reference Data APIs

- Complete tasks `5` and `6`.
- Implement room and label CRUD routes with validation rules.
- Decide and document delete semantics for referenced rooms and labels.
- Verify these endpoints manually with curl or the generated API docs.

#### Day 5: Build the Core Container Slice

- Start task `7` and, if time allows, task `8`.
- Implement container create, list, detail, update, and delete.
- Add search and filter support to the container listing route.
- Stop at the point where the backend can fully represent a container without images or QR output if needed.

#### Day 6: Add Media and QR Features

- Complete tasks `9` and `10`.
- Implement image upload and serving from the local volume.
- Implement QR code generation using the stable LAN scan URL.
- Verify that a generated QR image scans correctly from a phone on the local network.

#### Day 7: Start the Frontend Against Stable APIs

- Complete task `12`, then begin tasks `13` and `14`.
- Create the SvelteKit shell, Skeleton setup, and the admin dashboard route.
- Wire the dashboard to the live container listing API instead of mock data.
- Build the create flow only after backend contracts stop changing.

### 1. Repository and Compose Scaffold

Status: complete as of `2026-05-06`.

Responsible for establishing the base project structure and local runtime.

- Create `backend/`, `frontend/`, and `deploy/` directories to match the documented layout.
- Add `docker-compose.yml` with `db`, `backend`, `frontend`, and `nginx` services.
- Define named Docker volumes for PostgreSQL data and image storage.
- Add initial Dockerfiles for FastAPI and SvelteKit services.
- Add environment variable handling for database connection, image storage path, and public base URL.
- Set the backend up as a `uv`-managed Python project using `pyproject.toml` and `uv.lock`.

### 2. FastAPI App Bootstrap

Status: complete as of `2026-05-06`.

Responsible for the backend application skeleton and shared infrastructure.

- Create the FastAPI entry point and register routers.
- Add configuration loading, database session management, and startup wiring.
- Add shared error handling for missing records and invalid input.
- Add a basic health endpoint for container-level diagnostics.
- Establish backend developer tooling with `pytest` for tests, `ruff` for formatting and linting, and `ty` for type checking.

### 3. Database Schema and Migration Setup

Status: complete as of `2026-05-06`.

Responsible for creating the persistent data model and schema evolution workflow.

- Set up SQLAlchemy models and a migration tool such as Alembic inside the backend `uv` project.
- Create tables for `rooms`, `labels`, `containers`, and `images`.
- Add indexes and constraints, especially unique constraint on `containers.code`.
- Add timestamps and foreign key relationships.
- Add `search_vector` support and the trigger or generated-column strategy used to keep it updated.

### 4. Unique Container Code Generation

Status: complete as of `2026-05-06`.

Responsible for generating stable, unique container codes.

- Implement a code generator that produces uppercase alphanumeric 4-character values with a dash in the middle (for example `AB-12`).
- Check for collisions against existing records before insert completes.
- Ensure generated codes are immutable after creation.
- Add tests for collision handling and format validation.

### 5. Room CRUD API

Responsible for room management endpoints and validation.

- Implement `GET`, `POST`, `PUT`, and `DELETE` endpoints for rooms.
- Validate duplicate or empty room names.
- Define delete behavior when a room is referenced by containers.
- Return response models that the frontend can use directly.

### 6. Label CRUD API

Responsible for colour label management.

- Implement `GET`, `POST`, `PUT`, and `DELETE` endpoints for labels.
- Validate label names and hex colour format.
- Define delete behavior when a label is assigned to containers.
- Return label data in a form suitable for swatches and filters.

### 7. Container CRUD API

Status: complete as of `2026-05-06`.

Responsible for the core container lifecycle.

- Implement container create, list, detail, update, and delete endpoints.
- Generate the immutable container code during create.
- Support room and label assignment through foreign keys.
- Return image metadata with container detail responses.
- Ensure deletes also clean up related image records and, once task `9` exists, stored files.

### 8. Search and Filtering

Status: complete as of `2026-05-06`.

Responsible for searchable container listing.

- Extend `GET /api/containers` to support `search`, `room_id`, `label_id`, and `code` filters.
- Use PostgreSQL full-text search for name, description, and code matching.
- Ensure search results clearly return and display each matching container's 4-character code so users can search by contents and recover the identifier they need.
- Support combined filters in a single query.
- Add indexes and query tests so search remains responsive with larger datasets.

### 9. Image Upload and Storage

Status: complete as of `2026-05-06`.

Responsible for managing container photos on disk and in the database.

- Implement multipart image upload for a container.
- Treat the first image for a container as its primary exterior/storage-location photo.
- Store images in the configured local volume with safe generated filenames.
- Persist image metadata including caption and sort order.
- Serve stored images back to the frontend.
- Add delete and update operations for captions and ordering.

### 10. QR Code Rendering

Status: complete as of `2026-05-06`.

Responsible for generating printable QR label assets.

- Build a QR rendering utility that encodes the stable scan URL.
- Render the container code, QR image, container name, and room name into one label tile.
- Apply the selected label colour as the background while preserving scan contrast.
- Expose a backend endpoint that returns a print-ready PNG.

### 11. Public Scan View Data Path

Status: complete as of `2026-05-06`.

Responsible for supporting phone-based read-only access from QR scans.

- Ensure scan URLs resolve through the single LAN origin.
- Provide a backend or frontend data path for loading one container by ID.
- Keep the scan experience read-only and isolated from admin actions.
- Make sure image URLs and metadata work correctly on mobile browsers.

### 12. SvelteKit Frontend Bootstrap

Status: complete as of `2026-05-06`.

Responsible for the application shell and frontend development foundation.

- Create the SvelteKit app structure under `frontend/`.
- Configure Skeleton UI and establish the base theme tokens.
- Set up shared API helpers, route layout, and global styles.
- Confirm the app can run behind Nginx with the documented origin.

### 13. Admin Dashboard UI

Status: complete as of `2026-05-06`.

Responsible for the main container browsing and discovery experience.

- Build the dashboard route for container listing.
- Add the search bar, room filter, and label filter controls.
- Render container cards or rows with thumbnail, code, room, and label indicators.
- Add empty, loading, and error states.

### 14. Create Container Flow

Status: complete as of `2026-05-06`.

Responsible for creating new containers from the UI.

- Add a creation flow from the dashboard.
- Allow room and label selection during creation.
- Clearly instruct the user that the first uploaded image should show the outside of the container and where it is physically stored.
- Support initial image upload after create or within the same flow.
- Refresh the UI state so the new container appears immediately.

### 15. Container Detail and Edit UI

Status: complete as of `2026-05-06`.

Responsible for editing and maintaining container metadata.

- Build the `/containers/[id]` route.
- Show the immutable code prominently.
- Add form controls for name, description, room, and label.
- Clearly explain that the primary image is the exterior/storage-location photo for the container.
- Add image upload, delete, caption edit, and reorder interactions.
- Add QR download access from the detail page.

### 16. Mobile Scan View UI

Responsible for the phone-optimized container viewer.

- Build the `/scan/[id]` route in SvelteKit.
- Server-render the initial page load.
- Display code, name, room, description, and images with minimal UI chrome.
- Ensure the view remains usable on smaller screens and slower devices.

### 17. Print Sheet UI

Responsible for batch label printing from the frontend.

- Build the `/print` route.
- Allow selecting multiple containers for one print run.
- Render labels in a printable page grid.
- Add print-specific styling and verify the layout on paper sizes you plan to use.

### 18. Nginx Reverse Proxy Configuration

Responsible for exposing the system as one LAN-only web application.

- Route `/api/*` requests to FastAPI.
- Route frontend and scan page requests to SvelteKit.
- Serve the application on a single stable LAN hostname or address.
- Keep the configuration aligned with the LAN-only deployment model.

### 19. File Cleanup and Delete Semantics

Responsible for keeping stored files and related records consistent.

- Define how image files are removed when images or containers are deleted.
- Prevent orphaned files on disk.
- Handle partial failure cases where database and filesystem operations can diverge.
- Add tests for delete behavior.

### 20. Testing and Verification

Responsible for proving the system works end to end.

- Add backend tests for CRUD, search, code generation, and QR endpoints.
- Run backend verification through `uv run pytest`, `uv run ruff check`, `uv run ruff format --check`, and `uv run ty check`.
- Add frontend tests for key routes and interactive flows where practical.
- Manually verify mobile scan behavior from a phone on the local network.
- Verify printed QR labels remain scannable with the chosen colours and layout.

### 21. LAN Deployment Documentation

Responsible for making the system runnable in the target home-network environment.

- Document required environment variables and startup steps.
- Document how to assign a stable LAN hostname or DHCP reservation.
- Document where images are stored and how to back them up.
- Document current limitations, especially the LAN-only and single-user assumptions.

---

## Assumptions & Constraints

- Server has a **stable LAN hostname** (for example `containerscan.local`) backed by a DHCP reservation or static lease
- All scanning devices are on the **same local network** (home Wi-Fi)
- Images are stored on the **host filesystem** via a Docker volume — no cloud storage
- No HTTPS required (LAN-only); can be added later via a self-signed cert if desired
- Single-user, no authentication needed
- Colour labels are user-defined hex colours — no fixed palette is enforced
- Container codes are uppercase alphanumeric in the format `AA-BB`, auto-generated, unique across all containers, and immutable after creation
- Full-text search is handled by PostgreSQL natively — no external search engine required
- Frontend and API are served through a single LAN origin via Nginx to avoid port-specific QR codes and CORS complexity
