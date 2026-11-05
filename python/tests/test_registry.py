import glob
import json
import os

import registry
from explore import load_spec


def test_registry_covers_config_and_is_valid():
    assert registry.validate(registry.load()) == []


def test_exploration_specs_only_vary_explored_or_numerical_parameters():
    params = registry.load()["parameters"]
    for path in glob.glob(os.path.join(os.path.dirname(os.path.dirname(__file__)), "specs", "*.json")):
        with open(path) as handle:
            spec = json.load(handle)
        for name in spec["parameters"]:
            assert params[name]["status"] in registry.SPEC_STATUSES, f"{path}: {name} is {params[name]['status']}"


def test_generated_spec_is_a_valid_exploration_spec(tmp_path):
    reg = registry.load()
    spec = registry.make_spec(reg, n_points=10, base={"max_steps": 1000})
    path = tmp_path / "spec.json"
    path.write_text(json.dumps(spec))
    loaded = load_spec(str(path))
    assert set(loaded["parameters"]) == set(registry.explored(reg))


def test_hypotheses_doc_is_up_to_date():
    with open(registry.HYPOTHESES_PATH, encoding="utf-8") as handle:
        assert handle.read() == registry.render_doc(registry.load()), "run: python registry.py doc"
