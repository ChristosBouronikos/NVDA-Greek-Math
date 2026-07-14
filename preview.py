#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: GPL-2.0-only
# Project contact: Bouronikos Christos <chrisbouronikos@gmail.com>
# GitHub: https://github.com/ChristosBouronikos
# Author / maintainer: Christos Bouronikos  ·  chrisbouronikos@gmail.com
# Greek Math Reader is free, open-source software. If it helps make
# mathematics more accessible for you, please consider a kind, optional
# donation — it directly supports continued development. Thank you!
#   PayPal: https://paypal.me/christosbouronikos
"""Δοκιμή της ελληνικής εκφώνησης χωρίς NVDA.

Χρήση:
	python3 preview.py '<math><msup><mi>x</mi><mn>2</mn></msup></math>'
	python3 preview.py path/to/expression.xml
	python3 preview.py            # διαδραστικά: επικολλήστε MathML, Ctrl+D για τέλος
	python3 preview.py --demo     # έτοιμα παραδείγματα

Τυπώνει την εκφώνηση και στα τρία επίπεδα λεπτομέρειας.
Σε macOS μπορείτε να την ακούσετε:  python3 preview.py --demo --say
"""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "addon" / "globalPlugins" / "greekMathReader"))

from engine import ReadingConfig, SMART, TERSE, VERBOSE, speak_mathml, tokens_to_text  # noqa: E402

LEVELS = [("Σύντομη ", TERSE), ("Έξυπνη  ", SMART), ("Αναλυτική", VERBOSE)]

DEMOS = [
	("Τετραγωνική εξίσωση", """
		<math><mi>x</mi><mo>=</mo><mfrac>
		<mrow><mo>−</mo><mi>b</mi><mo>±</mo><msqrt><msup><mi>b</mi><mn>2</mn></msup>
		<mo>−</mo><mn>4</mn><mo>&#x2062;</mo><mi>a</mi><mo>&#x2062;</mo><mi>c</mi></msqrt></mrow>
		<mrow><mn>2</mn><mo>&#x2062;</mo><mi>a</mi></mrow></mfrac></math>"""),
	("Ολοκλήρωμα", """
		<math><msubsup><mo>∫</mo><mn>0</mn><mi>π</mi></msubsup>
		<mi>sin</mi><mo>&#x2061;</mo><mi>x</mi><mi>d</mi><mi>x</mi>
		<mo>=</mo><mn>2</mn></math>"""),
	("Σειρά (πρόβλημα της Βασιλείας)", """
		<math><munderover><mo>∑</mo><mrow><mi>n</mi><mo>=</mo><mn>1</mn></mrow><mi>∞</mi></munderover>
		<mfrac><mn>1</mn><msup><mi>n</mi><mn>2</mn></msup></mfrac>
		<mo>=</mo><mfrac><msup><mi>π</mi><mn>2</mn></msup><mn>6</mn></mfrac></math>"""),
	("Όριο", """
		<math><munder><mi>lim</mi><mrow><mi>x</mi><mo>→</mo><mn>0</mn></mrow></munder>
		<mfrac><mrow><mi>sin</mi><mo>&#x2061;</mo><mi>x</mi></mrow><mi>x</mi></mfrac>
		<mo>=</mo><mn>1</mn></math>"""),
	("Πίνακας", """
		<math><mi>A</mi><mo>=</mo><mrow><mo>(</mo><mtable>
		<mtr><mtd><mn>1</mn></mtd><mtd><mn>2</mn></mtd></mtr>
		<mtr><mtd><mn>3</mn></mtd><mtd><mn>4</mn></mtd></mtr>
		</mtable><mo>)</mo></mrow></math>"""),
	("Σύστημα εξισώσεων", """
		<math><mrow><mo>{</mo><mtable>
		<mtr><mtd><mrow><mi>x</mi><mo>+</mo><mi>y</mi><mo>=</mo><mn>3</mn></mrow></mtd></mtr>
		<mtr><mtd><mrow><mi>x</mi><mo>−</mo><mi>y</mi><mo>=</mo><mn>1</mn></mrow></mtd></mtr>
		</mtable></mrow></math>"""),
	("Παράγωγος", """
		<math><mfrac><mrow><mi>d</mi><mi>y</mi></mrow><mrow><mi>d</mi><mi>x</mi></mrow></mfrac>
		<mo>=</mo><mn>2</mn><mo>&#x2062;</mo><mi>x</mi></math>"""),
	("Πυθαγόρειο θεώρημα", """
		<math><msup><mi>α</mi><mn>2</mn></msup><mo>+</mo><msup><mi>β</mi><mn>2</mn></msup>
		<mo>=</mo><msup><mi>γ</mi><mn>2</mn></msup></math>"""),
]


def show(title, mathml, say=False):
	print(f"\n▶ {title}")
	for label, level in LEVELS:
		text = tokens_to_text(speak_mathml(mathml, ReadingConfig(verbosity=level)))
		print(f"   {label}: {text}")
	if say:
		text = tokens_to_text(speak_mathml(mathml, ReadingConfig(verbosity=SMART)))
		subprocess.run(["say", "-v", "Melina", text], check=False)


def main():
	args = [a for a in sys.argv[1:]]
	say = "--say" in args
	args = [a for a in args if a != "--say"]
	if "--demo" in args:
		for title, mathml in DEMOS:
			show(title, mathml, say=say)
		return
	if args:
		source = args[0]
		mathml = Path(source).read_text(encoding="utf-8") if Path(source).exists() else source
	else:
		print("Επικολλήστε MathML και πατήστε Ctrl+D:")
		mathml = sys.stdin.read()
	show("Παράσταση", mathml, say=say)


if __name__ == "__main__":
	main()
