import ast
import json
from pathlib import Path

import pytest
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SOURCE_PATHS = [
    PROJECT_ROOT / "main.py",
    *(PROJECT_ROOT / "screens").glob("*.py"),
    *(PROJECT_ROOT / "services").glob("*.py"),
]


@pytest.mark.parametrize(
    "source_path",
    PYTHON_SOURCE_PATHS,
    ids=lambda path: str(path.relative_to(PROJECT_ROOT)),
)
def test_python_source_has_valid_syntax(source_path):
    source = source_path.read_text(encoding="utf-8")

    ast.parse(source, filename=str(source_path))


def test_json_configuration_is_valid():
    config_path = PROJECT_ROOT / "camera_config.json"

    config = json.loads(config_path.read_text(encoding="utf-8"))

    assert isinstance(config, dict)
    assert {"device_index", "width", "height"} <= config.keys()


def test_button_configuration_references_existing_sources():
    config_path = PROJECT_ROOT / "buttons.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    assert isinstance(config, dict)
    assert config
    for button_name, button in config.items():
        assert isinstance(button, dict), button_name
        assert button.get("button_text"), button_name
        source_path = PROJECT_ROOT / button.get("button_file", "")
        assert source_path.is_file(), f"Missing source file: {source_path}"
