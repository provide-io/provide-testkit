"""Configuration for mutation testing."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class ModulePriority(str, Enum):
    """Priority levels for mutation testing modules."""

    CRITICAL = "critical"  # 100% mutation score target (security, crypto)
    HIGH = "high"  # 80% mutation score target (core functionality)
    STANDARD = "standard"  # 60% mutation score target (regular code)
    LOW = "low"  # 40% mutation score target (utilities, helpers)


@dataclass
class MutationConfig:
    """Configuration for mutation testing.

    Attributes:
        paths_to_mutate: Paths to include in mutation testing
        exclude_patterns: Patterns to exclude (e.g., generated code)
        module_priorities: Mapping of module paths to priority levels
        score_thresholds: Minimum scores per priority level
        max_workers: Maximum parallel workers for mutation testing
        timeout_per_mutant: Timeout in seconds for each mutant test
        use_coverage: Only mutate lines covered by tests
        runner: Test runner command (default: pytest)
    """

    paths_to_mutate: list[str] = field(default_factory=lambda: ["src"])
    exclude_patterns: list[str] = field(
        default_factory=lambda: ["*/generated/*", "*_pb2.py", "*_pb2.pyi", "*/test_*", "*/tests/*"]
    )
    module_priorities: dict[str, ModulePriority] = field(default_factory=dict)
    score_thresholds: dict[ModulePriority, float] = field(
        default_factory=lambda: {
            ModulePriority.CRITICAL: 100.0,
            ModulePriority.HIGH: 80.0,
            ModulePriority.STANDARD: 60.0,
            ModulePriority.LOW: 40.0,
        }
    )
    max_workers: int = 4
    timeout_per_mutant: int = 10
    use_coverage: bool = True
    runner: str = "pytest"

    @classmethod
    def from_dict(cls, config: dict[str, any]) -> MutationConfig:
        """Create config from dictionary (e.g., from pyproject.toml)."""
        # Convert string priorities to enum
        module_priorities = {}
        if "module_priorities" in config:
            for module, priority in config["module_priorities"].items():
                if isinstance(priority, str):
                    module_priorities[module] = ModulePriority(priority)
                else:
                    module_priorities[module] = priority

        # Convert threshold priorities
        score_thresholds = {}
        if "score_thresholds" in config:
            for priority, score in config["score_thresholds"].items():
                if isinstance(priority, str):
                    score_thresholds[ModulePriority(priority)] = float(score)
                else:
                    score_thresholds[priority] = float(score)

        return cls(
            paths_to_mutate=config.get("paths_to_mutate", cls.paths_to_mutate),
            exclude_patterns=config.get("exclude_patterns", cls.exclude_patterns),
            module_priorities=module_priorities or config.get("module_priorities", {}),
            score_thresholds=score_thresholds or config.get("score_thresholds", cls.score_thresholds),
            max_workers=config.get("max_workers", cls.max_workers),
            timeout_per_mutant=config.get("timeout_per_mutant", cls.timeout_per_mutant),
            use_coverage=config.get("use_coverage", cls.use_coverage),
            runner=config.get("runner", cls.runner),
        )

    def get_module_priority(self, module_path: str | Path) -> ModulePriority:
        """Get priority for a specific module."""
        module_str = str(module_path)

        # Check exact matches first
        if module_str in self.module_priorities:
            return self.module_priorities[module_str]

        # Check pattern matches
        for pattern, priority in self.module_priorities.items():
            if "*" in pattern:
                # Simple glob matching
                import fnmatch

                if fnmatch.fnmatch(module_str, pattern):
                    return priority

        # Default to standard priority
        return ModulePriority.STANDARD

    def get_target_score(self, module_path: str | Path) -> float:
        """Get target mutation score for a module based on its priority."""
        priority = self.get_module_priority(module_path)
        return self.score_thresholds.get(priority, 60.0)
