# KájovoCMLNG SSOT package

The canonical specification is [00_SSOT/KajovoCMLNG_SSOT.md](00_SSOT/KajovoCMLNG_SSOT.md). Embedded machine-readable contracts are authoritative; extracted UI files are projections. Audit evidence does not introduce another normative source.

This repository contains specification, validation and presentation artifacts, not the product implementation. See the [Czech entry index](README_CZ.md), [audit status](audit/FINAL_AUDIT.md), [quality checks](QUALITY_ASSURANCE.md) and [UI references](03_UI_REFERENCE/index.html).

Generate projections with `python scripts/project_experience.py`; verify them with `--check`. Render Czech references with `python scripts/render_live_views.py --render`, or English references by adding `--locale en`. All operation examples are explicitly labelled sample data.

No freeze, release or production deployment is performed by this task. A passing individual validator is not evidence that the complete package is ready for implementation or freeze.
