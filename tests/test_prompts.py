"""Tests for agent/prompt_agent.py - Prompt building functions."""

import pytest
from agent.prompt_agent import build_step_user_first_msg_prompt
from agent.plan import PlanStep, StepVariable


class TestBuildStepUserFirstMsgPrompt:
    """Test build_step_user_first_msg_prompt function."""

    def test_build_prompt_minimal(self):
        """Test building prompt with minimal inputs."""
        task = "Test task"
        current_step = PlanStep(
            step_description="Do X",
            input_variables=[],
            output_variables=[]
        )
        completed_steps = []

        result = build_step_user_first_msg_prompt(task, current_step, completed_steps)

        assert "Test task" in result
        assert "Do X" in result
        assert "CURRENT STEP" in result
        assert "Global Task" in result

    def test_build_prompt_with_completed_steps(self):
        """Test building prompt with completed steps."""
        task = "Main task"
        step1 = PlanStep(step_description="First step", input_variables=[], output_variables=[])
        step2 = PlanStep(step_description="Second step", input_variables=[], output_variables=[])
        completed_steps = [
            (step1, "result1"),
            (step2, "result2")
        ]
        current_step = PlanStep(
            step_description="Current task",
            input_variables=[],
            output_variables=[]
        )

        result = build_step_user_first_msg_prompt(task, current_step, completed_steps)

        assert "Previous Steps Completed" in result
        assert "Step 1" in result
        assert "First step" in result
        assert "Result:** result1" in result
        assert "Step 2" in result
        assert "Second step" in result
        assert "Result:** result2" in result

    def test_build_prompt_with_input_variables(self):
        """Test building prompt with input variables."""
        task = "Process data"
        input_var1 = StepVariable(
            variable_name="data",
            variable_description="Raw data to process",
            variable_data_type="list[str]"
        )
        input_var2 = StepVariable(
            variable_name="config",
            variable_description="Configuration settings",
            variable_data_type="dict"
        )
        current_step = PlanStep(
            step_description="Transform data",
            input_variables=[input_var1, input_var2],
            output_variables=[]
        )

        result = build_step_user_first_msg_prompt(task, current_step, [])

        assert "Input variables available" in result
        assert "data (list[str]): Raw data to process" in result
        assert "config (dict): Configuration settings" in result

    def test_build_prompt_with_output_variables(self):
        """Test building prompt with output variables."""
        task = "Generate report"
        output_var = StepVariable(
            variable_name="report",
            variable_description="Generated report",
            variable_data_type="str"
        )
        current_step = PlanStep(
            step_description="Create report",
            input_variables=[],
            output_variables=[output_var]
        )

        result = build_step_user_first_msg_prompt(task, current_step, [])

        assert "Output variables required" in result
        assert "report (str): Generated report" in result

    def test_build_prompt_dict_variables(self):
        """Test building prompt when variables are provided as dicts."""
        task = "Test dict variables"
        # Simulate dict-style variables (as seen in the code at lines 184-186)
        current_step = PlanStep(
            step_description="Test step",
            input_variables=[],
            output_variables=[]
        )

        # Create a mock step with dict-like variables (edge case)
        # This tests the isinstance(input_vars, dict) branch
        class MockStep:
            step_description = "Mock step"
            input_variables = {"x": "int", "y": "str"}
            output_variables = {"result": "float"}

        result = build_step_user_first_msg_prompt(task, MockStep(), [])

        assert "Input variables available" in result
        assert "x: int" in result or "x (int)" in result
        assert "Output variables required" in result
        assert "result: float" in result or "result (float)" in result

    def test_build_prompt_full_scenario(self):
        """Test building prompt with all fields populated."""
        task = "Complete workflow"

        # Completed steps
        completed_step = PlanStep(
            step_description="Load data",
            input_variables=[],
            output_variables=[
                StepVariable(
                    variable_name="raw_data",
                    variable_description="Loaded data",
                    variable_data_type="list"
                )
            ]
        )

        # Current step
        current_step = PlanStep(
            step_description="Process and analyze",
            input_variables=[
                StepVariable(
                    variable_name="raw_data",
                    variable_description="Loaded data",
                    variable_data_type="list"
                )
            ],
            output_variables=[
                StepVariable(
                    variable_name="analysis",
                    variable_description="Analysis results",
                    variable_data_type="dict"
                )
            ]
        )

        result = build_step_user_first_msg_prompt(
            task,
            current_step,
            [(completed_step, "Data loaded successfully")]
        )

        # Verify all sections are present
        assert "Complete workflow" in result
        assert "Global Task" in result
        assert "Previous Steps Completed" in result
        assert "Load data" in result
        assert "Data loaded successfully" in result
        assert "CURRENT STEP" in result
        assert "Process and analyze" in result
        assert "Input variables available" in result
        assert "raw_data (list)" in result
        assert "Output variables required" in result
        assert "analysis (dict)" in result
