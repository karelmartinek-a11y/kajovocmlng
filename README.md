# KájovoCML NG — development SSOT

**Freeze is blocked.** This package contains normative contracts, UI references and reproducible validation. It does not claim a completed first edition, a running implementation or production acceptance.

Start with [the Czech guide](README_CZ.md), [the SSOT](00_SSOT/KajovoCMLNG_SSOT.md), [the final audit](audit/FINAL_AUDIT.md) and [the machine-readable audit](audit/final-audit.json).

Run `python scripts/verify_package.py` for structural and integrity checks. Run `python scripts/verify_package.py --freeze` for the strict semantic gate. The latter must fail while unresolved findings remain. Literal PASS values in embedded historical audits are not proof of current package readiness.

The reference dashboard and specification editor are in `03_UI_REFERENCE/pages/`. They use explicitly labelled sample states; their controls expose canonical operation contracts and never pretend to execute production commands. The 48 responsive reference renders cover 12 states at four viewport sizes. See [visual bindings](01_UI_CONTRACT/ui/contracts/visual-artifact-bindings.json).

UI JSON resources mirrored from the SSOT must stay byte-identical. CSV matrices, catalogs and PNGs are generated views. `PACKAGE_MANIFEST.json` inventories all files; `FILE_MANIFEST_SHA256` hashes every file except itself. Git supplies the manifest's own immutable identity.
