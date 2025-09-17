"""Artifact management for quality analysis results."""

from __future__ import annotations

from pathlib import Path
import shutil
import time
from typing import Any

from provide.foundation.file import ensure_dir

from .base import QualityResult


class ArtifactManager:
    """Manages artifacts generated during quality analysis.

    Provides centralized artifact management with organization, cleanup,
    and metadata tracking capabilities.
    """

    def __init__(self, base_dir: Path | str = ".quality-artifacts"):
        """Initialize artifact manager.

        Args:
            base_dir: Base directory for all artifacts
        """
        self.base_dir = Path(base_dir)
        self.session_id = str(int(time.time()))

    def create_session_dir(self, tool: str) -> Path:
        """Create a session-specific directory for a tool.

        Args:
            tool: Tool name

        Returns:
            Path to tool's session directory
        """
        session_dir = self.base_dir / self.session_id / tool
        ensure_dir(session_dir)
        return session_dir

    def create_timestamped_dir(self, tool: str) -> Path:
        """Create a timestamped directory for a tool.

        Args:
            tool: Tool name

        Returns:
            Path to tool's timestamped directory
        """
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        timestamped_dir = self.base_dir / tool / timestamp
        ensure_dir(timestamped_dir)
        return timestamped_dir

    def get_latest_dir(self, tool: str) -> Path | None:
        """Get the latest artifact directory for a tool.

        Args:
            tool: Tool name

        Returns:
            Path to latest directory or None if none exist
        """
        tool_dir = self.base_dir / tool
        if not tool_dir.exists():
            return None

        # Find latest timestamped directory
        subdirs = [d for d in tool_dir.iterdir() if d.is_dir()]
        if not subdirs:
            return None

        return max(subdirs, key=lambda d: d.stat().st_mtime)

    def organize_artifacts(self, result: QualityResult, target_dir: Path) -> None:
        """Organize artifacts from a quality result.

        Args:
            result: Quality result with artifacts
            target_dir: Target directory for organized artifacts
        """
        if not result.artifacts:
            return

        ensure_dir(target_dir)

        # Copy artifacts to organized location
        for artifact_path in result.artifacts:
            if not artifact_path.exists():
                continue

            # Determine target filename
            target_filename = f"{result.tool}_{artifact_path.name}"
            target_path = target_dir / target_filename

            # Copy artifact
            if artifact_path.is_file():
                shutil.copy2(artifact_path, target_path)
            elif artifact_path.is_dir():
                shutil.copytree(artifact_path, target_path, dirs_exist_ok=True)

        # Create metadata file
        metadata = {
            "tool": result.tool,
            "passed": result.passed,
            "score": result.score,
            "execution_time": result.execution_time,
            "timestamp": time.time(),
            "artifacts": [str(p) for p in result.artifacts],
        }

        metadata_path = target_dir / f"{result.tool}_metadata.json"
        with open(metadata_path, "w") as f:
            import json

            json.dump(metadata, f, indent=2)

    def cleanup_old_artifacts(self, tool: str | None = None, keep_count: int = 5) -> None:
        """Clean up old artifact directories.

        Args:
            tool: Specific tool to clean up (None for all tools)
            keep_count: Number of recent directories to keep
        """
        if tool:
            tool_dirs = [self.base_dir / tool] if (self.base_dir / tool).exists() else []
        else:
            tool_dirs = [d for d in self.base_dir.iterdir() if d.is_dir()]

        for tool_dir in tool_dirs:
            if not tool_dir.is_dir():
                continue

            # Get all timestamped subdirectories
            subdirs = [d for d in tool_dir.iterdir() if d.is_dir()]
            if len(subdirs) <= keep_count:
                continue

            # Sort by modification time and remove oldest
            subdirs.sort(key=lambda d: d.stat().st_mtime, reverse=True)
            for old_dir in subdirs[keep_count:]:
                shutil.rmtree(old_dir, ignore_errors=True)

    def create_summary_report(self, results: dict[str, QualityResult]) -> Path:
        """Create a summary report across all tools.

        Args:
            results: Results from multiple tools

        Returns:
            Path to summary report
        """
        summary_dir = self.base_dir / "summaries"
        ensure_dir(summary_dir)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        summary_path = summary_dir / f"quality_summary_{timestamp}.json"

        # Build summary data
        summary = {
            "timestamp": time.time(),
            "session_id": self.session_id,
            "overall_passed": all(result.passed for result in results.values()),
            "tools": {},
        }

        for tool, result in results.items():
            summary["tools"][tool] = {
                "passed": result.passed,
                "score": result.score,
                "execution_time": result.execution_time,
                "artifact_count": len(result.artifacts),
                "key_metrics": self._extract_key_metrics(result),
            }

        # Write summary
        with open(summary_path, "w") as f:
            import json

            json.dump(summary, f, indent=2)

        return summary_path

    def _extract_key_metrics(self, result: QualityResult) -> dict[str, Any]:
        """Extract key metrics from a quality result.

        Args:
            result: Quality result

        Returns:
            Dictionary of key metrics
        """
        details = result.details
        metrics = {}

        if result.tool == "coverage":
            metrics.update(
                {
                    "coverage_percentage": details.get("coverage_percentage"),
                    "lines_covered": details.get("lines_covered"),
                    "lines_missing": details.get("lines_missing"),
                }
            )
        elif result.tool == "security":
            metrics.update(
                {
                    "total_issues": details.get("total_issues"),
                    "high_severity": details.get("severity_counts", {}).get("HIGH"),
                    "medium_severity": details.get("severity_counts", {}).get("MEDIUM"),
                    "low_severity": details.get("severity_counts", {}).get("LOW"),
                }
            )
        elif result.tool == "complexity":
            metrics.update(
                {
                    "average_complexity": details.get("average_complexity"),
                    "max_complexity": details.get("max_complexity"),
                    "overall_grade": details.get("overall_grade"),
                    "total_functions": details.get("total_functions"),
                }
            )
        elif result.tool == "documentation":
            metrics.update(
                {
                    "total_coverage": details.get("total_coverage"),
                    "covered_count": details.get("covered_count"),
                    "missing_count": details.get("missing_count"),
                    "grade": details.get("grade"),
                }
            )
        elif result.tool == "profiling":
            memory_data = details.get("memory", {})
            cpu_data = details.get("cpu", {})
            metrics.update(
                {
                    "peak_memory_mb": memory_data.get("peak_memory_mb"),
                    "execution_time": cpu_data.get("execution_time"),
                    "memory_score": details.get("scores", {}).get("memory_score"),
                    "cpu_score": details.get("scores", {}).get("cpu_score"),
                }
            )

        # Remove None values
        return {k: v for k, v in metrics.items() if v is not None}

    def export_artifacts(self, export_path: Path | str, compress: bool = True) -> Path:
        """Export all artifacts to a specified location.

        Args:
            export_path: Path to export to
            compress: Whether to create a compressed archive

        Returns:
            Path to exported artifacts
        """
        export_path = Path(export_path)

        if compress:
            # Create compressed archive
            if not export_path.suffix:
                archive_path = export_path.with_suffix(".tar.gz")
            else:
                archive_path = export_path

            shutil.make_archive(str(archive_path.with_suffix("")), "gztar", self.base_dir)
            return archive_path
        else:
            # Copy directory tree
            if export_path.exists():
                shutil.rmtree(export_path)

            shutil.copytree(self.base_dir, export_path)
            return export_path

    def get_disk_usage(self) -> dict[str, int]:
        """Get disk usage statistics for artifacts.

        Returns:
            Dictionary with disk usage information
        """
        if not self.base_dir.exists():
            return {"total_bytes": 0, "tool_breakdown": {}}

        total_size = 0
        tool_breakdown = {}

        for item in self.base_dir.rglob("*"):
            if item.is_file():
                size = item.stat().st_size
                total_size += size

                # Determine which tool this belongs to
                relative_path = item.relative_to(self.base_dir)
                tool = relative_path.parts[0] if relative_path.parts else "unknown"
                tool_breakdown[tool] = tool_breakdown.get(tool, 0) + size

        return {
            "total_bytes": total_size,
            "total_mb": total_size / (1024 * 1024),
            "tool_breakdown": tool_breakdown,
        }

    def generate_index(self) -> Path:
        """Generate an index of all artifacts.

        Returns:
            Path to generated index file
        """
        index_path = self.base_dir / "index.json"

        index_data = {
            "generated_at": time.time(),
            "session_id": self.session_id,
            "base_directory": str(self.base_dir),
            "disk_usage": self.get_disk_usage(),
            "tools": {},
        }

        # Scan for tool directories and artifacts
        for tool_dir in self.base_dir.iterdir():
            if not tool_dir.is_dir() or tool_dir.name in ["summaries", "exports"]:
                continue

            tool_info = {"latest_run": None, "total_runs": 0, "artifacts": []}

            # Find all run directories
            run_dirs = [d for d in tool_dir.iterdir() if d.is_dir()]
            tool_info["total_runs"] = len(run_dirs)

            if run_dirs:
                latest_dir = max(run_dirs, key=lambda d: d.stat().st_mtime)
                tool_info["latest_run"] = {
                    "timestamp": latest_dir.stat().st_mtime,
                    "path": str(latest_dir),
                    "artifacts": [str(f) for f in latest_dir.iterdir() if f.is_file()],
                }

            # Collect all artifacts
            for artifact in tool_dir.rglob("*"):
                if artifact.is_file():
                    tool_info["artifacts"].append(
                        {
                            "path": str(artifact),
                            "size": artifact.stat().st_size,
                            "modified": artifact.stat().st_mtime,
                        }
                    )

            index_data["tools"][tool_dir.name] = tool_info

        # Write index
        with open(index_path, "w") as f:
            import json

            json.dump(index_data, f, indent=2)

        return index_path
