import subprocess
import tempfile
import unittest
from pathlib import Path

from nightshift_sloth import gitops


def sh(cwd, *argv):
    subprocess.run(argv, cwd=cwd, check=True, capture_output=True)


class GitopsTest(unittest.TestCase):
    def test_worktree_commit_never_touches_main(self):
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d) / "repo"
            repo.mkdir()
            sh(repo, "git", "init", "-q", "-b", "main")
            (repo / "a.txt").write_text("one\n")
            sh(repo, "git", "add", ".")
            sh(repo, "git", "-c", "user.name=t", "-c", "user.email=t@localhost", "commit", "-qm", "init")
            main_sha = gitops.rev(repo, "main")

            wt = Path(d) / "wt"
            gitops.exclude_backboard_dir(repo)
            gitops.add_worktree(repo, wt, "sloth/chore/1-model", main_sha)
            (wt / "a.txt").write_text("two\n")
            (wt / ".backboard").mkdir()
            (wt / ".backboard" / "session.json").write_text("{}")
            sha = gitops.commit_all(wt, "sloth: chore")

            self.assertIsNotNone(sha)
            self.assertEqual(gitops.rev(repo, "main"), main_sha)
            self.assertEqual((repo / "a.txt").read_text(), "one\n")
            self.assertEqual(gitops.numstat(wt, main_sha), (1, 1, 1))  # .backboard/ is excluded
            self.assertEqual(gitops.sloth_branches(repo), ["sloth/chore/1-model"])
            gitops.remove_worktree(repo, wt)
            self.assertIsNone(gitops.commit_all(repo, "nothing to commit"))


if __name__ == "__main__":
    unittest.main()
