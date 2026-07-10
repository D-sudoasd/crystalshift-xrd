from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).parents[1] / "app.py"
NAV_OPTIONS = ["Pattern", "Peaks", "F2 evolution", "Sweep", "Method"]
RANGE_TEXTS = {
    "Wyckoff y valid range: 0.000 to 0.500",
    "shuffle_signed = 2(y - 0.25), range: -0.500 to +0.500",
    "shuffle_magnitude = abs(shuffle_signed), range: 0.000 to 0.500",
    "Default Ti-Nb lower-branch sweep: y=0.167..0.250, shuffle_magnitude=0.000..0.166",
}
LOWER_BRANCH_NOTE = "Lower branch: y = 0.25 - shuffle_magnitude / 2"


def _app() -> AppTest:
    return AppTest.from_file(str(APP_PATH))


def test_streamlit_app_starts_without_running_sweep() -> None:
    app = _app()
    with patch(
        "orthoxrd.batch.generate_sweep",
        side_effect=AssertionError("Pattern view must not run a sweep"),
    ):
        app.run(timeout=30)
    assert not app.exception


def test_core_inputs_and_advanced_controls_are_in_main_page() -> None:
    app = _app()
    app.run(timeout=30)

    main_number_labels = {item.label for item in app.main.number_input}
    main_select_labels = {item.label for item in app.main.selectbox}
    sidebar_labels = {item.label for item in app.sidebar.selectbox}

    assert {
        "Energy (keV)",
        "a (A)",
        "b (A)",
        "c (A)",
        "Wyckoff y (0.000-0.500)",
        "Basal shuffle magnitude (0.000-0.500)",
    } <= main_number_labels
    assert {"Incident source", "Lattice preset", "Atomic scattering"} <= main_select_labels
    assert not sidebar_labels


def test_navigation_uses_segmented_control_and_renders_only_active_view() -> None:
    app = _app()
    app.run(timeout=30)

    assert len(app.main.segmented_control) >= 1
    navigation = app.main.segmented_control[0]
    assert navigation.options == NAV_OPTIONS
    assert navigation.value == "Pattern"
    assert not app.main.tabs
    assert "Run sweep" not in {button.label for button in app.main.button}


def test_pattern_exposes_static_live_mode_and_display_range() -> None:
    app = _app()
    app.run(timeout=30)

    segmented_labels = {item.label for item in app.main.segmented_control}
    number_labels = {item.label for item in app.main.number_input}

    assert "Pattern mode" in segmented_labels
    assert {"X minimum", "X maximum"} <= number_labels


def test_live_controls_do_not_mix_widget_defaults_with_session_state(caplog) -> None:
    app = _app()
    app.run(timeout=30)
    mode = next(
        item for item in app.main.segmented_control if item.label == "Pattern mode"
    )
    with patch("orthoxrd.ui_live.render_live_component"):
        mode.select("Live evolution").run(timeout=30)

    assert not app.exception
    assert {
        "Live start",
        "Live stop",
        "Live step",
        "Preview points",
    } <= {item.label for item in app.main.number_input}
    assert not any(
        "created with a default value but also had its value set" in record.message
        for record in caplog.records
    )

def test_incident_source_switches_between_energy_and_wavelength() -> None:
    app = _app()
    app.run(timeout=30)

    incident_source = next(box for box in app.main.selectbox if box.label == "Incident source")
    incident_source.select("Custom wavelength").run(timeout=30)

    main_number_labels = {item.label for item in app.main.number_input}
    assert "Wavelength (A)" in main_number_labels
    assert "Energy (keV)" not in main_number_labels


def test_structure_range_note_is_visible() -> None:
    app = _app()
    app.run(timeout=30)

    rendered_text = _all_text(app)
    for expected in RANGE_TEXTS:
        assert expected in rendered_text


def test_sweep_is_explicit_and_supports_all_axes() -> None:
    app = _app()
    app.run(timeout=30)
    app.main.segmented_control[0].select("Sweep").run(timeout=30)

    button_labels = {button.label for button in app.main.button}
    axis = next(box for box in app.main.selectbox if box.label == "Sweep axis")
    assert "Run sweep" in button_labels
    assert "Download sweep ZIP" not in {item.label for item in app.get("download_button")}
    assert axis.options == [
        "Wyckoff y",
        "Shuffle magnitude",
        "Lattice a",
        "Lattice b",
        "Lattice c",
        "Energy",
        "Wavelength",
    ]


def test_sweep_shuffle_defaults_and_branch_note() -> None:
    app = _app()
    app.run(timeout=30)
    app.main.segmented_control[0].select("Sweep").run(timeout=30)

    axis = next(box for box in app.main.selectbox if box.label == "Sweep axis")
    axis.select("Shuffle magnitude").run(timeout=30)

    input_values = {item.label: item.value for item in app.main.number_input}
    assert input_values["Sweep start"] == 0.0
    assert input_values["Sweep stop"] == 0.166
    assert input_values["Sweep step"] == 0.001
    assert LOWER_BRANCH_NOTE in _all_text(app)
    assert "Shuffle branch" in {item.label for item in app.main.selectbox}


def test_local_sweep_normalization_displays_comparison_warning() -> None:
    app = _app()
    app.run(timeout=30)
    app.main.segmented_control[0].select("Sweep").run(timeout=30)

    normalization = next(box for box in app.main.selectbox if box.label == "Heatmap normalization")
    normalization.select("Local per step").run(timeout=30)
    assert "cannot compare amplitude between steps" in _all_text(app)


def test_f2_view_does_not_run_batch_engine() -> None:
    app = _app()
    with patch(
        "orthoxrd.batch.generate_sweep",
        side_effect=AssertionError("F2 view must not run a sweep"),
    ):
        app.run(timeout=30)
        app.main.segmented_control[0].select("F2 evolution").run(timeout=30)
    assert not app.exception


def test_sweep_result_becomes_stale_after_structure_change() -> None:
    app = _app()
    app.run(timeout=30)
    app.main.segmented_control[0].select("Sweep").run(timeout=30)

    run_button = next(button for button in app.main.button if button.label == "Run sweep")
    run_button.click().run(timeout=30)
    assert not app.exception
    assert "Sweep result matches the active configuration." in _all_text(app)

    y_input = next(
        item for item in app.main.number_input if item.label == "Wyckoff y (0.000-0.500)"
    )
    y_input.set_value(0.2).run(timeout=30)
    assert "Result is stale because the active configuration changed." in _all_text(app)
    prepare = next(button for button in app.main.button if button.label == "Prepare sweep ZIP")
    assert prepare.disabled


def _all_text(app: AppTest) -> str:
    values: list[str] = []
    for collection in (app.main.markdown, app.main.caption, app.main.info, app.main.warning):
        values.extend(str(item.value) for item in collection if item.value)
    values.extend(button.label for button in app.main.button)
    return "\n".join(values)
