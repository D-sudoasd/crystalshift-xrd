from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from orthoxrd.fit_observations import OBSERVATION_CSV_TEMPLATE
from orthoxrd.i18n import DEFAULT_LANG
from orthoxrd.locales.en import EN_HELP, EN_TEXT
from orthoxrd.locales.zh import ZH_HELP, ZH_TEXT

APP_PATH = Path(__file__).parents[1] / "app.py"
NAV_OPTIONS = [
    ZH_TEXT["nav.pattern"],
    ZH_TEXT["nav.peaks"],
    ZH_TEXT["nav.f2"],
    ZH_TEXT["nav.sweep"],
    ZH_TEXT["nav.fit"],
    ZH_TEXT["nav.method"],
]
RANGE_TEXTS = {
    ZH_TEXT["structure.range_y"].format(ymin=0.0, ymax=0.5),
    ZH_TEXT["structure.range_signed"].format(smin=-0.5, smax=0.5),
    ZH_TEXT["structure.range_mag"].format(smin=0.0, smax=0.5),
    ZH_TEXT["structure.range_tinb"].format(ymin=0.167, ymax=0.25, smin=0.0, smax=0.166),
}
LOWER_BRANCH_NOTE = ZH_TEXT["sweep.branch_lower"]



def _app() -> AppTest:
    return AppTest.from_file(str(APP_PATH))


def test_default_language_is_chinese() -> None:
    assert DEFAULT_LANG == "zh"
    assert ZH_TEXT["nav.pattern"] == "衍射谱"


def test_locale_catalogs_have_matching_keys() -> None:
    assert set(EN_TEXT) == set(ZH_TEXT)
    assert set(EN_HELP) == set(ZH_HELP)
    assert ZH_TEXT["plot.trace.bragg"]
    assert EN_TEXT["f2.x_title.signed_shuffle"] == "signed shuffle = 2(y - 0.25)"
    assert "calculated units" in EN_TEXT["plot.y_title.model"]


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
        ZH_TEXT["radiation.energy"],
        ZH_TEXT["structure.a"],
        ZH_TEXT["structure.b"],
        ZH_TEXT["structure.c"],
        ZH_TEXT["structure.y"].format(ymin=0.0, ymax=0.5),
        ZH_TEXT["structure.shuffle"].format(smin=0.0, smax=0.5),
    } <= main_number_labels
    assert {
        ZH_TEXT["radiation.source"],
        ZH_TEXT["structure.preset"],
        ZH_TEXT["advanced.scattering"],
    } <= main_select_labels
    assert not sidebar_labels


def test_first_screen_requires_input_review_and_shows_active_model_details() -> None:
    app = _app()
    app.run(timeout=30)

    rendered_text = _all_text(app)
    assert "分析或导出前必须核对" in rendered_text
    assert "成分散射因子" in rendered_text
    assert "Ti:0.64, Nb:0.24, Zr:0.04, Sn:0.08" in rendered_text
    assert "2θ 1–20°" in rendered_text
    assert "Pseudo-Voigt · FWHM 0.0600°" in rendered_text
    assert "LP 开 · 多重度 开 · 体积 1/V 开" in rendered_text


def test_advanced_settings_explain_impact_and_localize_profile_options() -> None:
    app = _app()
    app.run(timeout=30)

    assert "这些设置会改变峰是否出现、峰形和理论强度" in _all_text(app)
    profile = next(
        item for item in app.main.selectbox if item.label == ZH_TEXT["advanced.profile"]
    )
    assert set(profile.options) == {"Pseudo-Voigt", "高斯", "洛伦兹"}


def _navigation(app: AppTest):
    return next(
        item
        for item in app.main.segmented_control
        if list(item.options) == NAV_OPTIONS
    )


def test_navigation_uses_segmented_control_and_renders_only_active_view() -> None:
    app = _app()
    app.run(timeout=30)

    navigation = _navigation(app)
    assert list(navigation.options) == NAV_OPTIONS
    assert navigation.value in {"pattern", ZH_TEXT["nav.pattern"]}
    assert not app.main.tabs
    assert ZH_TEXT["sweep.run"] not in {button.label for button in app.main.button}


def test_peaks_view_explains_when_filters_match_no_rows() -> None:
    app = _app()
    app.run(timeout=30)
    _select_view(app, "peaks")

    hkl_filter = next(
        item for item in app.main.text_input if item.label == ZH_TEXT["peaks.hkl_filter"]
    )
    hkl_filter.set_value("999").run(timeout=30)

    assert "当前筛选没有匹配的峰" in _all_text(app)


def test_pattern_exposes_static_live_mode_and_display_range() -> None:
    app = _app()
    app.run(timeout=30)

    segmented_labels = {item.label for item in app.main.segmented_control}
    number_labels = {item.label for item in app.main.number_input}

    assert ZH_TEXT["pattern.mode"] in segmented_labels
    assert {ZH_TEXT["plot.x_min"], ZH_TEXT["plot.x_max"]} <= number_labels


def test_live_controls_do_not_mix_widget_defaults_with_session_state(caplog) -> None:
    app = _app()
    app.run(timeout=30)
    mode = next(
        item for item in app.main.segmented_control if item.label == ZH_TEXT["pattern.mode"]
    )
    with patch("orthoxrd.ui_live.render_live_component"):
        mode.select("live").run(timeout=30)

    assert not app.exception
    assert {
        ZH_TEXT["live.start"],
        ZH_TEXT["live.stop"],
        ZH_TEXT["live.step"],
        ZH_TEXT["live.points"],
    } <= {item.label for item in app.main.number_input}
    assert not any(
        "created with a default value but also had its value set" in record.message
        for record in caplog.records
    )


def test_incident_source_switches_between_energy_and_wavelength() -> None:
    app = _app()
    app.run(timeout=30)

    incident_source = next(
        box for box in app.main.selectbox if box.label == ZH_TEXT["radiation.source"]
    )
    incident_source.select("Custom wavelength").run(timeout=30)

    main_number_labels = {item.label for item in app.main.number_input}
    assert ZH_TEXT["radiation.wavelength"] in main_number_labels
    assert ZH_TEXT["radiation.energy"] not in main_number_labels


def test_structure_range_note_is_visible() -> None:
    app = _app()
    app.run(timeout=30)

    rendered_text = _all_text(app)
    for expected in RANGE_TEXTS:
        assert expected in rendered_text


def test_structure_readout_shows_the_current_shuffle_branch() -> None:
    app = _app()
    app.run(timeout=30)
    assert "当前下分支" in _all_text(app)

    y_input = next(
        item
        for item in app.main.number_input
        if item.label == ZH_TEXT["structure.y"].format(ymin=0.0, ymax=0.5)
    )
    y_input.set_value(0.3).run(timeout=30)

    assert "当前上分支" in _all_text(app)

    y_input = next(
        item
        for item in app.main.number_input
        if item.label == ZH_TEXT["structure.y"].format(ymin=0.0, ymax=0.5)
    )
    y_input.set_value(0.25).run(timeout=30)

    assert "当前零-shuffle 参考点" in _all_text(app)
    branch = next(
        item
        for item in app.main.segmented_control
        if item.label == ZH_TEXT["structure.branch"]
    )
    assert branch.value == "upper"

    shuffle = next(
        item
        for item in app.main.number_input
        if item.label
        == ZH_TEXT["structure.shuffle"].format(smin=0.0, smax=0.5)
    )
    shuffle.set_value(0.1).run(timeout=30)
    y_input = next(
        item
        for item in app.main.number_input
        if item.label == ZH_TEXT["structure.y"].format(ymin=0.0, ymax=0.5)
    )
    assert abs(float(y_input.value) - 0.3) < 1e-12
    assert "当前上分支" in _all_text(app)


def _select_view(app: AppTest, view: str) -> None:
    # AppTest exposes format_func labels in options but select() needs the stable code.
    _navigation(app).select(view).run(timeout=30)


def test_sweep_is_explicit_and_supports_all_axes() -> None:
    app = _app()
    app.run(timeout=30)
    _select_view(app, "sweep")

    button_labels = {button.label for button in app.main.button}
    axis = next(box for box in app.main.selectbox if box.label == ZH_TEXT["sweep.axis"])
    assert ZH_TEXT["sweep.run"] in button_labels
    assert ZH_TEXT["sweep.download"] not in {
        item.label for item in app.get("download_button")
    }
    assert len(list(axis.options)) == 7
    assert set(axis.options) in (
        {
            "y",
            "shuffle_magnitude",
            "a_A",
            "b_A",
            "c_A",
            "energy_keV",
            "wavelength_A",
        },
        {
            ZH_TEXT["axis.y"],
            ZH_TEXT["axis.shuffle_magnitude"],
            ZH_TEXT["axis.a_A"],
            ZH_TEXT["axis.b_A"],
            ZH_TEXT["axis.c_A"],
            ZH_TEXT["axis.energy_keV"],
            ZH_TEXT["axis.wavelength_A"],
        },
    )


def test_sweep_shuffle_defaults_and_branch_note() -> None:
    app = _app()
    app.run(timeout=30)
    _select_view(app, "sweep")

    axis = next(box for box in app.main.selectbox if box.label == ZH_TEXT["sweep.axis"])
    axis.select("shuffle_magnitude").run(timeout=30)

    input_values = {item.label: item.value for item in app.main.number_input}
    assert input_values[ZH_TEXT["sweep.start"]] == 0.0
    assert input_values[ZH_TEXT["sweep.stop"]] == 0.166
    assert input_values[ZH_TEXT["sweep.step"]] == 0.001
    assert LOWER_BRANCH_NOTE in _all_text(app)
    assert ZH_TEXT["sweep.branch"] in {item.label for item in app.main.selectbox}


def test_local_sweep_normalization_displays_comparison_warning() -> None:
    app = _app()
    app.run(timeout=30)
    _select_view(app, "sweep")

    normalization = next(
        box for box in app.main.selectbox if box.label == ZH_TEXT["sweep.normalization"]
    )
    normalization.select("local").run(timeout=30)
    assert ZH_TEXT["sweep.local_warning"] in _all_text(app)


def test_f2_view_does_not_run_batch_engine() -> None:
    app = _app()
    with patch(
        "orthoxrd.batch.generate_sweep",
        side_effect=AssertionError("F2 view must not run a sweep"),
    ):
        app.run(timeout=30)
        _select_view(app, "f2")
    assert not app.exception


def test_method_view_explains_first_use_order_and_every_result_view() -> None:
    app = _app()
    app.run(timeout=30)
    _select_view(app, "method")

    rendered_text = _all_text(app)
    assert "首次使用顺序" in rendered_text
    assert "分析或导出前先核对" in rendered_text
    assert "各分区用途" in rendered_text
    for view_name in ("衍射谱", "布拉格峰", "F² 演化", "参数扫描", "峰强拟合", "方法与解读"):
        assert view_name in rendered_text


def test_fit_view_is_lazy_and_does_not_run_sweep() -> None:
    app = _app()
    with patch(
        "orthoxrd.batch.generate_sweep",
        side_effect=AssertionError("Fit view must not run a sweep"),
    ):
        app.run(timeout=30)
        _select_view(app, "fit")
    assert not app.exception
    button_labels = {button.label for button in app.main.button}
    assert ZH_TEXT["fit.run"] in button_labels
    assert ZH_TEXT["fit.apply"] not in button_labels  # no result yet
    assert ZH_TEXT["fit.empty"] in _all_text(app)
    assert ZH_TEXT["nav.fit"] in NAV_OPTIONS
    # Template download and observation editor should be present before Run.
    assert ZH_TEXT["fit.obs.template"] in {
        item.label for item in app.get("download_button")
    } or ZH_TEXT["fit.obs.template"] in button_labels
    editor = next(
        item for item in app.main.text_area if item.label == ZH_TEXT["fit.obs.editor"]
    )
    assert str(editor.value) == OBSERVATION_CSV_TEMPLATE.splitlines(keepends=True)[0]
    run = next(button for button in app.main.button if button.label == ZH_TEXT["fit.run"])
    assert run.disabled


def test_fit_requires_two_valid_observations_before_run() -> None:
    app = _app()
    app.run(timeout=30)
    _select_view(app, "fit")
    editor = next(
        item for item in app.main.text_area if item.label == ZH_TEXT["fit.obs.editor"]
    )

    editor.set_value("h,k,l,I_obs,line,weight,sigma,notes\n0,2,1,10.0,,,,\n").run(
        timeout=30
    )
    run = next(button for button in app.main.button if button.label == ZH_TEXT["fit.run"])
    assert run.disabled

    editor = next(
        item for item in app.main.text_area if item.label == ZH_TEXT["fit.obs.editor"]
    )
    editor.set_value(
        "h,k,l,I_obs,line,weight,sigma,notes\n"
        "0,2,1,10.0,,,,\n1,1,0,8.0,,,,\n"
    ).run(timeout=30)
    run = next(button for button in app.main.button if button.label == ZH_TEXT["fit.run"])
    assert not run.disabled


def test_fit_rejects_two_observations_unmatched_by_the_active_model_before_run() -> None:
    app = _app()
    app.run(timeout=30)
    _select_view(app, "fit")
    editor = next(
        item for item in app.main.text_area if item.label == ZH_TEXT["fit.obs.editor"]
    )

    editor.set_value(
        "h,k,l,I_obs,line,weight,sigma,notes\n"
        "99,99,99,10.0,,,,\n98,98,98,8.0,,,,\n"
    ).run(timeout=30)

    run = next(button for button in app.main.button if button.label == ZH_TEXT["fit.run"])
    assert run.disabled
    assert "unmatched HKL" in _all_text(app)


def _structure_y_input(app: AppTest):
    return next(
        item
        for item in app.main.number_input
        if item.label == ZH_TEXT["structure.y"].format(ymin=0.0, ymax=0.5)
    )


def _structure_a_input(app: AppTest):
    return next(item for item in app.main.number_input if item.label == ZH_TEXT["structure.a"])


def _run_fit(app: AppTest) -> None:
    editor = next(
        item for item in app.main.text_area if item.label == ZH_TEXT["fit.obs.editor"]
    )
    editor.set_value(OBSERVATION_CSV_TEMPLATE).run(timeout=30)
    run_button = next(
        button for button in app.main.button if button.label == ZH_TEXT["fit.run"]
    )
    run_button.click().run(timeout=60)
    assert not app.exception


def test_fit_run_does_not_mutate_structure_y() -> None:
    app = _app()
    app.run(timeout=30)
    y_before = float(_structure_y_input(app).value)
    _select_view(app, "fit")
    _run_fit(app)
    assert ZH_TEXT["fit.apply"] in {button.label for button in app.main.button}
    assert float(_structure_y_input(app).value) == y_before


def test_fit_renders_four_diagnostics_and_coordinate_toggle() -> None:
    app = _app()
    app.run(timeout=30)
    _select_view(app, "fit")
    assert ZH_TEXT.get("fit.context.header", "fit.context.header") in _all_text(app)

    _run_fit(app)
    assert len(app.main.get("plotly_chart")) == 4
    display_axis = next(
        item
        for item in app.main.segmented_control
        if list(item.options)
        == [
            ZH_TEXT["axis.y"],
            ZH_TEXT["axis.signed_shuffle"],
            ZH_TEXT["axis.shuffle_magnitude"],
        ]
    )
    display_axis.select("shuffle_magnitude").run(timeout=30)

    assert not app.exception
    assert len(app.main.get("plotly_chart")) == 4


def test_fit_apply_writes_y_star_only_on_click() -> None:
    app = _app()
    app.run(timeout=30)
    y_before = float(_structure_y_input(app).value)
    _select_view(app, "fit")
    _run_fit(app)
    assert float(_structure_y_input(app).value) == y_before

    apply_button = next(
        button for button in app.main.button if button.label == ZH_TEXT["fit.apply"]
    )
    apply_button.click().run(timeout=30)
    assert not app.exception
    y_after = float(_structure_y_input(app).value)
    assert y_after != y_before
    structure_branch = next(
        item
        for item in app.main.segmented_control
        if item.label == ZH_TEXT["structure.branch"]
    )
    if y_after < 0.25:
        assert structure_branch.value == "lower"
    elif y_after > 0.25:
        assert structure_branch.value == "upper"
    # Apply commits y* without marking the fit stale (y is not a fit input).
    page = _all_text(app)
    assert "拟合结果与当前配置及观测表一致" in page
    assert "过期" not in page or "已相对当前配置" not in page
    assert any("y*" in str(item.value) for item in app.main.success)


def test_fit_result_stale_after_lattice_change_disables_prepare() -> None:
    app = _app()
    app.run(timeout=30)
    _select_view(app, "fit")
    _run_fit(app)
    assert "拟合结果与当前配置及观测表一致" in _all_text(app)

    a_input = _structure_a_input(app)
    a_input.set_value(float(a_input.value) + 0.05).run(timeout=30)
    assert not app.exception
    assert "结果已过期" in _all_text(app) or "过期" in _all_text(app)
    prepare = next(
        button for button in app.main.button if button.label == ZH_TEXT["fit.prepare"]
    )
    assert prepare.disabled
    apply = next(
        button for button in app.main.button if button.label == ZH_TEXT["fit.apply"]
    )
    assert apply.disabled


def test_fit_result_stale_after_observation_edit() -> None:
    app = _app()
    app.run(timeout=30)
    _select_view(app, "fit")
    _run_fit(app)
    editor = next(
        item for item in app.main.text_area if item.label == ZH_TEXT["fit.obs.editor"]
    )
    editor.set_value(str(editor.value) + "\n1,1,0,50.0,,,,").run(timeout=30)
    assert not app.exception
    assert "过期" in _all_text(app)
    prepare = next(
        button for button in app.main.button if button.label == ZH_TEXT["fit.prepare"]
    )
    assert prepare.disabled


def test_fit_invalid_y_range_disables_run() -> None:
    app = _app()
    app.run(timeout=30)
    _select_view(app, "fit")
    y_start = next(
        item for item in app.main.number_input if item.label == ZH_TEXT["fit.y_start"]
    )
    y_stop = next(
        item for item in app.main.number_input if item.label == ZH_TEXT["fit.y_stop"]
    )
    y_start.set_value(0.4).run(timeout=30)
    y_stop.set_value(0.1).run(timeout=30)
    assert not app.exception
    assert ZH_TEXT["fit.err.y_range"] in _all_text(app)
    run_button = next(
        button for button in app.main.button if button.label == ZH_TEXT["fit.run"]
    )
    assert run_button.disabled


def test_fit_prepare_zip_enabled_after_run_and_after_apply() -> None:
    app = _app()
    app.run(timeout=30)
    _select_view(app, "fit")
    _run_fit(app)
    prepare = next(
        button for button in app.main.button if button.label == ZH_TEXT["fit.prepare"]
    )
    assert not prepare.disabled
    prepare.click().run(timeout=60)
    assert not app.exception
    downloads = {item.label for item in app.get("download_button")}
    assert ZH_TEXT["fit.download"] in downloads

    apply_button = next(
        button for button in app.main.button if button.label == ZH_TEXT["fit.apply"]
    )
    apply_button.click().run(timeout=30)
    assert not app.exception
    # Apply y* must not stale the fit or drop a prepared export matching signature.
    page = _all_text(app)
    assert "拟合结果与当前配置及观测表一致" in page
    prepare_after = next(
        button for button in app.main.button if button.label == ZH_TEXT["fit.prepare"]
    )
    assert not prepare_after.disabled
    downloads_after = {item.label for item in app.get("download_button")}
    assert ZH_TEXT["fit.download"] in downloads_after


def test_fit_signature_ignores_structure_y_and_profile_knobs() -> None:
    from dataclasses import replace

    from orthoxrd.config import SimulationConfig
    from orthoxrd.fit_models import FitOptions
    from orthoxrd.models import LatticeParameters, RadiationLine
    from orthoxrd.ui_fit import _fit_signature

    base = SimulationConfig(
        lattice=LatticeParameters(a=3.222, b=4.759, c=4.668),
        y=0.25,
        lines=(RadiationLine("Cu Ka1", 1.5406, 1.0),),
        scattering_mode="unit",
        composition=(),
        two_theta_min=5.0,
        two_theta_max=80.0,
        hkl_max=4,
        min_peak=1.0,
        profile_kind="gaussian",
        fwhm_deg=0.1,
        pseudo_voigt_eta=0.5,
        spectrum_points=100,
        include_lorentz_polarization=True,
        include_multiplicity=True,
        include_cell_volume=False,
    )
    options = FitOptions(y_start=0.0, y_stop=0.5, grid_points=51)
    obs = "h,k,l,I_obs\n1,1,0,10\n0,2,0,20\n"
    sig_base = _fit_signature(base, options, obs)
    sig_y = _fit_signature(replace(base, y=0.18), options, obs)
    sig_profile = _fit_signature(
        replace(base, fwhm_deg=0.3, spectrum_points=400, min_peak=5.0),
        options,
        obs,
    )
    sig_lattice = _fit_signature(
        replace(base, lattice=LatticeParameters(a=3.3, b=4.759, c=4.668)),
        options,
        obs,
    )
    sig_obs = _fit_signature(base, options, obs + "1,1,1,5\n")
    assert sig_base == sig_y == sig_profile
    assert sig_base != sig_lattice
    assert sig_base != sig_obs


def test_sweep_result_becomes_stale_after_structure_change() -> None:
    app = _app()
    app.run(timeout=30)
    _select_view(app, "sweep")

    run_button = next(
        button for button in app.main.button if button.label == ZH_TEXT["sweep.run"]
    )
    run_button.click().run(timeout=30)
    assert not app.exception
    assert "扫描结果与当前配置一致" in _all_text(app)

    y_input = next(
        item
        for item in app.main.number_input
        if item.label == ZH_TEXT["structure.y"].format(ymin=0.0, ymax=0.5)
    )
    y_input.set_value(0.2).run(timeout=30)
    assert "结果已过期" in _all_text(app)
    prepare = next(
        button for button in app.main.button if button.label == ZH_TEXT["sweep.prepare"]
    )
    assert prepare.disabled


def test_csv_and_excel_guidance_is_visible_on_data_views() -> None:
    app = _app()
    app.run(timeout=30)
    assert ZH_TEXT["export.csv_excel_hint.current"] in _all_text(app)

    _select_view(app, "peaks")
    assert ZH_TEXT["export.csv_excel_hint.current"] in _all_text(app)

    _select_view(app, "f2")
    labels = {item.label for item in app.get("download_button")}
    assert {ZH_TEXT["f2.download"], ZH_TEXT["f2.download_excel"]} <= labels
    assert ZH_TEXT["export.csv_excel_hint.f2"] in _all_text(app)


def _all_text(app: AppTest) -> str:
    values: list[str] = []
    for collection in (
        app.main.markdown,
        app.main.caption,
        app.main.info,
        app.main.warning,
        app.main.success,
        app.main.error,
    ):
        values.extend(str(item.value) for item in collection if item.value)
    values.extend(button.label for button in app.main.button)
    return "\n".join(values)
