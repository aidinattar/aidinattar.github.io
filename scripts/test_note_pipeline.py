#!/usr/bin/env python3
"""Tests for Pages CMS -> Franklin note normalization and image checks."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import normalize_notes as normalizer


class NotePipelineTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.notes = self.root / 'notes'
        self.assets = self.root / '_assets'
        self.notes.mkdir()
        self.assets.mkdir()
        self.patches = [
            patch.object(normalizer, 'ROOT', self.root),
            patch.object(normalizer, 'NOTES', self.notes),
            patch.object(normalizer, 'ASSETS', self.assets),
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def test_pages_cms_literal_strings_and_arrays_and_latex_are_preserved(self):
        note = self.notes / 'test.md'
        body = (r'Formula: $x_t = w_{t+1}$' + '\n' +
                '```julia\nprintln("Don\'t change this")\n```\n')
        note.write_text("+++\ntitle = 'John note'\n" +
                        "description = 'Using \"quoted\" strings'\n" +
                        "topics = ['Neural learning', 'Local balance']\n" +
                        "order = 2.0\npublished = true\n+++\n" + body)
        meta, changed = normalizer.normalize_one(note)
        self.assertTrue(changed)
        rendered = note.read_text()
        self.assertIn('title = "John note"', rendered)
        self.assertIn('topics = ["Neural learning", "Local balance"]', rendered)
        self.assertTrue(rendered.endswith(body))
        self.assertEqual(meta['order'], 2.0)
        self.assertEqual(normalizer.normalize_one(note)[1], False)

    def test_dollar_is_safe_for_julia_and_valid_for_toml(self):
        note = self.notes / 'dollar.md'
        note.write_text("+++\ntitle = 'Cost $L_2$'\n+++\nbody\n")
        normalizer.normalize_one(note)
        self.assertIn(r'Cost \u0024L_2\u0024', note.read_text())
        meta, _, _ = normalizer.read_note(note)
        self.assertEqual(meta['title'], 'Cost $L_2$')
        self.assertFalse(normalizer.normalize_one(note)[1])

    def test_repair_unambiguous_body_asset_path(self):
        file = self.assets / 'plot.png'
        file.write_bytes(b'img')
        note = self.notes / 'broken.md'
        note.write_text("+++\ntitle = 'Plot'\nimage = '/assets/plot.png'\n+++\n"
                        '<img src="/assets/notes/broken/plot.png" alt="plot">\n')
        with self.assertRaisesRegex(ValueError, 'missing image'):
            normalizer.normalize_one(note)
        _, changed = normalizer.normalize_one(note, repair_image_paths=True)
        self.assertTrue(changed)
        self.assertIn('src="/assets/plot.png"', note.read_text())
        self.assertFalse(normalizer.normalize_one(note)[1])

    def test_unrepairable_asset_fails_build(self):
        note = self.notes / 'missing.md'
        note.write_text("+++\ntitle = 'Plot'\nimage = '/assets/not-uploaded.png'\n+++\nBody\n")
        with self.assertRaisesRegex(ValueError, 'missing image'):
            normalizer.normalize_one(note, repair_image_paths=True)

    def test_unpublished_draft_may_lack_assets(self):
        note = self.notes / 'draft.md'
        note.write_text("+++\ntitle = 'Draft'\npublished = false\nimage = '/assets/not-yet.png'\n+++\nBody\n")
        normalizer.normalize_one(note)
        self.assertIn('published = false', note.read_text())

    def test_cms_raw_html_intro_is_wrapped_and_idempotent(self):
        note = self.notes / 'intro.md'
        body = ("<section class=\"page-intro note-intro\">\n"
                "  <h1>Title</h1>\n"
                "  <div class=\"chip-list\"><span>Tag</span></div>\n"
                "</section>\n\n"
                "An equation $w_t$ and an image below.\n\n"
                "$$\n\\alpha + \\beta\n$$\n")
        note.write_text("+++\ntitle = 'A note'\npublished = true\n+++\n" + body)
        meta, changed = normalizer.normalize_one(note)
        self.assertTrue(changed)
        actual = note.read_text()
        self.assertIn("~~~\n<section class=\"page-intro note-intro\">", actual)
        self.assertIn("</section>\n~~~\n\nAn equation $w_t$", actual)
        self.assertIn("$$\n\\alpha + \\beta\n$$", actual)
        self.assertFalse(normalizer.normalize_one(note)[1])

    def test_existing_html_fences_and_code_blocks_are_unchanged(self):
        body = ("~~~\n<section><h1>Existing</h1></section>\n~~~\n"
                "\n```html\n<section><h1>Code sample</h1></section>\n```\n"
                "\n~~~\n<figure><img src=\"/assets/a.png\"></figure>\n~~~\n")
        self.assertEqual(normalizer.wrap_unfenced_html(body), body)

    def test_bad_unclosed_html_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Unclosed raw HTML'):
            normalizer.wrap_unfenced_html("<section>\nUnclosed\n")

    def test_raw_figure_html_is_wrapped(self):
        src = '<figure class="note-figure">\n<img src="/assets/img.png">\n</figure>\n'
        self.assertEqual(normalizer.wrap_unfenced_html(src), '~~~\n' + src + '~~~\n')

    def test_invalid_unquoted_date_fails_loudly(self):
        note = self.notes / 'date.md'
        note.write_text('+++\ntitle = "Date"\ndate = 2026-10-10\n+++\nBody\n')
        with self.assertRaisesRegex(ValueError, 'unquoted TOML dates'):
            normalizer.normalize_one(note)

if __name__ == '__main__':
    unittest.main()
