# CSIT327 – Information Management 2
## Project Development 2 — Implementation / Completion Report

> **Note before exporting to PDF:** Paste your browser screenshots in Section 2.2 (*Screenshots*) and update the Pull Request URLs and test account credentials after merging PRs on GitHub, then export as `docs/Tultol-Mauring-Alexandra-G02-PD2.pdf`.

---

### Project Information

| Field | Details |
|---|---|
| **System Name** | Tultol |
| **Student Name** | Mauring, Alexandra Louie C. |
| **Section** | G02 |
| **Increment** | Project Development 2 – Core Feature (Vertical Slice) |
| **GitHub Repository** | https://github.com/mautcha/Tultol-Mauring-Alexandra-G02 |
| **Date Submitted** | 11/16/2026 |

---

### 1. Project Overview

Tultol is a web-based indoor mall navigation system designed for shoppers and mall administrators in Metro Cebu malls (such as SM Seaside City Cebu, Ayala Center Cebu, and SM City Cebu). Shoppers often struggle to locate specific stores, unit numbers, and wings inside large multi-level malls. Tultol solves this by providing a searchable mall, floor, and store directory with indoor landmark directions and personal store bookmarks.

**Core feature for this increment:** Mall Store & Floor Directory and Shopper Saved Stores

**Justification:** Helping users find stores, identify which floor and unit a store belongs to, and follow indoor landmark directions is the primary purpose of an indoor mall navigation system. Linking Mall Admin store management with Shopper search and personal bookmarks connects both user roles to the central database entities of Tultol.

---

### 2. Features Implemented in This Increment

#### 2.1 Standard Features (from Project Development 1)

| Feature | Status | Notes |
|---|---|---|
| Account Registration | Complete | Registers Shopper accounts with email/username uniqueness checks and PBKDF2 password hashing (`accounts/views.py`, `accounts/forms.py`). |
| Login / Logout | Complete | Supports login by username or email, validates `?next=` redirects, and enforces POST-only logout (`accounts/views.py`). |
| Role-Based User Dashboard | Complete | Separate dashboards for `shopper` (`/dashboard/shopper/`) and `admin` (`/dashboard/admin/`) protected by `@login_required` and `@role_required`. |
| User Profile (view and edit) | Complete | Logged-in users can view and update only their own name, email, contact number, and profile photo, plus change/reset password. |

#### 2.2 Core Feature: Mall Store & Floor Directory + Shopper Saved Stores

**Description:** The core feature implements a full vertical slice of Tultol's mall navigation directory stored in Supabase PostgreSQL. Mall Admins can create, view, update, and delete Malls, Floor levels, and Stores (including unit codes, categories, open status, and indoor landmark directions). Logged-in Shoppers can search and filter stores across malls and categories, view floor-level details and directions, and bookmark stores into their personal **My Saved Stores** list with editable visit notes.

##### User Roles and Access

| Role | What this role can do in the feature |
|---|---|
| **Shopper** | Browse malls and floor levels, search/filter stores, view store landmark directions, and Create/Read/Update/Delete their own `SavedStore` bookmarks and notes. Blocked from admin CRUD URLs. |
| **Mall Admin** | Full CRUD on `Mall`, `Floor`, and `Store` records, plus browsing the store directory and managing their own bookmarks. |

##### User Flow

1. User logs in via `/accounts/login/` and is redirected to their role-specific dashboard (`/dashboard/admin/` or `/dashboard/shopper/`).
2. **Mall Admin flow:** Admin opens **Manage Malls & Floors** (`/directory/malls/`) to add a `Mall` and its `Floor` levels, then opens **Manage Stores & Tenants** (`/directory/stores/add/`) to create `Store` entries with unit codes and landmark directions, and can edit or delete records at any time.
3. **Shopper flow:** Shopper opens **Store Search** (`/directory/`) from the dashboard, filters by keyword, mall, or category, and clicks **View Directions** (`/directory/stores/<id>/`) to read floor notes and landmark directions.
4. On the store detail page, the shopper enters an optional visit note and clicks **Save Store** (`POST /directory/saved/add/<store_id>/`) to bookmark it.
5. Shopper opens **Saved** (`/directory/saved/`) to view their bookmarked stores, click **Edit Note** to update their visit note, or click **Remove** to delete the bookmark.

##### CRUD Operations

| Operation | Implemented? (Yes/No) | Where in the UI | Who can do it |
|---|---|---|---|
| **Create** | Yes | `+ Add Mall`, `+ Add Floor`, `+ Add Store` buttons; `📌 Save Store` form on Store Detail page | Mall Admin (Malls/Floors/Stores); Shopper/Logged-in User (Saved Stores) |
| **Read** | Yes | `/directory/` (Store list & filter), `/directory/malls/`, `/directory/stores/<id>/`, `/directory/saved/` | Both Shopper and Mall Admin (Saved Stores scoped to `request.user` only) |
| **Update** | Yes | `Edit` buttons on Mall, Floor, and Store pages; `Edit Note` button on Saved Stores | Mall Admin (Malls/Floors/Stores); Owner only (Saved Stores) |
| **Delete** | Yes | `Delete` POST buttons on Mall, Floor, and Store pages; `Remove` POST button on Saved Stores | Mall Admin (Malls/Floors/Stores); Owner only (Saved Stores) |

##### Database Models

| Model / Table | Key Fields | Relationships (ForeignKey / ManyToMany) |
|---|---|---|
| `Mall` (`directory_mall`) | `id`, `name`, `city`, `address`, `opening_hours`, `created_at` | `created_by`: `ForeignKey → User` |
| `Floor` (`directory_floor`) | `id`, `floor_number`, `name`, `map_notes` | `mall`: `ForeignKey → Mall`; `created_by`: `ForeignKey → User` |
| `Store` (`directory_store`) | `id`, `name`, `category`, `unit_code`, `landmark_directions`, `operating_hours`, `is_open`, `created_at`, `updated_at` | `mall`: `ForeignKey → Mall`; `floor`: `ForeignKey → Floor`; `created_by`: `ForeignKey → User` |
| `SavedStore` (`directory_savedstore`) | `id`, `note`, `created_at` | `user`: `ForeignKey → User`; `store`: `ForeignKey → Store` (unique per user & store) |

##### Key Files

| Layer | File path(s) |
|---|---|
| Models | `directory/models.py`, `directory/migrations/0001_initial.py`, `directory/migrations/0002_savedstore.py` |
| Views | `directory/views.py` |
| URLs | `directory/urls.py`, `tultol/urls.py` |
| Forms | `directory/forms.py` |
| Templates | `templates/directory/store_list.html`, `templates/directory/store_detail.html`, `templates/directory/mall_list.html`, `templates/directory/saved_list.html`, `templates/directory/form.html` |

##### Validation and Business Rules

| Rule | How it is enforced |
|---|---|
| Only logged-in users can access directory and bookmarks | `@login_required` decorator on all `directory` views redirects anonymous users to `/accounts/login/`. |
| Only Mall Admins can create/edit/delete malls, floors, and stores | `@role_required('admin')` decorator checks `request.user.profile.role` and blocks shoppers with an error message. |
| Mall names must be unique (case-insensitive) | `MallForm.clean_name()` raises `ValidationError` if duplicate. |
| Floor number must be unique per mall | `FloorForm.clean()` and `Meta.unique_together = ('mall', 'floor_number')` prevent duplicate floor numbers in the same mall. |
| Unit code is normalized uppercase and must be unique per floor | `StoreForm.clean_unit_code()` and `StoreForm.clean()` reject duplicate unit codes on the same floor; `StoreForm.save()` automatically derives `store.mall` from `store.floor.mall`. |
| Users can only view, edit, and delete their own saved stores | Views filter by `user=request.user` and use `get_object_or_404(SavedStore, pk=pk, user=request.user)`. |
| Duplicate bookmarks are prevented | `Meta.unique_together = ('user', 'store')` + `SavedStore.objects.get_or_create(...)` in `saved_store_create_view`. |

##### Branches and Pull Requests

| Branch | Merged Into | Pull Request Link | What it contains |
|---|---|---|---|
| `feature/mall-store-directory` | `develop` *(and PR #1)* | `https://github.com/mautcha/Tultol-Mauring-Alexandra-G02/pull/1` *(update with develop PR link)* | `directory` app, `Mall`/`Floor`/`Store` models, migrations, admin CRUD, search/filter UI, and tests |
| `feature/shopper-bookmarks` | `develop` | `[Paste PR #2 Link]` | `SavedStore` model, migration, shopper bookmark CRUD, `README.md`, and PD2 report |
| `develop` | `main` | `[Paste Final Release PR Link]` | Increment release (PD2 vertical slice + documentation) |

##### Screenshots

- `[Screenshot 1 – Mall Admin adding a Mall / Floor / Store]`
- `[Screenshot 2 – Validation error message (e.g., duplicate unit code or missing required field)]`
- `[Screenshot 3 – Shopper searching the Store Directory and viewing landmark directions]`
- `[Screenshot 4 – Shopper saving a store and managing My Saved Stores]`

---

### 3. Remaining Tasks

| No. | Task | Description | Priority | Target Increment |
|---|---|---|---|---|
| 1 | Interactive 2D Floor Map Viewer | Display clickable floor map images with store pin markers per floor level. | High | Project Development 3 |
| 2 | Parking Pin Saver | Allow shoppers to save and update their parked vehicle level, wing, and pillar code. | Medium | Project Development 3 |
| 3 | Cloud Media Storage (Supabase Storage) | Move uploaded profile photos and floor map images from local `media/` to Supabase Storage for deployment. | Low | Project Development 3 |

---

### 4. Outstanding Issues

| Issue ID | Description | Steps to Reproduce | Severity | Status / Workaround |
|---|---|---|---|---|
| ISS-01 | Uploaded profile photos are stored in local `media/` rather than cloud object storage. | 1. Log in 2. Open Profile -> Edit Profile 3. Upload photo | Minor | Open – works in local development; Supabase Storage planned for deployment. |

---

### 5. Test Accounts

| Role | Username / Email | Password |
|---|---|---|
| **Mall Admin** | `admin` | `[Set via create_default_admin --password ...]` |
| **Shopper** | `[Register a test shopper account]` | `[Test password]` |

---

### 6. Declaration

I declare that the work described in this report is my own, that it is accurately reflected in my GitHub repository, and that all remaining tasks and known issues are disclosed above.

Name: Alexandra Louie C. Mauring  
Date: 11/16/2026
