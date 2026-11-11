# Docusaurus export

Always runs after Post-Deployment Testing (or after that stage marks
SKIPPED). Official product docs do not depend on a deploy in this cycle.

## Config

From `aidlc.config.yaml` `operations.*`:

- `docusaurus_path` (default `docs-site`)
- `docs.language` (default `en`)
- `include` / `exclude` (defaults in `docs/aidlc.config.example.yaml`)

## Scaffold

If `operations.docusaurus_path` is missing `package.json`, copy the fork
template `templates/docusaurus-scaffold/` into that folder:

- `package.json`
- `docusaurus.config.js` (set `i18n.defaultLocale` to `operations.docs.language`)
- `sidebars.js`
- `docs/` for exported markdown

Then `npm install` and `npm run build` in that folder. A failing build is
blocking.

## Include / exclude

Copy included sources into `docs/` using the markers in
`scripts/aidlc-validate/README.md`. **Must be absent** from the site tree:
`audit.md`, `deployment-deploy.md`, question files, raw plans.

Run:

```bash
python -m aidlc_validate export --root PRODUCT_REPO
```

Write `aidlc-docs/operations/docusaurus-export.md` with what was copied and
the validator result.

## After export — gate `operations`

Present `operations-summary.md` (or note SKIPPED deploy/PDT), the docs-site
path, and the proposed delivered-feature marks on the Vision. **Wait for
explicit approval.** Only after approval, mark the in-scope features as
delivered in `aidlc-docs/vision/features.md` / `vision-document.md`. Do not
mark them before the gate.
