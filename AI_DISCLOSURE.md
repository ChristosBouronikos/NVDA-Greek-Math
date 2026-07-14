# AI assistance disclosure

Greek Math Reader was developed with AI-assisted tools. This disclosure is
provided for transparency to users, contributors, and NVDA Add-on Store
reviewers.

## Scope of assistance

AI-assisted tools contributed drafts or suggestions for:

* Python implementation and refactoring;
* automated tests and representative MathML/LaTeX cases;
* English and Greek documentation;
* build and GitHub Actions automation; and
* repository and Add-on Store submission preparation.

No AI model is included in the add-on and the add-on does not send user data to
an AI service. It runs locally using deterministic Python code.

## Human direction and review

The author and maintainer, **Bouronikos Christos**, supplied the accessibility
goal, Greek-language requirements, real NVDA and Microsoft Word observations,
diagnostic results, release decisions, and acceptance criteria. The maintainer
reviews proposed changes, decides which Greek mathematical readings are
appropriate, evaluates generated output, and remains responsible for releases.

The repository preserves reviewable evidence of that work:

* exact-wording tests capture the accepted Greek readings;
* corpus fixtures cover Word, MathJax, and MathType representations;
* `TERMINOLOGY_REVIEW.md` records terminology decisions still open to human
  review; and
* `CHANGELOG.md` records the user-reported problems and the changes made for
  each release.

AI output is treated as an untrusted draft: it must pass automated tests and
maintainer review before release. Windows-specific behavior must additionally
be tested with NVDA and the relevant application; cross-platform unit tests do
not substitute for that manual check.

## Contact

* Author / maintainer: Bouronikos Christos
* Email: [chrisbouronikos@gmail.com](mailto:chrisbouronikos@gmail.com)
* GitHub: [ChristosBouronikos](https://github.com/ChristosBouronikos)
* Optional donation: [PayPal](https://paypal.me/christosbouronikos)
