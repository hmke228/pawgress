"""The reserved components must import without external services or dependencies."""

from importlib import import_module

import pytest


@pytest.mark.parametrize(
    "module_name", ["cli", "ai", "rag", "behavioral_comparison", "storage"]
)
def test_component_import(module_name: str) -> None:
    module = import_module(f"pawgress.{module_name}")
    assert module.__name__ == f"pawgress.{module_name}"
