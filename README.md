# panAtlas documentation

Source for the panAtlas documentation site: how panAtlas works, how it runs as a distributed system on
[Cresco](https://crescoedge.github.io/docs/), and an exhaustive reference for its metadata.
Built with MkDocs Material, the same way as the [Cresco](https://crescoedge.github.io/docs/) and
[GaiaKeep](https://gaiakeep.github.io/docs/) sites.

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/mkdocs serve            # preview at http://127.0.0.1:8000
scripts/deploy.sh --dry-run       # gates (secret scan, public-content filter) + strict build
scripts/deploy.sh                 # publish to gh-pages (only when the owner has decided the site is public)
```

Install the pre-push gate once: `git config core.hooksPath scripts/hooks`.

Content rules (enforced by `scripts/public_filter.py`): no hostnames, addresses, accounts, absolute paths,
ORCID iDs, credentials, or institution and facility names. Pages cite the private repositories by
repo-relative path, never by link.

## Licence

The documentation text is licensed under [CC BY 4.0](LICENSE). The panAtlas software is not covered by this licence.
