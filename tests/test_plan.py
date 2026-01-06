"""Tests for agent/plan.py - Plan formatting and validation."""

import pytest
from agent.plan import (
    StepVariable,
    PlanStep,
    Plan,
    format_completed_steps,
    format_remaining_steps,
    check_plan,
)


class TestFormatCompletedSteps:
    """Test format_completed_steps function."""

    def test_format_completed_steps_empty(self):
        """Test formatting empty list of completed steps."""
        result = format_completed_steps([])
        assert result == ""

    def test_format_completed_steps_single_step_no_vars(self):
        """Test formatting single step without variables."""
        step = PlanStep(
            step_description="Test step",
            input_variables=[],
            output_variables=[]
        )
        result = format_completed_steps([(step, "success")])

        assert "Step 1: Test step" in result
        assert "Result: success" in result

    def test_format_completed_steps_with_input_vars(self):
        """Test formatting step with input variables."""
        input_var = StepVariable(
            variable_name="x",
            variable_description="Input value",
            variable_data_type="int"
        )
        step = PlanStep(
            step_description="Process input",
            input_variables=[input_var],
            output_variables=[]
        )
        result = format_completed_steps([(step, "processed")])

        assert "Step 1: Process input" in result
        assert "Input variables: x (int)" in result
        assert "Result: processed" in result

    def test_format_completed_steps_with_output_vars(self):
        """Test formatting step with output variables."""
        output_var = StepVariable(
            variable_name="result",
            variable_description="Computed result",
            variable_data_type="str"
        )
        step = PlanStep(
            step_description="Generate output",
            input_variables=[],
            output_variables=[output_var]
        )
        result = format_completed_steps([(step, "generated")])

        assert "Step 1: Generate output" in result
        assert "Output variables: result (str)" in result
        assert "Result: generated" in result

    def test_format_completed_steps_multiple_steps(self):
        """Test formatting multiple completed steps."""
        step1 = PlanStep(
            step_description="First step",
            input_variables=[],
            output_variables=[]
        )
        step2 = PlanStep(
            step_description="Second step",
            input_variables=[],
            output_variables=[]
        )
        result = format_completed_steps([
            (step1, "result1"),
            (step2, "result2")
        ])

        assert "Step 1: First step" in result
        assert "Step 2: Second step" in result
        assert "Result: result1" in result
        assert "Result: result2" in result


class TestFormatRemainingSteps:
    """Test format_remaining_steps function."""

    def test_format_remaining_steps_empty(self):
        """Test formatting empty list of remaining steps."""
        result = format_remaining_steps([])
        assert result == ""

    def test_format_remaining_steps_single_step(self):
        """Test formatting single remaining step."""
        step = PlanStep(
            step_description="Remaining task",
            input_variables=[],
            output_variables=[]
        )
        result = format_remaining_steps([step])

        assert "Step 1: Remaining task" in result

    def test_format_remaining_steps_multiple_steps(self):
        """Test formatting multiple remaining steps."""
        step1 = PlanStep(step_description="Task 1", input_variables=[], output_variables=[])
        step2 = PlanStep(step_description="Task 2", input_variables=[], output_variables=[])
        step3 = PlanStep(step_description="Task 3", input_variables=[], output_variables=[])

        result = format_remaining_steps([step1, step2, step3])

        assert "Step 1: Task 1" in result
        assert "Step 2: Task 2" in result
        assert "Step 3: Task 3" in result

    def test_format_remaining_steps_with_variables(self):
        """Test formatting steps with both input and output variables."""
        input_var = StepVariable(
            variable_name="data",
            variable_description="Input data",
            variable_data_type="list[str]"
        )
        output_var = StepVariable(
            variable_name="processed",
            variable_description="Processed data",
            variable_data_type="dict"
        )
        step = PlanStep(
            step_description="Transform data",
            input_variables=[input_var],
            output_variables=[output_var]
        )
        result = format_remaining_steps([step])

        assert "Step 1: Transform data" in result
        assert "Input variables: data (list[str])" in result
        assert "Output variables: processed (dict)" in result


class TestCheckPlan:
    """Test check_plan validation function."""

    def test_check_plan_empty_plan(self, capsys):
        """Test that empty plan produces no warnings."""
        plan = Plan(steps=[])
        check_plan(plan)

        captured = capsys.readouterr()
        assert "⚠️" not in captured.out

    def test_check_plan_first_step_has_inputs_warning(self, capsys):
        """Test warning when first step has input variables."""
        input_var = StepVariable(
            variable_name="x",
            variable_description="Input",
            variable_data_type="int"
        )
        step = PlanStep(
            step_description="First step",
            input_variables=[input_var],
            output_variables=[]
        )
        plan = Plan(steps=[step])

        check_plan(plan)

        captured = capsys.readouterr()
        assert "⚠️" in captured.out
        assert "First step has input variables: x" in captured.out
        assert "First step should not require inputs" in captured.out

    def test_check_plan_input_not_produced_warning(self, capsys):
        """Test warning when step requires variable not produced by previous steps."""
        step1 = PlanStep(
            step_description="Step 1",
            input_variables=[],
            output_variables=[]
        )
        input_var = StepVariable(
            variable_name="missing_var",
            variable_description="Not produced",
            variable_data_type="str"
        )
        step2 = PlanStep(
            step_description="Step 2",
            input_variables=[input_var],
            output_variables=[]
        )
        plan = Plan(steps=[step1, step2])

        check_plan(plan)

        captured = capsys.readouterr()
        assert "⚠️" in captured.out
        assert "Step 2 requires input 'missing_var'" in captured.out
        assert "no previous step produces it" in captured.out

    def test_check_plan_output_not_consumed_warning(self, capsys):
        """Test warning when output variable is not consumed by subsequent steps."""
        output_var = StepVariable(
            variable_name="unused",
            variable_description="Not used",
            variable_data_type="int"
        )
        step1 = PlanStep(
            step_description="Step 1",
            input_variables=[],
            output_variables=[output_var]
        )
        step2 = PlanStep(
            step_description="Step 2",
            input_variables=[],
            output_variables=[]
        )
        plan = Plan(steps=[step1, step2])

        check_plan(plan)

        captured = capsys.readouterr()
        assert "⚠️" in captured.out
        assert "Step 1 outputs 'unused'" in captured.out
        assert "not used by any subsequent step" in captured.out

    def test_check_plan_valid_chain_no_warnings(self, capsys):
        """Test valid plan with proper variable chain produces no warnings."""
        output_var = StepVariable(
            variable_name="data",
            variable_description="Generated data",
            variable_data_type="str"
        )
        step1 = PlanStep(
            step_description="Generate data",
            input_variables=[],
            output_variables=[output_var]
        )

        input_var = StepVariable(
            variable_name="data",
            variable_description="Generated data",
            variable_data_type="str"
        )
        step2 = PlanStep(
            step_description="Process data",
            input_variables=[input_var],
            output_variables=[]
        )
        plan = Plan(steps=[step1, step2])

        check_plan(plan)

        captured = capsys.readouterr()
        assert "⚠️" not in captured.out

    def test_check_plan_last_step_outputs_ok(self, capsys):
        """Test that last step outputs don't trigger warnings."""
        output_var = StepVariable(
            variable_name="final_result",
            variable_description="Final output",
            variable_data_type="dict"
        )
        step = PlanStep(
            step_description="Final step",
            input_variables=[],
            output_variables=[output_var]
        )
        plan = Plan(steps=[step])

        check_plan(plan)

        captured = capsys.readouterr()
        # Should not warn about unused output for last step
        # But will warn about first step having no inputs (which is OK)
        if "⚠️" in captured.out:
            assert "not used by any subsequent step" not in captured.out
