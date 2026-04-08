# Settings

The Settings page (`/settings`) lets administrators configure the Control Surface behavior, security posture, and user accounts. Access it from **Settings** in the sidebar.

![The Settings page with General, Security, and Users sections](../images/user-guide/settings.jpg)

The page header shows your current **Role** (e.g. Admin) and **Access** level (e.g. Admin settings). Settings are organized into sections scoped to your effective role.

## General

**Control surface defaults** configure how the operator interface behaves across all users:

- **Title** — the server name displayed in the browser tab and shared shell chrome. Set this to something meaningful like your organization name or stream label.
- **Confirm deletion actions** — when enabled, destructive operations (deleting routes, outputs, files) require an explicit confirmation dialog.
- **Confirm enable and disable actions** — when enabled, toggling inputs or outputs on/off requires confirmation. Useful for production environments where accidental toggles could disrupt a live broadcast.

**Google Drive** settings control file ingest from Google Drive:

- **Google API Key** — required before operators can load files from Google Drive into route playlists. Obtain an API key from the Google Cloud Console with the Drive API enabled.
- **Files Limit** — maximum number of concurrent downloads when Google Drive ingest is active.

**Live shell summary** shows read-only values propagated through the shared authenticated shell:

- **Public Host** — the domain or IP the instance is accessible at.
- **Delete Confirmation** — whether the deletion confirmation toggle is active.
- **Enable Confirmation** — whether the enable/disable confirmation toggle is active.
- **Sign-in Mode** — current authentication posture (e.g. "Named users required").

## Security

The Security section shows your current **Access posture** — the signed-in user, effective role, and authentication requirement — and lets you manage credentials.

### Access posture

- **Current User** — the username you are signed in as (e.g. `@admin`).
- **Effective Role** — your active role for this session (Admin, Operator, or Viewer).
- **Auth Requirement** — the server's sign-in mode. See *Sign-in modes* below.

### Change password

Update the password for the currently signed-in user. Password changes invalidate the current session and sign you back in with the new secret.

### Sign-in modes

FluxOmni supports two sign-in modes, configured by an Admin in this section:

- **Named user sign-in** — every operator must authenticate with a local username and password. This is the recommended mode for production.
- **Open access** — no authentication is required. Anyone who can reach the Control Surface has full access. Suitable for local development or firewalled networks only.

## Users

The Users section lets administrators create local accounts and manage the user directory.

### Create a user

Fill in the **Username**, optional **Display Name**, **Password**, and select a **Role** from the dropdown. Click **Create user** to add the account.

### User roles

FluxOmni has three roles that map directly to the backend authorization contract:

| Role | Access |
| ---- | ------ |
| **Admin** | Full access to all operations: routes, fleet, settings (including security and user management), and export/import. |
| **Operator** | Stream management access: create and manage routes, playlists, and outputs. Can view fleet status but cannot modify fleet settings, admin settings, or user accounts. |
| **Viewer** | Read-only access to all pages. Can observe routes, fleet, and settings but cannot modify anything. |

### Directory

Below the creation form, the **Directory** lists all local accounts with their role, last login timestamp, and controls to **Update role** or **Delete** the account. You cannot delete the account you are currently signed in with.

## Export / Import

Accessible from **Export / Import** in the sidebar, this page lets you bulk export or import route configurations. Use this to:

- Back up your routing configuration before major changes.
- Migrate routes between FluxOmni instances.
- Share route templates with other operators.
