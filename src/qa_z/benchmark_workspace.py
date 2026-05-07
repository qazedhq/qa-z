"""Workspace and lock helpers for benchmark execution."""

from __future__ import annotations

import os
import shutil
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Iterator

if TYPE_CHECKING:
    from qa_z.benchmark import BenchmarkFixture


BENCHMARK_LOCK_FILENAME = ".benchmark.lock"


@contextmanager
def benchmark_results_lock(results_dir: Path):
    """Prevent concurrent benchmark runs from resetting the same work dir."""
    lock_path = results_dir / BENCHMARK_LOCK_FILENAME
    try:
        with lock_path.open("x", encoding="utf-8") as lock_file:
            lock_file.write(f"pid={os.getpid()}\n")
            lock_file.write(f"started_at={_utc_timestamp()}\n")
            lock_file.write(f"results_dir={results_dir}\n")
    except FileExistsError as exc:
        lock_details = _read_benchmark_lock_details(lock_path)
        raise _benchmark_error(
            "Benchmark results directory is already in use: "
            f"{results_dir}. Remove stale lock {lock_path} only after confirming "
            "no benchmark is running, or use a different --results-dir. "
            f"lock details: {lock_details}."
        ) from exc
    try:
        yield
    finally:
        try:
            unlink_with_retries(lock_path)
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise _benchmark_error(
                "Could not remove benchmark results lock "
                f"{lock_path}. Remove stale lock only after confirming no "
                "benchmark is running, or use a different --results-dir. "
                f"results_dir={results_dir}. error={exc}"
            ) from exc


def _benchmark_error(message: str) -> Exception:
    from qa_z.benchmark import BenchmarkError

    return BenchmarkError(message)


def _utc_timestamp() -> str:
    """Return a compact UTC timestamp for operator-facing lock files."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _read_benchmark_lock_details(lock_path: Path) -> str:
    """Read safe, compact lock metadata for benchmark conflict diagnostics."""
    try:
        raw_lock = lock_path.read_text(encoding="utf-8")
    except OSError:
        return "unavailable"
    details: list[str] = []
    for line in raw_lock.splitlines():
        clean = line.strip()
        if not clean:
            continue
        details.append(clean[:240])
        if len(details) >= 3:
            break
    if not details:
        return "empty lock file"
    return "; ".join(details)


def prepare_workspace(fixture: "BenchmarkFixture", work_dir: Path) -> Path:
    """Copy fixture repo data into an isolated benchmark workspace."""
    fixture_work_dir = work_dir / fixture.name
    reset_directory(fixture_work_dir)
    workspace = fixture_work_dir / "repo"
    if fixture.repo_path.exists():
        shutil.copytree(fixture.repo_path, workspace)
    else:
        workspace.mkdir(parents=True, exist_ok=True)
    install_support_files(fixture, workspace)
    return workspace


def install_support_files(fixture: "BenchmarkFixture", workspace: Path) -> None:
    """Copy shared benchmark support scripts into the isolated workspace."""
    support_dir = fixture.path.parent.parent / "support"
    if not support_dir.exists():
        return

    script_dir = workspace / ".qa-z-benchmark"
    script_dir.mkdir(parents=True, exist_ok=True)
    for support_file in support_dir.glob("*.py"):
        shutil.copy2(support_file, script_dir / support_file.name)

    bin_dir = support_dir / "bin"
    if bin_dir.exists():
        target_bin = workspace / ".qa-z-benchmark-bin"
        shutil.copytree(bin_dir, target_bin, dirs_exist_ok=True)
        for helper in target_bin.iterdir():
            if helper.is_file():
                helper.chmod(helper.stat().st_mode | 0o755)


@contextmanager
def fixture_path_environment(workspace: Path) -> Iterator[None]:
    """Temporarily prepend fixture helper binaries to PATH."""
    bin_dir = workspace / ".qa-z-benchmark-bin"
    original_path = os.environ.get("PATH", "")
    if bin_dir.exists():
        os.environ["PATH"] = f"{bin_dir}{os.pathsep}{original_path}"
    try:
        yield
    finally:
        os.environ["PATH"] = original_path


def reset_directory(path: Path) -> None:
    """Remove and recreate a directory."""
    if path.exists():
        rmtree_with_retries(path)
    path.mkdir(parents=True, exist_ok=True)


def rmtree_with_retries(
    path: Path, *, retries: int = 3, delay_seconds: float = 0.1
) -> None:
    """Remove a directory with small retries for transient Windows locks."""
    last_error: PermissionError | None = None
    for attempt in range(retries):
        try:
            shutil.rmtree(path)
            return
        except FileNotFoundError:
            return
        except PermissionError as exc:
            last_error = exc
            if attempt == retries - 1:
                raise
            time.sleep(delay_seconds)
    if last_error is not None:
        raise last_error


def unlink_with_retries(
    path: Path, *, retries: int = 3, delay_seconds: float = 0.1
) -> None:
    """Unlink a file with small retries for transient Windows locks."""
    last_error: PermissionError | None = None
    for attempt in range(retries):
        try:
            path.unlink()
            return
        except FileNotFoundError:
            return
        except PermissionError as exc:
            last_error = exc
            if attempt == retries - 1:
                raise
            time.sleep(delay_seconds)
    if last_error is not None:
        raise last_error
