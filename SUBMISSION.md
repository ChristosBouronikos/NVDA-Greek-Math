# Submitting Greek Math Reader to the NVDA Add-on Store

This checklist follows the current official [NVDA Add-on Store submission
guide](https://github.com/nvaccess/addon-datastore/blob/master/docs/submitters/submissionGuide.md)
and its [Add-on registration issue
form](https://github.com/nvaccess/addon-datastore/issues/new?template=registerAddon.yml).

The registration issue must be opened by the maintainer's GitHub account. For a
new add-on, NV Access approves that account as a publisher for this add-on ID;
the official guide asks maintainers to allow up to two weeks. Submitting the
issue generates the Store pull request automatically.

## Release metadata

| Field | Value |
|---|---|
| Add-on ID / manifest name | `greekMathReader` |
| Version | `2.0.0` |
| Display name / manifest summary | `Greek Math Reader` |
| Publisher | `Bouronikos Christos` |
| Source and homepage | `https://github.com/ChristosBouronikos/NVDA-Greek-Math` |
| Minimum NVDA API version | `2024.1.0` |
| Last tested NVDA API version | `2026.1.1` |
| Channel | `stable` |
| License name | `GPL-2.0-only` |
| License URL | `https://www.gnu.org/licenses/old-licenses/gpl-2.0.html` |

NVDA 2026.1.1 is listed as a stable, non-experimental API version in the Store's
current `nvdaAPIVersions.json`, so the stable channel is appropriate.

## Before creating the Store issue

1. Merge the repository pull request containing version 2.0.0.
2. Complete the Windows/NVDA checks below and record the tested versions.
3. Create and push tag `v2.0.0`. The release workflow builds the package, runs
   tests, creates the GitHub Release, and attaches both the `.nvda-addon` file
   and `sha256.txt`.
4. Confirm that this permanent direct URL downloads the release asset and ends
   in `.nvda-addon`:

   `https://github.com/ChristosBouronikos/NVDA-Greek-Math/releases/download/v2.0.0/greekMathReader-2.0.0.nvda-addon`

5. Confirm the package manifest matches the values above and the package
   contains `COPYING.txt`, English/Greek HTML help, compiled Greek translations,
   and only the required `globalPlugins/greekMathReader` package. In particular,
   the source tree intentionally has no checked-in generated `addon/manifest.ini`
   and no unused `globalPlugins/__init__.py` or `appModules/__init__.py` files.

## Add-on registration issue values

Open the [Add-on registration
form](https://github.com/nvaccess/addon-datastore/issues/new?template=registerAddon.yml)
and enter:

| Issue-form field | Value |
|---|---|
| Download URL | `https://github.com/ChristosBouronikos/NVDA-Greek-Math/releases/download/v2.0.0/greekMathReader-2.0.0.nvda-addon` |
| Source URL | `https://github.com/ChristosBouronikos/NVDA-Greek-Math` |
| Publisher | `Bouronikos Christos` |
| Channel | `stable` |
| License Name | `GPL-2.0-only` |
| License URL | `https://www.gnu.org/licenses/old-licenses/gpl-2.0.html` |

Suggested issue title suffix: `Greek Math Reader 2.0.0`.

## Suggested submission text

The registration form is primarily a set of structured fields. If a short
introduction is useful in a follow-up comment or during review, the following
text is ready to use:

> Hello NVDA Add-on Store team,
>
> I would kindly like to submit Greek Math Reader 2.0.0 for inclusion in the
> NVDA Add-on Store. Greek Math Reader helps Greek-speaking blind and visually
> impaired users access mathematical content in natural Greek. It supports
> MathML on webpages and in EPUB books, modern Microsoft Word equations, and
> selected or copied LaTeX. It also provides interactive navigation so users
> can explore an expression one part at a time.
>
> The repository includes English and Greek documentation, automated tests,
> release metadata, and the GPL-2.0-only license. Artificial intelligence tools
> were used in the development and documentation of the repository and add-on.
> The add-on is developed and maintained by Bouronikos Christos
> (chrisbouronikos@gmail.com).
>
> Thank you very much for your time and for maintaining the NVDA Add-on Store.
> I appreciate your review and welcome any feedback or requested improvements.

After submission, the Store automation creates a pull request and validates the
download URL, package manifest, unique add-on ID, versions, URLs, SHA256, and
VirusTotal result. If validation fails, correct the release or manifest and
submit the form again as directed by the automation.

## Windows and NVDA pre-release checks

- [ ] Install `greekMathReader-2.0.0.nvda-addon` in NVDA 2024.1, the oldest
      declared version; restart NVDA and check the log for errors.
- [ ] Install it in NVDA 2026.1.1, the last tested version; restart NVDA and
      check the log for errors.
- [ ] Confirm `NVDA+Alt+Shift+G` speaks «χι στο τετράγωνο συν 1» with a Greek
      voice and `NVDA+Alt+G` repairs provider routing.
- [ ] Verify MathML on a web page and in an EPUB document.
- [ ] Verify modern Word `.docx` OMath with character/word navigation, current
      line, selection, Say All, typing, and interactive navigation.
- [ ] Verify `NVDA+Alt+L` with selected and clipboard LaTeX, including the
      double-press interactive mode.
- [ ] Verify terse, smart, and verbose modes; decimal comma; settings reset;
      and Copy diagnostics.
- [ ] Verify the installed help opens in English and Greek and contains the
      author, email, GitHub, donation, and license information.
- [ ] Disable or uninstall the add-on and confirm NVDA's previous math speech
      and interaction providers are restored.

## Later updates

For each release, bump `addon_version` and the changelog in `buildVars.py`, add
the matching `CHANGELOG.md` entry, run all checks, merge the repository pull
request, create the version tag and GitHub Release, then submit the new permanent
asset URL through the same Add-on registration form. Once the publisher is
approved for `greekMathReader`, later versions normally skip manual publisher
approval.
