"""Tests for agent/utils.py - Pure functions without LLM calls."""

import pytest
from agent.utils import check_assigned_variables, format_step_variables
from agent.plan import StepVariable


class TestCheckAssignedVariables:
    """Test check_assigned_variables function."""

    def test_check_assigned_variables_final_answer_simple(self):
        """Test simple final_answer assignment."""
        code = "final_answer = 42"
        assert check_assigned_variables(code) is True

    def test_check_assigned_variables_step_status_simple(self):
        """Test simple step_status assignment."""
        code = "step_status = 'done'"
        assert check_assigned_variables(code) is True

    def test_check_assigned_variables_tuple_assignment(self):
        """Test tuple unpacking with final_answer or step_status."""
        code = "final_answer, step_status = (1, 2)"
        assert check_assigned_variables(code) is True

    def test_check_assigned_variables_list_assignment(self):
        """Test list unpacking with final_answer."""
        code = "[x, final_answer, y] = [1, 2, 3]"
        assert check_assigned_variables(code) is True

    def test_check_assigned_variables_no_match(self):
        """Test code without final_answer or step_status."""
        code = "result = 42"
        assert check_assigned_variables(code) is False

    def test_check_assigned_variables_invalid_syntax(self):
        """Test that invalid Python syntax returns False."""
        code = "def broken("
        assert check_assigned_variables(code) is False

    def test_check_assigned_variables_empty_code(self):
        """Test empty code string."""
        code = ""
        assert check_assigned_variables(code) is False

    def test_check_assigned_variables_multiline(self):
        """Test multiline code with assignment."""
        code = """
x = 10
y = 20
final_answer = x + y
"""
        assert check_assigned_variables(code) is True

    def test_check_assigned_variables_in_function(self):
        """Test assignment inside a function (should still be detected)."""
        code = """
def my_func():
    final_answer = 100
"""
        assert check_assigned_variables(code) is True


class TestFormatStepVariables:
    """Test format_step_variables function."""

    def test_format_step_variables_empty_list(self):
        """Test formatting empty list."""
        result = format_step_variables([])
        assert result == "None"

    def test_format_step_variables_single_variable(self):
        """Test formatting a single variable."""
        var = StepVariable(
            variable_name="x",
            variable_description="A number",
            variable_data_type="int"
        )
        result = format_step_variables([var])
        assert result == "\n  - x (int): A number"

    def test_format_step_variables_multiple_variables(self):
        """Test formatting multiple variables."""
        vars_list = [
            StepVariable(
                variable_name="x",
                variable_description="First number",
                variable_data_type="int"
            ),
            StepVariable(
                variable_name="y",
                variable_description="Second number",
                variable_data_type="float"
            ),
            StepVariable(
                variable_name="result",
                variable_description="Computed result",
                variable_data_type="str"
            ),
        ]
        result = format_step_variables(vars_list)

        assert "  - x (int): First number" in result
        assert "  - y (float): Second number" in result
        assert "  - result (str): Computed result" in result
        assert result.startswith("\n")

    def test_format_step_variables_complex_types(self):
        """Test formatting complex nested types."""
        var = StepVariable(
            variable_name="data",
            variable_description="Nested data structure",
            variable_data_type="list[dict[str, int]]"
        )
        result = format_step_variables([var])
        assert "data (list[dict[str, int]]): Nested data structure" in result
