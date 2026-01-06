"""Shared test fixtures for all test files."""

import pytest
from agent.plan import StepVariable, PlanStep, Plan


@pytest.fixture
def sample_step_variable():
    """Create a sample StepVariable for testing."""
    return StepVariable(
        variable_name="test_var",
        variable_description="A test variable",
        variable_data_type="str"
    )


@pytest.fixture
def sample_plan_step():
    """Create a sample PlanStep for testing."""
    return PlanStep(
        step_description="Test step",
        input_variables=[],
        output_variables=[]
    )


@pytest.fixture
def sample_plan():
    """Create a sample Plan for testing."""
    return Plan(steps=[])


@pytest.fixture
def temp_log_dir(tmp_path):
    """Provide temporary directory for log tests."""
    return tmp_path / "logs"
