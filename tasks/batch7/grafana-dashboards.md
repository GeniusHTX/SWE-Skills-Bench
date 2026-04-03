# Task: Implement a Dashboard Provisioning API Handler in Grafana

## Background

Grafana (https://github.com/grafana/grafana) supports provisioning dashboards from disk using YAML configuration files. The task is to implement a Go HTTP handler in the Grafana backend that accepts a dashboard JSON payload via POST, validates it against the Grafana dashboard schema, persists it to the provisioned dashboard store, and returns a standardized response including the generated UID and version.

## Files to Create/Modify

- `pkg/api/dashboard_provision.go` (create) — HTTP handler `ProvisionDashboardHandler` for `POST /api/dashboards/provision`
- `pkg/services/dashboards/provision_service.go` (create) — `DashboardProvisionService` with validation and persistence logic
- `pkg/services/dashboards/provision_service_test.go` (create) — Unit tests for the provision service
- `pkg/api/routing/dashboard_routes.go` (modify) — Register the new endpoint with middleware for authentication and role check

## Requirements

### `DashboardProvisionService` (`provision_service.go`)

```go
type ProvisionRequest struct {
    Dashboard   map[string]interface{} `json:"dashboard"`    // Raw dashboard JSON object
    FolderUID   string                 `json:"folderUid"`    // Target folder UID (empty = General)
    Overwrite   bool                   `json:"overwrite"`    // Allow overwriting existing dashboards by UID
    Message     string                 `json:"message"`      // Commit message for version history
}

type ProvisionResult struct {
    UID     string `json:"uid"`
    ID      int64  `json:"id"`
    URL     string `json:"url"`
    Status  string `json:"status"`  // "success"
    Version int    `json:"version"`
    Slug    string `json:"slug"`
}

type DashboardProvisionService struct {
    store      db.DB
    folderSvc  folder.Service
    guardian   guardian.DashboardGuardian
}

func NewDashboardProvisionService(store db.DB, folderSvc folder.Service, guardian guardian.DashboardGuardian) *DashboardProvisionService

func (s *DashboardProvisionService) Provision(ctx context.Context, orgID int64, req *ProvisionRequest) (*ProvisionResult, error)
```

#### `Provision` Logic

1. **Extract UID**: If `req.Dashboard["uid"]` is set and non-empty, use it; otherwise generate a new UID via `util.GenerateShortUID()`

2. **Validate dashboard JSON**:
   - `title` field must be present and a non-empty string
   - `schemaVersion` field must be a number > 0
   - `panels` field, if present, must be an array
   - Return `ErrInvalidDashboard{Field: "title", Reason: "missing or empty"}` if validation fails

3. **Check for existing dashboard** (if UID is set):
   - Query the store for a dashboard with this UID in this org
   - If found and `req.Overwrite` is `false`: return `ErrDashboardExists{UID: uid}`
   - If found and `req.Overwrite` is `true`: proceed with update; increment version from existing

4. **Resolve folder**: If `req.FolderUID` is empty, use the General folder (ID = 0). Otherwise look up the folder by UID and verify it exists.

5. **Persist**: Insert or update the dashboard in the store. Set `provisioned = true`, `org_id = orgID`, and record the `Message` in the version record.

6. **Return** `ProvisionResult` with the final UID, ID, version number, slug (URL-safe title), and URL (`/d/<uid>/<slug>`).

#### Error Types

```go
type ErrInvalidDashboard struct {
    Field  string
    Reason string
}

func (e ErrInvalidDashboard) Error() string {
    return fmt.Sprintf("invalid dashboard: field %q %s", e.Field, e.Reason)
}

type ErrDashboardExists struct {
    UID string
}

func (e ErrDashboardExists) Error() string {
    return fmt.Sprintf("dashboard with UID %q already exists; set overwrite=true to replace it", e.UID)
}
```

### HTTP Handler (`dashboard_provision.go`)

```go
func (hs *HTTPServer) ProvisionDashboardHandler(c *contextmodel.ReqContext) response.Response {
    // 1. Decode request body into ProvisionRequest
    // 2. Call hs.provisionSvc.Provision(c.Req.Context(), c.SignedInUser.GetOrgID(), &req)
    // 3. Return response.JSON(http.StatusOK, result) on success
    // 4. On ErrInvalidDashboard: return response.Error(http.StatusBadRequest, err.Error(), err)
    // 5. On ErrDashboardExists: return response.Error(http.StatusConflict, err.Error(), err)
    // 6. On other errors: return response.Error(http.StatusInternalServerError, "failed to provision dashboard", err)
}
```

#### Authentication & Authorization

- Register the endpoint with `reqSignedIn` middleware (existing middleware)
- Require the `OrgRoleType: org.RoleEditor` or higher (use existing `reqOrgRole` middleware)
- The route: `r.Post("/api/dashboards/provision", reqSignedIn, reqOrgRole(org.RoleEditor), routing.Wrap(hs.ProvisionDashboardHandler))`

### Route Registration (`dashboard_routes.go`)

In the existing route registration function, add:
```go
r.Post("/api/dashboards/provision", middleware.ReqSignedIn, middleware.ReqOrgRole(org.RoleEditor), routing.Wrap(hs.ProvisionDashboardHandler))
```

Do not remove or modify any existing dashboard routes.

## Expected Functionality

- `POST /api/dashboards/provision` with `{"dashboard": {"title": "My Dashboard", "schemaVersion": 36, "panels": []}, "folderUid": "", "overwrite": false, "message": "initial"}` returns HTTP 200 with `{"uid": "<generated>", "version": 1, "status": "success", "url": "/d/<uid>/my-dashboard"}`
- Posting a dashboard with an existing UID and `overwrite: false` returns HTTP 409 Conflict
- Posting a dashboard with an existing UID and `overwrite: true` returns HTTP 200 with `version: 2`
- Posting a dashboard without a `title` field returns HTTP 400 with the invalid field message
- Unauthenticated requests return HTTP 401; Viewer role requests return HTTP 403

## Acceptance Criteria

- `Provision` correctly generates a UID when none is provided
- `Provision` validates `title`, `schemaVersion`, and `panels` fields
- `ErrDashboardExists` is returned when the dashboard exists and `overwrite=false`
- When `overwrite=true`, the version is incremented from the existing dashboard's version
- `ProvisionDashboardHandler` maps `ErrInvalidDashboard` to 400, `ErrDashboardExists` to 409, and other errors to 500
- The endpoint is registered at `POST /api/dashboards/provision` with authentication and editor role requirement
- All unit tests pass with mock store and folder service, covering: new dashboard creation, overwrite, no-overwrite conflict, and validation errors
