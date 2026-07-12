# Attention

Use the **Attention** page to triage active route, fleet, and storage issues from one place before they interrupt an operator workflow.

Open **Attention** from the **Operate** section of the sidebar, or visit `/attention`.

## Review active alerts

The page groups actionable alerts by surface:

- **Route alerts** identify an affected route and offer **Open route** to inspect its current routing and execution context.
- **Fleet alerts** identify media-node conditions that can block route execution or operator workflows.
- **Storage alerts** identify artifact-capacity conditions that can block uploads and imports; use **Open artifacts** to inspect the library.

Each route or storage alert is marked **Critical** or **Attention**. Start with Critical alerts, then use the linked route, fleet, or artifact surface to investigate the condition.

When no active or known alert exists, the page shows **All clear**.

## Mark an alert as known

Use **Known** when an issue is understood and is being handled elsewhere. The alert moves to **Known issues** and no longer contributes to the sidebar urgency badge.

Marking an alert as known does not repair the underlying condition. Use **Restore** in **Known issues** to return it to active triage when it needs attention again.

## Next steps

- [Routes](routes.md) — inspect route inputs, outputs, runtime state, and playback
- [Fleet](fleet.md) — inspect media-node health and artifact distribution
- [Artifacts](artifacts.md) — resolve storage admission and import issues
- [Monitoring](../getting-started/monitoring.md) — configure broader health and telemetry monitoring
