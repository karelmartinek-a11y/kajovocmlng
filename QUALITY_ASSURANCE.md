# Quality assurance

## Meaning of results

`audit/final-audit.json` is the current package-level evidence. `structuralStatus=PASS` means the implemented structural checks passed; `status=BLOCKED` means the package cannot be declared complete or freeze ready. Read the blocker details before implementation admission.

The checks cover the repository inventory, strict JSON parsing, Python syntax for active resources, all embedded resource byte counts and hashes, compressed capsule integrity, UI mirror equality, action/field CSV projections, exact operation IDs, visual process-family coverage, new JSON Schema compilation, error record fields and unique codes, graphical artifact bindings, and the R9/R10/R16/UI/CLOSURE/R17 validators. The verifier detects opaque route payloads and incomplete inherited error predicates instead of trusting embedded claims of completeness.

Historical audit-only fragments are inspected and reported separately. Their literal PASS, revision markers and preserved source digests are provenance; they cannot grant current readiness. A truncated historical script is preserved as evidence and never executed.

## Visual verification

`scripts/render_reference.mjs` renders 12 states at 390×844, 768×1024, 1366×768 and 1920×1080. It records JavaScript errors, horizontal overflow, action-menu interaction, Escape dismissal and the output-data tab. Results are in `audit/visual-validation.json`. The source uses real HTML/CSS/SVG layouts and explicitly marked fixtures. The renderer is a reference-browser check, not a claim that the selected future production libraries or backend were deployed.

The visual audit includes inspection of desktop and mobile renders; the topology label overlap found during review was removed. Progress is an inline panel above the work surface. Mobile uses the same selected-object actions through a list and visible menu. No timer produces fictitious operation progress or communication traffic.

## Integrity and repeatability

Run `python scripts/regenerate_ui_projections.py` after editing the UI registry; it synchronizes embedded mirrors. Render graphics, refresh embedded metadata, write the audit, then run `scripts/update_manifests.py`. Verify the final tree after manifest generation. Rebuilding manifests is never a substitute for semantic review.

`python scripts/verify_package.py --freeze` must return a nonzero status while blockers remain. No freeze tag, branch lock or release is created by these scripts.
