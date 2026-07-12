# Export / Import

Use **Export / Import** to move route definitions between Fluxomni Studio instances, restore reviewed route configuration, or save a route-definition snapshot before major changes.

**Export / Import** is a sidebar action under **Control**, not a separate page. Select it to open the modal.

## Export route definitions

Choose the export scope in the modal, then download or copy the generated JSON. Store exported files securely: route definitions can contain destination addresses and operational configuration.

Use an export before making broad route changes or when preparing a migration. The export contains route-definition data; it does not create accounts or restore passwords on import.

## Preview an import

1. Open **Export / Import** and select the import tab.
2. Paste exported JSON or upload a `.json` file.
3. Select the import options, then preview the proposed changes.
4. Review every route, settings change, warning, and error before applying.

The preview simulates changes before Fluxomni Studio writes state. Outputs are matched by destination URL, so changing a destination can appear as one output removed and another created.

## Apply changes safely

By default, import preserves definitions that are not present in the submitted specification. Select **Replace existing definitions** only when the imported JSON is intended to remove definitions missing from the spec.

A preview with dangerous changes requires typing `APPLY` before the modal enables **Apply**. If imported owner IDs do not exist on the destination instance, you can preview a username-based owner mapping for existing local users.

After applying, download or copy the import report and confirm the affected routes in [Routes](routes.md).

## Next steps

- [Routes](routes.md) — verify inputs, outputs, and execution after an import
- [Settings](settings.md#users) — review local users and route ownership
- [Backup & Restore](../getting-started/backup.md) — back up application state and `.env`, not only route definitions
