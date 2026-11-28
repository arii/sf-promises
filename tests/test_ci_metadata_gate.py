import importlib.util
from pathlib import Path
import subprocess
import unittest
import tempfile
import os
from unittest.mock import Mock

SPEC = importlib.util.spec_from_file_location('ci_gate', Path(__file__).resolve().parents[1] / 'scripts/ci_needs_tests.py')
GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GATE)


class TestCiMetadataGate(unittest.TestCase):
    def test_only_exact_funding_path_skips(self):
        self.assertFalse(GATE.needs_tests(['.github/FUNDING.yml']))
        for paths in [[], [''], ['docs/app.js'], ['docs/README.md'], ['tests/test_display_consistency.py'], ['requirements.txt'], ['.github/workflows/ci.yml'], ['.github/FUNDING.yml', 'docs/app.js'], ['.github/funding.yml']]:
            with self.subTest(paths=paths):
                self.assertTrue(GATE.needs_tests(paths))

    def test_unknown_and_new_branch_bases_run_tests_without_fetch(self):
        run = Mock()
        for base in [None, '', '0' * 40, 'invalid']:
            self.assertTrue(GATE.inspect_diff(base, 'b' * 40, run))
        run.assert_not_called()

    def test_fetch_or_diff_failure_runs_tests(self):
        for error in [subprocess.CalledProcessError(1, 'git'), subprocess.TimeoutExpired('git', 60), OSError('missing git')]:
            self.assertTrue(GATE.inspect_diff('a' * 40, 'b' * 40, Mock(side_effect=error)))

    def test_diff_paths_are_nul_delimited_and_renames_not_hidden(self):
        run = Mock(side_effect=[subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 0, stdout=b'.github/FUNDING.yml\0')])
        self.assertFalse(GATE.inspect_diff('a' * 40, 'b' * 40, run))
        self.assertIn('--no-renames', run.call_args.args[0])
        run = Mock(side_effect=[subprocess.CompletedProcess([], 0), subprocess.CompletedProcess([], 0, stdout=b'.github/FUNDING.yml\0docs/app.js\0')])
        self.assertTrue(GATE.inspect_diff('a' * 40, 'b' * 40, run))

    def test_workflow_keeps_required_job_and_all_application_gates(self):
        workflow = Path('.github/workflows/ci.yml').read_text()
        self.assertNotIn('paths-ignore:', workflow)
        self.assertIn('  test:\n', workflow)
        self.assertIn('cancel-in-progress: ${{ github.event_name == \'pull_request\' }}', workflow)
        self.assertEqual(workflow.count("if: steps.changes.outputs.run_tests != 'false'"), 5)
        for command in ['python-version: "3.11"', 'node -c docs/app.js', 'pytest tests/ -v --timeout=120', 'timeout-minutes: 10', 'PYTHONUNBUFFERED: "1"']:
            self.assertIn(command, workflow)

    def test_real_git_funding_and_site_diffs(self):
        with tempfile.TemporaryDirectory() as folder:
            repo = Path(folder) / 'origin'
            repo.mkdir()
            def git(*args):
                return subprocess.check_output(['git', '-C', str(repo), *args], stderr=subprocess.PIPE).decode().strip()
            git('init')
            git('config', 'user.email', 'test@example.invalid')
            git('config', 'user.name', 'CI gate test')
            (repo / 'app.py').write_text('print(1)')
            git('add', '.')
            git('commit', '-m', 'base')
            base = git('rev-parse', 'HEAD')
            (repo / '.github').mkdir()
            (repo / '.github/FUNDING.yml').write_text('github: example')
            git('add', '.')
            git('commit', '-m', 'funding')
            funding = git('rev-parse', 'HEAD')
            git('remote', 'add', 'origin', str(repo))
            previous = os.getcwd()
            try:
                os.chdir(repo)
                self.assertFalse(GATE.inspect_diff(base, funding))
                (repo / 'app.py').write_text('print(2)')
                git('add', '.')
                git('commit', '-m', 'code')
                self.assertTrue(GATE.inspect_diff(funding, git('rev-parse', 'HEAD')))
                self.assertTrue(GATE.inspect_diff(base, git('rev-parse', 'HEAD')))
            finally:
                os.chdir(previous)
