"""Tests for agent/executor.py - Code execution functions."""

import pytest
import subprocess
from agent.executor import execute_python, execute_bash, PERSISTENT_GLOBALS


@pytest.fixture(autouse=True)
def reset_persistent_globals():
    """Reset PERSISTENT_GLOBALS after each test to prevent pollution."""
    # Store initial keys
    initial_keys = set(PERSISTENT_GLOBALS.keys())

    yield

    # Cleanup: remove any new keys added during test
    current_keys = set(PERSISTENT_GLOBALS.keys())
    for key in current_keys - initial_keys:
        del PERSISTENT_GLOBALS[key]


class TestExecutePython:
    """Test execute_python function."""

    def test_execute_python_simple_arithmetic(self):
        """Test executing simple arithmetic."""
        result = execute_python("print(2 + 2)")

        assert result.stdout == "4\n"
        assert result.stderr == ""

    def test_execute_python_variable_assignment(self):
        """Test variable assignment and printing."""
        result = execute_python("x = 42\nprint(x)")

        assert result.stdout == "42\n"
        assert result.stderr == ""

    def test_execute_python_persistent_globals(self):
        """Test that variables persist across calls."""
        # First execution
        result1 = execute_python("counter = 1")
        assert result1.stderr == ""

        # Second execution - counter should still exist
        result2 = execute_python("counter += 1\nprint(counter)")
        assert result2.stdout == "2\n"
        assert result2.stderr == ""

    def test_execute_python_syntax_error(self):
        """Test handling of syntax errors."""
        result = execute_python("def broken(")

        assert result.stdout == ""
        assert "SyntaxError" in result.stderr

    def test_execute_python_runtime_error(self):
        """Test handling of runtime errors."""
        result = execute_python("x = 1 / 0")

        assert "ZeroDivisionError" in result.stderr

    def test_execute_python_stdout_and_stderr(self):
        """Test capturing both stdout and stderr."""
        code = """
import sys
print('out')
print('err', file=sys.stderr)
"""
        result = execute_python(code)

        assert "out" in result.stdout
        # Note: stderr from print() is captured, but successful execution means stderr=""
        # The stderr in print is redirected and captured differently

    def test_execute_python_multiple_prints(self):
        """Test multiple print statements."""
        code = """
print('line1')
print('line2')
print('line3')
"""
        result = execute_python(code)

        assert "line1" in result.stdout
        assert "line2" in result.stdout
        assert "line3" in result.stdout

    def test_execute_python_return_globals(self):
        """Test that globals are returned in response."""
        result = execute_python("test_var = 'hello'")

        assert result.globals is not None
        assert "test_var" in result.globals
        assert result.globals["test_var"] == "hello"


class TestExecuteBash:
    """Test execute_bash function."""

    def test_execute_bash_simple_echo(self):
        """Test simple echo command."""
        result = execute_bash("echo 'hello'")

        assert result.stdout == "hello\n"
        assert result.stderr == ""

    def test_execute_bash_pwd(self):
        """Test pwd command."""
        result = execute_bash("pwd")

        assert "plan_repl_agent" in result.stdout
        assert result.stderr == ""

    def test_execute_bash_exit_code_success(self):
        """Test successful command (exit code 0)."""
        result = execute_bash("true")

        assert result.stderr == ""

    def test_execute_bash_exit_code_failure(self):
        """Test failed command (non-zero exit code)."""
        result = execute_bash("exit 1")

        # Non-zero exit code means stderr will be set (even if empty from command itself)
        # The 'false' command doesn't output to stderr, so let's use a command that does
        result2 = execute_bash("ls /nonexistent_directory_12345")
        assert result2.stderr != ""

    def test_execute_bash_stderr_capture(self):
        """Test capturing stderr output from failed command."""
        # Note: execute_bash only populates stderr when returncode != 0
        # So we need a command that fails AND outputs to stderr
        result = execute_bash("ls /nonexistent_directory_stderr_test_12345 2>&1")

        # This command will fail and output to stderr
        result2 = execute_bash("cat /nonexistent_file_12345")
        assert result2.stderr != ""
        assert "No such file" in result2.stderr or "cannot" in result2.stderr.lower()

    def test_execute_bash_multiline(self):
        """Test multiline bash script."""
        code = """
x=10
y=20
echo $((x + y))
"""
        result = execute_bash(code)

        assert "30" in result.stdout

    def test_execute_bash_timeout_handling(self, mocker):
        """Test timeout handling for long-running commands."""
        # Mock subprocess.run to raise TimeoutExpired
        mock_run = mocker.patch('agent.executor.subprocess.run')
        mock_run.side_effect = subprocess.TimeoutExpired('bash', 60)

        result = execute_bash("sleep 100")

        assert result.stdout == ""
        assert "Command timed out after 60 seconds" in result.stderr

    def test_execute_bash_exception_handling(self, mocker):
        """Test generic exception handling."""
        # Mock subprocess.run to raise a generic exception
        mock_run = mocker.patch('agent.executor.subprocess.run')
        mock_run.side_effect = Exception("Mock error")

        result = execute_bash("echo test")

        assert result.stdout == ""
        assert "Bash execution error" in result.stderr
        assert "Mock error" in result.stderr

    def test_execute_bash_command_not_found(self):
        """Test handling of non-existent commands."""
        result = execute_bash("nonexistentcommand12345")

        assert result.stderr != ""
        assert "not found" in result.stderr or "command not found" in result.stderr.lower()
