# Docusaurus export

Always runs after Post-Deployment Testing (or after that stage marks
SKIPPED). Official product docs do not depend on a deploy in this cycle.

## Config

From `aidlc.config.yaml` `operations.*`:

- `docusaurus_path` (default `docs-site`)
- `docs.language` (default `en`)
- `include` / `exclude` (defaults in `docs/aidlc.config.example.yaml`)

## Scaffold — generate in the product repo

If `operations.docusaurus_path` is missing `package.json`, **write** the
files listed in `operations/docusaurus-scaffold-files.md` into that folder
in the **product** repository:

- `package.json`
- `docusaurus.config.js` (set `i18n.defaultLocale` to `operations.docs.language`)
- `sidebars.js`
- `src/css/custom.css`
- `docs/index.md` (placeholder; exported sources replace/extend `docs/`)
- `static/img/.gitkeep`

Do **not** read or copy `templates/docusaurus-scaffold/` from the rules
fork at runtime. That tree is a CI fixture in this fork only. The product
site is generated here.

Then `npm install` and `npm run build` in that folder. A failing build is
blocking.

## Include / exclude

Copy included sources into `docs/` using the markers in
`scripts/aidlc-validate/README.md`. **Must be absent** from the site tree:
`audit.md`, `deployment-deploy.md`, question files, raw plans.

### MDX braces and `[Answer]:` lines

Docusaurus 3 compiles markdown as MDX. A cell such as `Book {id, title}`
fails the build (`id is not defined`). A line ` [Answer]: A ` is a
CommonMark **link reference definition** (`[Answer]` → URL `A`) and
breaks the build when `onBrokenLinks` is `throw`.

When copying markdown into `docs-site/`:

1. Prefer rewriting `{identifier}` as `` `{identifier}` `` or as the
   identifier without braces.
2. Otherwise escape `{` as `\{` and `}` as `\}` **outside fenced and
   inline code**.
3. Rewrite every line that starts with `[Answer]:` so it is not a link
   definition, for example `\[Answer\]: A` or wrap the line in backticks
   or a code fence. Do this in the **exported copy only**.
4. Do not change the source under `aidlc-docs/` unless the catalog itself
   used braces; the exported copy must be MDX-safe and must not contain
   unescaped `[Answer]:` lines.

Run:

```bash
python3 -m aidlc_validate export --root PRODUCT_REPO
```

Use **`python3`**. Do not assume a `python` command exists.

Write `aidlc-docs/operations/docusaurus-export.md` with what was copied and
the validator result.

## After export — gate `operations`

Present `operations-summary.md` (or note SKIPPED deploy/PDT), the docs-site
path, and the proposed delivered-feature marks on the Vision. **Wait for
explicit approval.** Only after approval, mark the in-scope features as
delivered in `aidlc-docs/vision/features.md` / `vision-document.md`. Do not
mark them before the gate.
