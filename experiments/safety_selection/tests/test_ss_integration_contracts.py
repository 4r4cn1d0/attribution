"""Lead integration regressions for the three bounded post-author review findings."""
import copy
import pytest
from experiments.safety_selection.scoring import normalized_label_scores
from experiments.safety_selection.config import load_data_config, validate_data_config, ConfigError
from experiments.safety_selection.selector_view import _validate_static, SelectorViewError
from pathlib import Path


def test_equal_extreme_label_likelihoods_remain_normalized():
    result = normalized_label_scores(dict.fromkeys(('Safe', 'Unsafe', 'Controversial'), -1e20))
    assert sum(result.values()) == pytest.approx(1)
    assert list(result.values()) == pytest.approx([1/3]*3)


def test_date_provenance_cannot_export_construction_labels():
    config = load_data_config(Path(__file__).parents[1]/'configs/study-v2-data.json')
    for value in ('Unsafe', 'ToxicChat-risk'):
        bad = copy.deepcopy(config)
        bad['provenance']['risk'] = value
        with pytest.raises(ConfigError): validate_data_config(bad)
