# Submitting Greek Math Reader to the NVDA Add-on Store

This is the exact process, based on the official submission guide
(<https://github.com/nvaccess/addon-datastore/blob/master/docs/submitters/submissionGuide.md>).

The store submission itself must be completed from the maintainer's GitHub
account because the issue form records who is authorized to publish this add-on
ID. The release asset must still be public and directly downloadable. The
README currently documents manual installation of the unpublished 1.1.5
diagnostic build; after publication, normal users should install from the
NVDA Add-on Store.

## Before you submit (one-time setup)

1. **Publish the source on GitHub** (e.g. `github.com/<you>/NVDA-Greek-Math`).
   The manifest's `url` in `buildVars.py` must point to it — update it if your
   repository URL differs, then rebuild.
2. **Test on Windows with real NVDA** (see checklist below).
3. **Create a GitHub Release** on your repository and attach the built
   `greekMathReader-1.1.5.nvda-addon` file. Copy the asset's download URL — it
   must start with `https://` and end with `.nvda-addon`.

## Issue form values

Use these values in the **Add-on registration** form:

| Field | Value |
|---|---|
| Add-on ID | `greekMathReader` |
| Add-on version | `1.1.5` |
| Channel | `stable` |
| Display name | `Greek Math Reader` |
| Publisher | `Bouronikos Christos` |
| Homepage | `https://github.com/chrisbouronikos/NVDA-Greek-Math` |
| Source URL | `https://github.com/chrisbouronikos/NVDA-Greek-Math` |
| Download URL | GitHub release asset URL ending in `.nvda-addon` |
| Minimum NVDA version | `2024.1.0` |
| Last tested NVDA version | `2026.1.1` |
| License | `GPL v2` |
| License URL | `https://www.gnu.org/licenses/old-licenses/gpl-2.0.html` |
| SHA256 | `4ce245b0a16018667b3b79889b73550358ceb3ce89b80e9ce2d366b61aa8dd73` |

## Submission steps

1. Go to <https://github.com/nvaccess/addon-datastore/issues/new/choose> and
   pick the **add-on registration** issue form.
2. Fill in the form: the `.nvda-addon` download URL, channel = **stable**, and
   the license (GPL v2).
3. Automation generates the metadata from your form + the add-on's manifest and
   opens a pull request. Validation errors (if any) are commented on the PR —
   fix and resubmit.
4. The add-on is scanned by VirusTotal and CodeQL automatically.
5. Because this is a **first submission**, NV Access staff manually approve it;
   allow **up to 2 weeks**. Later version updates skip this step.

## What the automated validation checks (already satisfied by this project)

* `name` = `greekMathReader` — letters/numbers only ✔
* `version` `major.minor.patch` ✔ (`1.1.5`)
* `minimumNVDAVersion` = 2024.1.0 and `lastTestedNVDAVersion` = 2026.1.1 —
  both real NVDA API versions ✔
* All URLs are HTTPS ✔
* Download URL ends in `.nvda-addon` (ensure this when creating the release)

## Pre-submission test checklist (on Windows + NVDA)

- [ ] Install the `.nvda-addon` file in NVDA 2024.1 (oldest supported) and the
      current stable NVDA 2026.1.1 — no errors in the NVDA log on startup.
- [ ] Browse to Wikipedia's Greek article «Τετραγωνική εξίσωση» (or any MathML
      page) in Firefox/Chrome — equations read in Greek in browse mode.
- [ ] NVDA+Alt+M on the quadratic formula — interaction opens; arrows navigate
      numerator/denominator/root; Escape exits.
- [ ] Settings → Greek Math Reader — change verbosity; equation reading changes
      accordingly.
- [ ] NVDA+Alt+G repairs and reasserts exclusive Greek reading.
- [ ] With NVDA UI language set to Greek, the settings panel and messages
      appear in Greek.
- [ ] In NVDA 2026.1.1 specifically: disable the add-on and confirm math reading
      falls back to built-in MathCAT (English).

## Release updates later

Bump `addon_version` in `buildVars.py`, update the changelog string, rebuild,
create a new GitHub release, and submit the new URL through the same issue
form. Updates are processed without manual review.
