# Attention

Use the **Attention** page to review active route, fleet, and storage issues in one place before they interrupt your work.

Open **Attention** from the **Operate** section of the sidebar, or visit `/attention`.

## Review active alerts

The page groups alerts by area:

- **Route alerts** identify an affected route and offer **Open route** to check its current routing and execution state.
- **Fleet alerts** identify media-node conditions that can prevent routes from running or interrupt your work.
- **Storage alerts** identify artifact storage limits that can block uploads and imports; use **Open artifacts** to inspect the library.

Each route or storage alert is marked **Critical** or **Attention**. Start with Critical alerts, then open the linked route, fleet, or artifact page to investigate.

When no active or known alert exists, the page shows **All clear**.

## Mark an alert as known

Use **Known** when an issue is understood and is being handled elsewhere. The alert moves to **Known issues** and no longer contributes to the sidebar urgency badge.

Marking an alert as known does not repair the cause. Use **Restore** in **Known issues** to return it to the active alerts when it needs attention again.

## Next steps

- [Routes](routes.md) — inspect route inputs, outputs, runtime state, and playback
- [Fleet](fleet.md) — inspect media-node health and artifact distribution
- [Artifacts](artifacts.md) — resolve storage limit and import issues
- [Monitoring](../getting-started/monitoring.md) — set up health and telemetry monitoring
