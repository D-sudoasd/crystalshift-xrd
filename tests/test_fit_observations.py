from __future__ import annotations

import pytest

from orthoxrd.fit_models import FitError
from orthoxrd.fit_observations import (
    OBSERVATION_CSV_TEMPLATE,
    observation_csv_editor_template,
    observation_csv_template,
    parse_observation_csv,
)


def test_template_is_stable_and_documented() -> None:
    text = observation_csv_template()
    assert text == OBSERVATION_CSV_TEMPLATE
    assert text.startswith("h,k,l,I_obs")
    assert "line" in text.splitlines()[0]
    assert "weight" in text.splitlines()[0]
    assert "sigma" in text.splitlines()[0]
    assert "notes" in text.splitlines()[0]


def test_editor_template_is_header_only_while_download_keeps_examples() -> None:
    editor_text = observation_csv_editor_template()

    assert editor_text == OBSERVATION_CSV_TEMPLATE.splitlines(keepends=True)[0]
    assert len(parse_observation_csv(observation_csv_template())) == 3


def test_valid_csv_parses_to_observation_records() -> None:
    csv_text = """h,k,l,I_obs,line,weight,sigma,notes
0,2,0,100.0,line_00,,,strong
1,1,1,250.5,,,,
2,0,0,80,,,2.0,with sigma
"""
    observations = parse_observation_csv(csv_text)
    assert len(observations) == 3
    first = observations[0]
    assert (first.h, first.k, first.l) == (0, 2, 0)
    assert first.I_obs == pytest.approx(100.0)
    assert first.line == "line_00"
    assert first.notes == "strong"
    assert first.row == 2
    assert observations[2].sigma == pytest.approx(2.0)
    assert observations[2].weight is None


def test_line_id_column_is_accepted() -> None:
    csv_text = """h,k,l,I_obs,line_id
0,2,0,10,Ka1
1,1,1,20,Ka1
"""
    observations = parse_observation_csv(csv_text)
    assert observations[0].line == "Ka1"
    assert observations[1].line == "Ka1"


def test_missing_required_column_raises() -> None:
    with pytest.raises(FitError) as exc_info:
        parse_observation_csv("h,k,l\n0,2,0\n")
    assert any(issue.column == "I_obs" for issue in exc_info.value.issues)


def test_empty_table_raises() -> None:
    with pytest.raises(FitError, match="at least one observation"):
        parse_observation_csv("h,k,l,I_obs\n")


def test_non_positive_i_obs_raises_with_row() -> None:
    csv_text = """h,k,l,I_obs
0,2,0,10
1,1,1,0
"""
    with pytest.raises(FitError) as exc_info:
        parse_observation_csv(csv_text)
    assert any(
        issue.row == 3 and issue.column == "I_obs" for issue in exc_info.value.issues
    )


def test_bad_types_raise_with_row_identity() -> None:
    csv_text = """h,k,l,I_obs
a,2,0,10
0,2,0,x
"""
    with pytest.raises(FitError) as exc_info:
        parse_observation_csv(csv_text)
    rows = {issue.row for issue in exc_info.value.issues}
    assert 2 in rows
    assert 3 in rows


def test_unknown_column_is_rejected() -> None:
    with pytest.raises(FitError) as exc_info:
        parse_observation_csv("h,k,l,I_obs,foo\n0,2,0,1,bar\n")
    assert any(issue.column == "foo" for issue in exc_info.value.issues)


def test_count_csv_data_rows_helper() -> None:
    from orthoxrd.ui_fit import MAX_OBS_UPLOAD_ROWS, _count_csv_data_rows

    assert _count_csv_data_rows("h,k,l,I_obs\n1,1,0,1\n\n0,2,0,2\n") == 2
    assert MAX_OBS_UPLOAD_ROWS == 500


def test_optional_weight_and_sigma_preserved() -> None:
    csv_text = """h,k,l,I_obs,weight,sigma
0,2,0,10,1.5,
1,1,1,20,,0.5
"""
    observations = parse_observation_csv(csv_text)
    assert observations[0].weight == pytest.approx(1.5)
    assert observations[0].sigma is None
    assert observations[1].weight is None
    assert observations[1].sigma == pytest.approx(0.5)


def test_template_parses_successfully() -> None:
    observations = parse_observation_csv(observation_csv_template())
    assert len(observations) == 3
    assert all(obs.I_obs > 0 for obs in observations)


def test_blank_line_preserves_physical_row_numbers() -> None:
    # Physical lines: 1=header, 2=good, 3=blank, 4=bad I_obs → error on row 4.
    csv_text = """h,k,l,I_obs
0,2,0,10

1,1,1,0
"""
    with pytest.raises(FitError) as exc_info:
        parse_observation_csv(csv_text)
    assert any(
        issue.row == 4 and issue.column == "I_obs" for issue in exc_info.value.issues
    )


def test_blank_line_row_identity_on_valid_parse() -> None:
    csv_text = """h,k,l,I_obs
0,2,0,10

1,1,1,20
"""
    observations = parse_observation_csv(csv_text)
    assert [obs.row for obs in observations] == [2, 4]


def test_padded_header_is_rejected() -> None:
    with pytest.raises(FitError) as exc_info:
        parse_observation_csv("h,k,l, I_obs\n0,2,0,10\n1,1,1,20\n")
    assert any(
        "whitespace" in issue.message.lower() for issue in exc_info.value.issues
    )


def test_conflicting_line_and_line_id_raises() -> None:
    csv_text = """h,k,l,I_obs,line,line_id
0,2,0,10,Ka1,line_00
1,1,1,20,Ka1,Ka1
"""
    with pytest.raises(FitError) as exc_info:
        parse_observation_csv(csv_text)
    assert any(
        issue.row == 2 and "disagree" in issue.message
        for issue in exc_info.value.issues
    )
