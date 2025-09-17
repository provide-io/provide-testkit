"""Tests for quality analysis base classes and protocols."""

from pathlib import Path

from provide.testkit.quality.base import (
    BaseQualityFixture,
    QualityConfigError,
    QualityError,
    QualityResult,
    QualityToolError,
)


class TestQualityResult:
    """Test QualityResult data class."""

    def test_basic_creation(self):
        """Test basic result creation."""
        result = QualityResult(tool="test", passed=True)
        assert result.tool == "test"
        assert result.passed is True
        assert result.score is None
        assert result.details == {}
        assert result.artifacts == []
        assert result.execution_time is None

    def test_full_creation(self):
        """Test result creation with all fields."""
        artifacts = [Path("test.txt")]
        details = {"issues": 3}

        result = QualityResult(
            tool="bandit", passed=False, score=85.5, details=details, artifacts=artifacts, execution_time=1.23
        )

        assert result.tool == "bandit"
        assert result.passed is False
        assert result.score == 85.5
        assert result.details == details
        assert result.artifacts == artifacts
        assert result.execution_time == 1.23

    def test_summary_passed(self):
        """Test summary for passed result."""
        result = QualityResult(tool="coverage", passed=True, score=95.5)
        assert result.summary == "coverage: ✅ PASSED (95.5%)"

    def test_summary_failed(self):
        """Test summary for failed result."""
        result = QualityResult(tool="security", passed=False)
        assert result.summary == "security: ❌ FAILED"

    def test_summary_no_score(self):
        """Test summary without score."""
        result = QualityResult(tool="lint", passed=True)
        assert result.summary == "lint: ✅ PASSED"


class MockQualityFixture(BaseQualityFixture):
    """Mock fixture for testing."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_called = False
        self.teardown_called = False

    def setup(self):
        self.setup_called = True

    def teardown(self):
        self.teardown_called = True


class TestBaseQualityFixture:
    """Test BaseQualityFixture abstract base class."""

    def test_initialization(self, tmp_path):
        """Test fixture initialization."""
        config = {"tool_option": "value"}
        fixture = MockQualityFixture(config=config, artifact_dir=tmp_path)

        assert fixture.config == config
        assert fixture.artifact_dir == tmp_path
        assert fixture.results == []
        assert fixture._setup_complete is False

    def test_default_initialization(self):
        """Test fixture with default values."""
        fixture = MockQualityFixture()

        assert fixture.config == {}
        assert fixture.artifact_dir == Path(".quality")
        assert fixture.results == []

    def test_ensure_setup(self):
        """Test ensure_setup calls setup once."""
        fixture = MockQualityFixture()

        assert not fixture.setup_called
        assert not fixture._setup_complete

        fixture.ensure_setup()
        assert fixture.setup_called
        assert fixture._setup_complete

        # Second call should not call setup again
        fixture.setup_called = False
        fixture.ensure_setup()
        assert not fixture.setup_called
        assert fixture._setup_complete

    def test_add_and_get_results(self):
        """Test result tracking."""
        fixture = MockQualityFixture()

        result1 = QualityResult(tool="test1", passed=True)
        result2 = QualityResult(tool="test2", passed=False)

        fixture.add_result(result1)
        fixture.add_result(result2)

        results = fixture.get_results()
        assert len(results) == 2
        assert results[0] == result1
        assert results[1] == result2

        # Ensure returned list is a copy
        results.append(QualityResult(tool="test3", passed=True))
        assert len(fixture.get_results()) == 2

    def test_create_artifact_dir(self, tmp_path):
        """Test artifact directory creation."""
        fixture = MockQualityFixture(artifact_dir=tmp_path / "quality")

        # Create main artifact dir
        artifact_dir = fixture.create_artifact_dir()
        assert artifact_dir.exists()
        assert artifact_dir == tmp_path / "quality"

        # Create subdirectory
        subdir = fixture.create_artifact_dir("coverage")
        assert subdir.exists()
        assert subdir == tmp_path / "quality" / "coverage"

    def test_create_artifact_dir_exists_ok(self, tmp_path):
        """Test artifact directory creation when already exists."""
        fixture = MockQualityFixture(artifact_dir=tmp_path)

        # Create directory first
        (tmp_path / "test").mkdir()

        # Should not raise error
        artifact_dir = fixture.create_artifact_dir("test")
        assert artifact_dir.exists()


class TestQualityExceptions:
    """Test quality exception classes."""

    def test_quality_error_basic(self):
        """Test basic QualityError."""
        error = QualityError("Test error")
        assert str(error) == "Test error"
        assert error.tool is None
        assert error.details == {}

    def test_quality_error_with_tool(self):
        """Test QualityError with tool information."""
        details = {"exit_code": 1, "stderr": "Error output"}
        error = QualityError("Tool failed", tool="bandit", details=details)

        assert str(error) == "Tool failed"
        assert error.tool == "bandit"
        assert error.details == details

    def test_quality_config_error(self):
        """Test QualityConfigError inheritance."""
        error = QualityConfigError("Invalid config", tool="test")
        assert isinstance(error, QualityError)
        assert str(error) == "Invalid config"
        assert error.tool == "test"

    def test_quality_tool_error(self):
        """Test QualityToolError inheritance."""
        error = QualityToolError("Tool execution failed", tool="coverage")
        assert isinstance(error, QualityError)
        assert str(error) == "Tool execution failed"
        assert error.tool == "coverage"
