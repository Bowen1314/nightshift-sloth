import unittest

from nightshift_sloth import chores

SAMPLE = """---
test: python3 -m unittest discover -s tests
timer: 300
---
# Chores

- [x] done-already: this one is finished
- [ ] fix-thing: the thing is broken
  and the description continues here
- [ ] **bold-id** — dash separators work too

Some trailing prose.
"""


class ChoresTest(unittest.TestCase):
    def test_front_matter(self):
        cf = chores.parse(SAMPLE)
        self.assertEqual(cf.test_command, "python3 -m unittest discover -s tests")
        self.assertEqual(cf.timer, 300)

    def test_items_and_continuations(self):
        cf = chores.parse(SAMPLE)
        self.assertEqual([c.id for c in cf.chores], ["done-already", "fix-thing", "bold-id"])
        self.assertTrue(cf.chores[0].done)
        self.assertIn("continues here", cf.get("fix-thing").text)

    def test_next_open_skips_done_and_attempted(self):
        cf = chores.parse(SAMPLE)
        self.assertEqual(cf.next_open(set()).id, "fix-thing")
        attempted = chores.attempted(["sloth/fix-thing/20261024-0230-deepseek", "main", "feature/x"])
        self.assertEqual(attempted, {"fix-thing"})
        self.assertEqual(cf.next_open(attempted).id, "bold-id")
        self.assertIsNone(cf.next_open({"fix-thing", "bold-id"}))


if __name__ == "__main__":
    unittest.main()
