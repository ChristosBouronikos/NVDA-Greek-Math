#!/usr/bin/env python3
"""Dependency-free builder for the Greek Math Reader NVDA add-on.

Produces greekMathReader-<version>.nvda-addon without requiring SCons.
The SCons build (sconstruct) remains the canonical build for CI/releases;
this script is a convenience for local development on any OS.

Steps:
  1. Generate addon/manifest.ini from manifest.ini.tpl + buildVars.py
  2. Compile addon/locale/*/LC_MESSAGES/nvda.po to nvda.mo
  3. Generate translated manifests (locale/<lang>/manifest.ini)
  4. Convert addon/doc/*/readme.md to readme.html
  5. Zip the addon directory into the .nvda-addon package

Usage: python3 build.py
"""

import gettext
import html
import re
import shutil
import struct
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
ADDON = ROOT / "addon"

sys.path.insert(0, str(ROOT))

# buildVars.py imports helper types from site_scons, whose package __init__
# requires SCons. Stub just those two modules so buildVars loads without SCons.
import types  # noqa: E402

_typings = types.ModuleType("site_scons.site_tools.NVDATool.typings")
_typings.AddonInfo = dict
_typings.BrailleTables = dict
_typings.SymbolDictionaries = dict
_utils = types.ModuleType("site_scons.site_tools.NVDATool.utils")
_utils._ = lambda s: s
for _name in ("site_scons", "site_scons.site_tools", "site_scons.site_tools.NVDATool"):
	sys.modules.setdefault(_name, types.ModuleType(_name))
sys.modules["site_scons.site_tools.NVDATool.typings"] = _typings
sys.modules["site_scons.site_tools.NVDATool.utils"] = _utils

import buildVars  # noqa: E402


def generate_manifest() -> None:
	template = (ROOT / "manifest.ini.tpl").read_text(encoding="utf-8")
	manifest = template.format(**buildVars.addon_info)
	(ADDON / "manifest.ini").write_text(manifest, encoding="utf-8")
	print("generated addon/manifest.ini")


def compile_po(po_path: Path, mo_path: Path) -> None:
	"""Compile a .po file to .mo, via msgfmt if available, else a minimal pure-Python fallback."""
	msgfmt = shutil.which("msgfmt")
	if msgfmt:
		subprocess.run([msgfmt, "-o", str(mo_path), str(po_path)], check=True)
		return
	# Minimal .po parser: handles msgid/msgstr with multi-line strings; skips fuzzy/untranslated.
	catalog: dict[str, str] = {}
	msgid: list[str] | None = None
	msgstr: list[str] | None = None
	current: list[str] | None = None
	fuzzy = False

	def flush() -> None:
		nonlocal msgid, msgstr, fuzzy
		if msgid is not None and msgstr is not None and not fuzzy:
			key, val = "".join(msgid), "".join(msgstr)
			if val:
				catalog[key] = val
		msgid = msgstr = None
		fuzzy = False

	for line in po_path.read_text(encoding="utf-8").splitlines():
		line = line.strip()
		if line.startswith("#"):
			if line.startswith("#,") and "fuzzy" in line:
				fuzzy = True
			continue
		if line.startswith("msgid "):
			flush()
			msgid = [eval_po_string(line[6:])]
			current = msgid
		elif line.startswith("msgstr "):
			msgstr = [eval_po_string(line[7:])]
			current = msgstr
		elif line.startswith('"') and current is not None:
			current.append(eval_po_string(line))
	flush()
	write_mo(mo_path, catalog)


def eval_po_string(s: str) -> str:
	s = s.strip()
	if not (s.startswith('"') and s.endswith('"')):
		return ""
	body = s[1:-1]
	return (
		body.replace('\\"', '"')
		.replace("\\n", "\n")
		.replace("\\t", "\t")
		.replace("\\\\", "\\")
	)


def write_mo(mo_path: Path, catalog: dict[str, str]) -> None:
	"""Write a GNU gettext .mo file (little-endian) from a msgid->msgstr dict."""
	keys = sorted(catalog.keys())
	offsets = []
	ids = b""
	strs = b""
	for key in keys:
		id_b = key.encode("utf-8")
		str_b = catalog[key].encode("utf-8")
		offsets.append((len(ids), len(id_b), len(strs), len(str_b)))
		ids += id_b + b"\x00"
		strs += str_b + b"\x00"
	n = len(keys)
	keystart = 7 * 4 + 16 * n
	valuestart = keystart + len(ids)
	koffsets = []
	voffsets = []
	for o1, l1, o2, l2 in offsets:
		koffsets += [l1, o1 + keystart]
		voffsets += [l2, o2 + valuestart]
	output = struct.pack("Iiiiiii", 0x950412DE, 0, n, 7 * 4, 7 * 4 + n * 8, 0, 0)
	output += struct.pack(f"<{len(koffsets)}i", *koffsets)
	output += struct.pack(f"<{len(voffsets)}i", *voffsets)
	output += ids + strs
	mo_path.write_bytes(output)


def compile_translations() -> None:
	for po in sorted(ADDON.glob("locale/*/LC_MESSAGES/nvda.po")):
		mo = po.with_suffix(".mo")
		compile_po(po, mo)
		print(f"compiled {po.relative_to(ROOT)}")
		lang_dir = po.parent.parent
		generate_translated_manifest(mo, lang_dir / "manifest.ini")


def generate_translated_manifest(mo_path: Path, dest: Path) -> None:
	with open(mo_path, "rb") as f:
		_ = gettext.GNUTranslations(f).gettext
	vars_ = {
		var: _(buildVars.addon_info[var])
		for var in ("addon_summary", "addon_description", "addon_changelog")
	}
	template = (ROOT / "manifest-translated.ini.tpl").read_text(encoding="utf-8")
	dest.write_text(template.format(**vars_), encoding="utf-8")
	print(f"generated {dest.relative_to(ROOT)}")


def md_to_html(md: str, title: str) -> str:
	"""Tiny Markdown-to-HTML conversion: headings, lists, code spans, paragraphs, links, tables."""
	try:
		import markdown  # type: ignore

		body = markdown.markdown(md, extensions=buildVars.markdownExtensions)
	except ImportError:
		body = _mini_markdown(md)
	return (
		"<!DOCTYPE html>\n<html>\n<head>\n<meta charset=\"utf-8\"/>\n"
		f"<title>{html.escape(title)}</title>\n</head>\n<body>\n{body}\n</body>\n</html>\n"
	)


def _mini_markdown(md: str) -> str:
	out: list[str] = []
	in_list = False
	in_table = False
	for line in md.splitlines():
		stripped = line.strip()
		if in_list and not stripped.startswith(("* ", "- ")):
			out.append("</ul>")
			in_list = False
		if in_table and not stripped.startswith("|"):
			out.append("</table>")
			in_table = False
		if not stripped:
			continue
		m = re.match(r"^(#{1,6})\s+(.*)$", stripped)
		if m:
			level = len(m.group(1))
			out.append(f"<h{level}>{_inline(m.group(2))}</h{level}>")
		elif stripped.startswith(("* ", "- ")):
			if not in_list:
				out.append("<ul>")
				in_list = True
			out.append(f"<li>{_inline(stripped[2:])}</li>")
		elif stripped.startswith("|"):
			cells = [c.strip() for c in stripped.strip("|").split("|")]
			if all(re.fullmatch(r":?-+:?", c) for c in cells):
				continue
			if not in_table:
				out.append("<table>")
				in_table = True
			out.append("<tr>" + "".join(f"<td>{_inline(c)}</td>" for c in cells) + "</tr>")
		else:
			out.append(f"<p>{_inline(stripped)}</p>")
	if in_list:
		out.append("</ul>")
	if in_table:
		out.append("</table>")
	return "\n".join(out)


def _inline(text: str) -> str:
	text = html.escape(text)
	text = re.sub(r"`([^`]+)`", r"<code>\1</code>", text)
	text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", text)
	text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)
	return text


def build_docs() -> None:
	for md_file in sorted(ADDON.glob("doc/*/readme.md")):
		html_file = md_file.with_suffix(".html")
		html_file.write_text(
			md_to_html(md_file.read_text(encoding="utf-8"), buildVars.addon_info["addon_summary"]),
			encoding="utf-8",
		)
		print(f"generated {html_file.relative_to(ROOT)}")


def package() -> Path:
	version = buildVars.addon_info["addon_version"]
	name = buildVars.addon_info["addon_name"]
	out = ROOT / f"{name}-{version}.nvda-addon"
	excluded_suffixes = {".po", ".pot"}
	with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
		for path in sorted(ADDON.rglob("*")):
			if path.is_dir() or path.suffix in excluded_suffixes:
				continue
			if "__pycache__" in path.parts:
				continue
			zf.write(path, path.relative_to(ADDON))
	print(f"\npackaged: {out.name} ({out.stat().st_size // 1024} KB)")
	return out


if __name__ == "__main__":
	generate_manifest()
	compile_translations()
	build_docs()
	package()
