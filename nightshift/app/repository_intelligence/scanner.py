"""Repository scanner: detect tech stack and structure."""

from __future__ import annotations

from pathlib import Path

STACK_DETECTORS: dict[str, tuple[str, str]] = {
    "package.json": ("node", "npm"),
    "pyproject.toml": ("python", "python"),
    "pom.xml": ("java", "maven"),
    "build.gradle": ("java", "gradle"),
    "go.mod": ("go", "go"),
    "pubspec.yaml": ("dart", "flutter"),
    "Cargo.toml": ("rust", "cargo"),
}


def detect_stack(repo_path: Path) -> dict[str, str | None]:
    """Detect language/framework from manifest files (PRD section 22)."""
    result: dict[str, str | None] = {
        "language": None,
        "framework": None,
        "package_manager": None,
    }
    for manifest, (language, pkg_manager) in STACK_DETECTORS.items():
        if (repo_path / manifest).exists():
            result["language"] = language
            result["package_manager"] = pkg_manager
            break

    # Framework hints
    if result["language"] == "node":
        pkg = repo_path / "package.json"
        if pkg.exists():
            import json

            data = json.loads(pkg.read_text(encoding="utf-8"))
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            if "@nestjs/core" in deps:
                result["framework"] = "nestjs"
            elif "next" in deps:
                result["framework"] = "nextjs"
            elif "react" in deps:
                result["framework"] = "react"
            elif "vue" in deps:
                result["framework"] = "vue"
    elif result["language"] == "dart":
        result["framework"] = "flutter"

    return result


def list_source_dirs(repo_path: Path) -> list[str]:
    """Return likely source directories."""
    candidates = ["src", "app", "lib", "packages", "server"]
    return [c for c in candidates if (repo_path / c).is_dir()]


def find_readme(repo_path: Path) -> str | None:
    for name in ("README.md", "README.rst", "README.txt"):
        candidate = repo_path / name
        if candidate.exists():
            return candidate.read_text(encoding="utf-8", errors="ignore")[:4000]
    return None
