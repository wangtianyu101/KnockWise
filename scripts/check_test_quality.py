#!/usr/bin/env python3
"""Reject empty, placeholder, or undocumented skipped Python tests.

The checker deliberately does not require a literal ``assert`` in every test:
``pytest.raises``, mock assertions, and assertion helpers are all valid styles.
Instead, it blocks the structural patterns that create false-green pytest runs.
"""
from __future__ import annotations

import argparse
import ast
import io
import re
import tokenize
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence


PLACEHOLDER_PATTERN = re.compile(
    r"(?:\b(?:todo|fixme|xxx|placeholder)\b|待实现|待补|未实现)",
    flags=re.IGNORECASE,
)


@dataclass(frozen=True)
class Violation:
    path: Path
    line: int
    code: str
    test_name: str
    message: str


def _call_name(node: ast.AST) -> str:
    """Return a dotted name for simple calls such as pytest.mark.skip."""
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
    return ".".join(reversed(parts))


def _is_nonempty_reason(node: ast.AST | None) -> bool:
    if node is None:
        return False
    if isinstance(node, ast.Constant):
        return isinstance(node.value, str) and bool(node.value.strip())
    # Dynamic reasons (for example f-strings containing a path) are documented.
    return isinstance(node, (ast.FormattedValue, ast.JoinedStr, ast.Name, ast.Attribute))


def _reason_from_call(call: ast.Call, *, skipif: bool) -> ast.AST | None:
    for keyword in call.keywords:
        if keyword.arg == "reason":
            return keyword.value
    position = 1 if skipif else 0
    if len(call.args) > position:
        return call.args[position]
    return None


def _is_skip_decorator(decorator: ast.expr) -> bool:
    target = decorator.func if isinstance(decorator, ast.Call) else decorator
    name = _call_name(target)
    return name.endswith((".skip", ".skipif")) or name in {"skip", "unittest.skip"}


def _has_skip_decorator(decorators: Iterable[ast.expr]) -> bool:
    return any(_is_skip_decorator(decorator) for decorator in decorators)


def _skip_decorator_without_reason(decorators: Iterable[ast.expr]) -> ast.AST | None:
    for decorator in decorators:
        if isinstance(decorator, ast.Call):
            name = _call_name(decorator.func)
            if name.endswith(".skipif"):
                if not _is_nonempty_reason(_reason_from_call(decorator, skipif=True)):
                    return decorator
            elif name.endswith(".skip") or name in {"skip", "unittest.skip"}:
                if not _is_nonempty_reason(_reason_from_call(decorator, skipif=False)):
                    return decorator
        else:
            name = _call_name(decorator)
            if name.endswith(".skip") or name in {"skip", "unittest.skip"}:
                return decorator
    return None


def _runtime_skip_calls(function: ast.FunctionDef | ast.AsyncFunctionDef) -> list[ast.Call]:
    return [
        node
        for node in ast.walk(function)
        if isinstance(node, ast.Call) and _call_name(node.func) in {"pytest.skip", "skip"}
    ]


def _skip_without_reason(function: ast.FunctionDef | ast.AsyncFunctionDef) -> ast.AST | None:
    """Return the first undocumented skip decorator/call, if present."""
    decorator = _skip_decorator_without_reason(function.decorator_list)
    if decorator is not None:
        return decorator

    for node in _runtime_skip_calls(function):
        if not _is_nonempty_reason(_reason_from_call(node, skipif=False)):
            return node
    return None


def _is_docstring(statement: ast.stmt) -> bool:
    return (
        isinstance(statement, ast.Expr)
        and isinstance(statement.value, ast.Constant)
        and isinstance(statement.value.value, str)
    )


def _is_noop_statement(statement: ast.stmt) -> bool:
    if isinstance(statement, ast.Pass):
        return True
    if isinstance(statement, ast.Expr):
        return isinstance(statement.value, ast.Constant) and statement.value.value is Ellipsis
    if isinstance(statement, ast.Return):
        return statement.value is None or (
            isinstance(statement.value, ast.Constant) and statement.value.value is None
        )
    return False


def _is_empty_test(function: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    body = list(function.body)
    if body and _is_docstring(body[0]):
        body = body[1:]
    return not body or all(_is_noop_statement(statement) for statement in body)


def _comment_markers(source: str) -> dict[int, str]:
    markers: dict[int, str] = {}
    try:
        tokens = tokenize.generate_tokens(io.StringIO(source).readline)
        for token in tokens:
            if token.type != tokenize.COMMENT:
                continue
            match = PLACEHOLDER_PATTERN.search(token.string)
            if match:
                markers[token.start[0]] = match.group(0)
    except tokenize.TokenError:
        # ast.parse reports the actionable syntax error separately.
        pass
    return markers


def _placeholder_marker(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    comment_markers: dict[int, str],
) -> tuple[int, str] | None:
    docstring = ast.get_docstring(function, clean=False)
    if docstring:
        match = PLACEHOLDER_PATTERN.search(docstring)
        if match:
            first_statement = function.body[0]
            return first_statement.lineno, match.group(0)

    for line, marker in sorted(comment_markers.items()):
        if function.lineno <= line <= (function.end_lineno or function.lineno):
            return line, marker
    return None


def scan_file(path: Path) -> tuple[list[Violation], int]:
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source, filename=str(path))
    except SyntaxError as error:
        return [
            Violation(
                path=path,
                line=error.lineno or 1,
                code="syntax-error",
                test_name="<module>",
                message=error.msg,
            )
        ], 0

    comments = _comment_markers(source)
    violations: list[Violation] = []
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent
    tests = [
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    ]
    tests.sort(key=lambda node: (node.lineno, node.name))

    for function in tests:
        skip_present = _has_skip_decorator(function.decorator_list) or bool(
            _runtime_skip_calls(function)
        )
        undocumented_skip = _skip_without_reason(function)
        ancestor = parents.get(function)
        while ancestor is not None:
            if isinstance(ancestor, ast.ClassDef):
                skip_present = skip_present or _has_skip_decorator(ancestor.decorator_list)
                if undocumented_skip is None:
                    undocumented_skip = _skip_decorator_without_reason(ancestor.decorator_list)
            ancestor = parents.get(ancestor)
        documented_skip = skip_present and undocumented_skip is None

        marker = _placeholder_marker(function, comments)
        if marker is not None and not documented_skip:
            line, text = marker
            violations.append(
                Violation(
                    path=path,
                    line=line,
                    code="placeholder-marker",
                    test_name=function.name,
                    message=f"placeholder marker {text!r} must be removed or replaced by an explained skip",
                )
            )
        elif _is_empty_test(function) and not documented_skip:
            violations.append(
                Violation(
                    path=path,
                    line=function.lineno,
                    code="empty-test",
                    test_name=function.name,
                    message="test body contains only pass, ellipsis, docstring, or an empty return",
                )
            )

        if undocumented_skip is not None:
            violations.append(
                Violation(
                    path=path,
                    line=getattr(undocumented_skip, "lineno", function.lineno),
                    code="skip-without-reason",
                    test_name=function.name,
                    message="skip/skipif must include a non-empty reason",
                )
            )

    return violations, len(tests)


def collect_test_files(paths: Iterable[Path]) -> list[Path]:
    files: set[Path] = set()
    for path in paths:
        if path.is_dir():
            files.update(candidate for candidate in path.rglob("test_*.py") if candidate.is_file())
        elif path.is_file() and path.suffix == ".py":
            files.add(path)
    return sorted(files)


def scan_paths(paths: Iterable[Path]) -> list[Violation]:
    violations: list[Violation] = []
    for path in collect_test_files(paths):
        file_violations, _ = scan_file(path)
        violations.extend(file_violations)
    return violations


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve()))
    except ValueError:
        return str(path)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Reject false-green Python tests before they reach CI.",
    )
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        default=[Path("backend/tests")],
        help="Python test files or directories (default: backend/tests)",
    )
    args = parser.parse_args(argv)

    missing = [path for path in args.paths if not path.exists()]
    if missing:
        parser.error("path does not exist: " + ", ".join(str(path) for path in missing))

    files = collect_test_files(args.paths)
    violations: list[Violation] = []
    test_count = 0
    for path in files:
        file_violations, file_test_count = scan_file(path)
        violations.extend(file_violations)
        test_count += file_test_count

    for violation in violations:
        print(
            f"{_display_path(violation.path)}:{violation.line}: "
            f"{violation.code} {violation.test_name} - {violation.message}"
        )
    print(
        f"Test quality: {len(files)} file(s), {test_count} test(s), "
        f"{len(violations)} violation(s)"
    )
    return 1 if violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
