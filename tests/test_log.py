"""Tests for agent/log.py - Logging utilities."""

import pytest
import re
from pathlib import Path
from agent.log import _init_log_dir, _format_plan
from agent.plan import Plan, PlanStep, StepVariable


class TestInitLogDir:
    """Test _init_log_dir function."""

    def test_init_log_dir_creates_directory(self, monkeypatch, tmp_path):
        """Test that _init_log_dir creates a directory."""
        # Mock the base path to use tmp_path
        import agent.log
        original_file = agent.log.__file__

        # Create a mock __file__ path
        mock_agent_dir = tmp_path / "agent"
        mock_agent_dir.mkdir()
        monkeypatch.setattr("agent.log.__file__", str(mock_agent_dir / "log.py"))

        log_dir = _init_log_dir()

        assert log_dir.exists()
        assert log_dir.is_dir()

        # Restore
        monkeypatch.setattr("agent.log.__file__", original_file)

    def test_init_log_dir_returns_path_object(self, monkeypatch, tmp_path):
        """Test that _init_log_dir returns a Path object."""
        import agent.log
        original_file = agent.log.__file__

        mock_agent_dir = tmp_path / "agent"
        mock_agent_dir.mkdir()
        monkeypatch.setattr("agent.log.__file__", str(mock_agent_dir / "log.py"))

        log_dir = _init_log_dir()

        assert isinstance(log_dir, Path)

        monkeypatch.setattr("agent.log.__file__", original_file)

    def test_init_log_dir_creates_parent_dirs(self, monkeypatch, tmp_path):
        """Test that _init_log_dir creates parent directories."""
        import agent.log
        original_file = agent.log.__file__

        mock_agent_dir = tmp_path / "agent"
        mock_agent_dir.mkdir()
        monkeypatch.setattr("agent.log.__file__", str(mock_agent_dir / "log.py"))

        log_dir = _init_log_dir()

        # Check that logs directory was created
        logs_parent = log_dir.parent
        assert logs_parent.exists()
        assert logs_parent.name == "logs"

        monkeypatch.setattr("agent.log.__file__", original_file)

    def test_init_log_dir_timestamp_format(self, monkeypatch, tmp_path):
        """Test that directory name follows YYYYMMDD_HHMMSS format."""
        import agent.log
        original_file = agent.log.__file__

        mock_agent_dir = tmp_path / "agent"
        mock_agent_dir.mkdir()
        monkeypatch.setattr("agent.log.__file__", str(mock_agent_dir / "log.py"))

        log_dir = _init_log_dir()

        # Check timestamp format: YYYYMMDD_HHMMSS
        timestamp_pattern = r'^\d{8}_\d{6}$'
        assert re.match(timestamp_pattern, log_dir.name)

        monkeypatch.setattr("agent.log.__file__", original_file)


class TestFormatPlan:
    """Test _format_plan function."""

    def test_format_plan_empty(self):
        """Test formatting empty plan."""
        plan = Plan(steps=[])
        result = _format_plan(plan)

        assert result == ""

    def test_format_plan_single_step(self):
        """Test formatting plan with single step."""
        step = PlanStep(
            step_description="Do something",
            input_variables=[],
            output_variables=[]
        )
        plan = Plan(steps=[step])
        result = _format_plan(plan)

        assert "Step 1: Do something" in result
        assert "-" * 80 in result  # Check for separator
        assert "input_variables" in result
        assert "output_variables" in result

    def test_format_plan_custom_start_step(self):
        """Test formatting with custom start_step number."""
        step1 = PlanStep(
            step_description="First task",
            input_variables=[],
            output_variables=[]
        )
        step2 = PlanStep(
            step_description="Second task",
            input_variables=[],
            output_variables=[]
        )
        plan = Plan(steps=[step1, step2])
        result = _format_plan(plan, start_step=5)

        assert "Step 5: First task" in result
        assert "Step 6: Second task" in result

    def test_format_plan_with_variables(self):
        """Test formatting plan with input and output variables."""
        input_var = StepVariable(
            variable_name="x",
            variable_description="Input",
            variable_data_type="int"
        )
        output_var = StepVariable(
            variable_name="y",
            variable_description="Output",
            variable_data_type="str"
        )
        step = PlanStep(
            step_description="Transform",
            input_variables=[input_var],
            output_variables=[output_var]
        )
        plan = Plan(steps=[step])
        result = _format_plan(plan)

        # Variables should be JSON formatted
        assert "input_variables" in result
        assert "output_variables" in result
        # Check that JSON structure is present
        assert "{" in result or "[" in result

    def test_format_plan_multiple_steps(self):
        """Test formatting plan with multiple steps."""
        step1 = PlanStep(
            step_description="Step one",
            input_variables=[],
            output_variables=[]
        )
        step2 = PlanStep(
            step_description="Step two",
            input_variables=[],
            output_variables=[]
        )
        step3 = PlanStep(
            step_description="Step three",
            input_variables=[],
            output_variables=[]
        )
        plan = Plan(steps=[step1, step2, step3])
        result = _format_plan(plan)

        assert "Step 1: Step one" in result
        assert "Step 2: Step two" in result
        assert "Step 3: Step three" in result
        # Check that separators are present
        assert result.count("-" * 80) >= 6  # At least 2 separators per step
