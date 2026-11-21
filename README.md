# panAtlas documentation

Source for the panAtlas documentation site: how panAtlas works, and an exhaustive reference for its metadata.
Built with MkDocs Material, the same way as the [GaiaKeep](https://gaiakeep.github.io/docs/) site.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve            # preview at http://127.0.0.1:8000
scripts/deploy.sh --dry-run       # gates (secret scan, public-content filter, name gate) + strict build
scripts/deploy.sh                 # publish to gh-pages (only when the owner has decided the site is public)
```

Install the pre-push gate once: `git config core.hooksPath scripts/hooks`.

Content rules (enforced by `scripts/public_filter.py`): no hostnames, addresses, accounts, absolute paths,
ORCID iDs, credentials, or institution and facility names. Pages cite the private repositories by
repo-relative path, never by link. `public_filter.py deny .` refuses any name on a private list, which the script
holds only as SHA-256 digests.

## Licence

The documentation text is licensed under [CC BY 4.0](LICENSE). The panAtlas software is not covered by this licence.
