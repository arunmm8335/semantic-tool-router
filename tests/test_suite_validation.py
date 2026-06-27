from __future__ import annotations

import sys
import unittest
from pathlib import Path

from semantic_tool_router.agent_eval import RankOneSelector, run_live_agent_eval
from semantic_tool_router.live_benchmark import LiveServerCase, LiveTask
from semantic_tool_router.suite_validation import validate_live_suite


class SuiteValidationTests(unittest.TestCase):
    def test_validate_fake_server_suite(self) -> None:
        fake_server = Path(__file__).resolve().parent / "fixtures" / "fake_mcp_server.py"
        suite = Path(__file__).resolve().parent / "fixtures" / "fake_live_suite.json"
        suite.write_text(
            (
                '{"top_k": 1, "servers": [{"id": "fake", "command": ["'
                + str(sys.executable).replace("\\", "\\\\")
                + '", "'
                + str(fake_server).replace("\\", "\\\\")
                + '"], "tasks": [{"query": "read file", "expected_tools": ["read_text_file"]}]}]}'
            ),
            encoding="utf-8",
        )
        try:
            report = validate_live_suite(suite, ".", timeout=30.0)
            self.assertTrue(report.valid)
        finally:
            suite.unlink(missing_ok=True)

    def test_run_live_agent_eval_executes_tool(self) -> None:
        fake_server = Path(__file__).resolve().parent / "fixtures" / "fake_mcp_server.py"
        case = LiveServerCase(
            identifier="fake",
            command=(sys.executable, str(fake_server)),
            tasks=(
                LiveTask(
                    query="read a local text file",
                    expected_tools=("read_text_file",),
                    execute_arguments={"path": "README.md"},
                ),
            ),
        )
        report, rows = run_live_agent_eval(
            (case,),
            top_k=1,
            selector=RankOneSelector(),
            selector_name="rank1",
            execute_tools=True,
            workspace=".",
        )
        self.assertEqual(report.execution_attempt_count, 1)
        self.assertTrue(rows[0]["execution_success"])
        self.assertEqual(report.end_to_end_execute_success_rate, 1.0)


if __name__ == "__main__":
    unittest.main()
