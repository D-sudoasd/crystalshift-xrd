"""Simplified Chinese UI catalog."""

from __future__ import annotations


def _h(purpose: str, importance: str, example: str, notes: str) -> str:
    return (
        f"【功能】{purpose}\n"
        f"【重要性】{importance}\n"
        f"【新手示例】{example}\n"
        f"【注意事项】{notes}"
    )


ZH_TEXT: dict[str, str] = {
    # Language
    "lang.label": "界面语言",
    "lang.zh": "中文",
    "lang.en": "English",
    "common.on": "开",
    "common.off": "关",
    # App shell
    "app.page_title": "CrystalShift XRD",
    "app.model_tag": "Cmcm 4c | schema 2.2",
    "app.subtitle": "面向晶格、Wyckoff-y、基面 shuffle 与入射辐射的运动学粉末 XRD 理论模型。",
    "app.spinner": "正在计算当前理论模型…",
    "app.summary.a": "a (Å)",
    "app.summary.b": "b (Å)",
    "app.summary.c": "c (Å)",
    "app.summary.y": "Wyckoff y",
    "app.summary.shuffle": "shuffle |s|",
    "app.summary.energy": "能量 (keV)",
    "app.summary.lambda": "波长 λ (Å)",
    "app.summary.hash": "配置哈希",
    "app.active_model.composition_na": "不适用（单位散射体）",
    "app.active_model_details": (
        "**活动模型** · 散射：{scattering} · 成分：{composition} · "
        "2θ {tth_min:g}–{tth_max:g}° · {profile} · FWHM {fwhm:.4f}° · "
        "修正：LP {lp} · 多重度 {multiplicity} · 体积 1/V {volume}"
    ),
    "inputs.required_review": (
        '<div class="xrd-note xrd-note-warn"><strong>分析或导出前必须核对：</strong>'
        "入射辐射、晶格、Wyckoff y、有符号 shuffle 与 shuffle 幅度，以及"
        "「材料与计算设置」中的"
        "散射/成分、2θ 窗口、峰形和强度修正。</div>"
    ),
    # Navigation
    "nav.label": "结果视图",
    "nav.pattern": "衍射谱",
    "nav.peaks": "布拉格峰",
    "nav.f2": "F² 演化",
    "nav.sweep": "参数扫描",
    "nav.fit": "峰强拟合",
    "nav.method": "方法与解读",
    # Axes (shared)
    "axis.y": "Wyckoff y",
    "axis.signed_shuffle": "有符号 shuffle",
    "axis.shuffle_magnitude": "shuffle 幅度",
    "axis.shuffle": "shuffle 幅度",
    "axis.a_A": "晶格常数 a",
    "axis.b_A": "晶格常数 b",
    "axis.c_A": "晶格常数 c",
    "axis.energy_keV": "能量",
    "axis.wavelength_A": "波长",
    "branch.lower": "下分支",
    "branch.upper": "上分支",
    # Radiation
    "radiation.title": "入射辐射",
    "radiation.source": "入射源",
    "radiation.mode.Custom energy": "自定义能量",
    "radiation.mode.Custom wavelength": "自定义波长",
    "radiation.mode.Cu K-alpha doublet": "Cu K-α 双线",
    "radiation.mode.Co K-alpha doublet": "Co K-α 双线",
    "radiation.mode.Mo K-alpha doublet": "Mo K-α 双线",
    "radiation.mode.30 keV synchrotron": "30 keV 同步辐射",
    "radiation.energy": "能量 (keV)",
    "radiation.wavelength": "波长 (Å)",
    "radiation.include_k_alpha2": "包含 K-α2 分量",
    "radiation.primary_wavelength": "主波长：{wavelength:.6f} Å{suffix}",
    "radiation.primary_energy": "主能量：{energy:.4f} keV{suffix}",
    "radiation.primary_line_single": "主辐射线：{label}，λ={wavelength:.6f} Å，E={energy:.4f} keV",
    "radiation.primary_line_doublet": "主线：{primary} ({w1:.1f})，次线：{secondary} ({w2:.1f})",
    "radiation.scaled_suffix": " | 已按 {count} 线源缩放；相对波长与权重保持不变",
    # Structure
    "structure.title": "晶体结构",
    "structure.preset": "晶格预设",
    "structure.a": "a (Å)",
    "structure.b": "b (Å)",
    "structure.c": "c (Å)",
    "structure.y": "Wyckoff y ({ymin:.3f}-{ymax:.3f})",
    "structure.shuffle": "基面 shuffle 幅度 ({smin:.3f}-{smax:.3f})",
    "structure.branch": "shuffle 幅度分支",
    "structure.signed_label": "有符号 shuffle",
    "structure.signed_meta": "2(y − 0.25) · 当前{branch}",
    "structure.branch.lower": "下分支",
    "structure.branch.upper": "上分支",
    "structure.branch.reference": "零-shuffle 参考点",
    "structure.relation_note": (
        "<div class=\"xrd-note\"><strong>y / shuffle 关系</strong> "
        "signed = 2(y − 0.25)；magnitude = abs(signed)。"
        "Ti-Nb 下分支：y={y_min:.3f}..{y_max:.3f}，"
        "magnitude=0..{s_max:.3f}。</div>"
    ),
    "structure.expander": "有效范围与分支说明",
    "structure.range_y": "Wyckoff y 有效范围：{ymin:.3f} 至 {ymax:.3f}",
    "structure.range_signed": "shuffle_signed = 2(y − 0.25)，范围：{smin:.3f} 至 {smax:+.3f}",
    "structure.range_mag": "shuffle_magnitude = abs(shuffle_signed)，范围：{smin:.3f} 至 {smax:.3f}",
    "structure.range_tinb": (
        "默认 Ti-Nb 下分支扫描：y={ymin:.3f}..{ymax:.3f}，"
        "shuffle_magnitude={smin:.3f}..{smax:.3f}"
    ),
    "structure.branch_detail": (
        "下分支：y = 0.25 − shuffle_magnitude / 2；"
        "上分支：y = 0.25 + shuffle_magnitude / 2。"
    ),
    "structure.context.caption": (
        "当前结构：y={y:.6f} | 有符号 shuffle={signed:+.6f} | "
        "shuffle 幅度={magnitude:.6f} | {branch}。"
        "这些坐标调制结构因子与理论强度；谱图/峰表的物理横轴仍为 2θ、q 或 d。"
    ),
    "structure.plot.cell": "Cmcm 晶胞",
    "structure.plot.reference": "y=0.25 参考位点",
    "structure.plot.current": "当前 4c 位点",
    "structure.plot.shuffle_path": "沿 b 轴的 shuffle 路径",
    "structure.plot.shuffle_arrow": "shuffle 方向",
    # Advanced
    "advanced.popover": "材料与计算设置（请核对）",
    "advanced.intro": "这些设置会改变峰是否出现、峰形和理论强度；关闭面板后，当前取值仍会显示在活动模型摘要中。",
    "advanced.scattering_section": "##### 散射模型",
    "advanced.window_section": "##### 模拟窗口",
    "advanced.profile_section": "##### 峰形剖面",
    "advanced.factors_section": "##### 强度修正因子",
    "advanced.scattering": "原子散射",
    "advanced.scattering.composition": "成分散射因子",
    "advanced.scattering.unit": "单位散射体 F²",
    "advanced.unit_caption": "所有位点取 f=1。最适合单独考察解析 F²(y) 趋势。",
    "advanced.composition": "成分分数",
    "advanced.tth_min": "模拟 2θ 下限 (°)",
    "advanced.tth_max": "模拟 2θ 上限 (°)",
    "advanced.hkl_max": "最大 h, k, l",
    "advanced.points": "谱图采样点数",
    "advanced.cutoff": "峰表截断阈值 (%)",
    "advanced.profile": "峰形",
    "advanced.profile.pseudo_voigt": "Pseudo-Voigt",
    "advanced.profile.gaussian": "高斯",
    "advanced.profile.lorentzian": "洛伦兹",
    "advanced.fwhm": "半高宽 FWHM (° 2θ)",
    "advanced.eta": "Pseudo-Voigt η",
    "advanced.lp": "Lorentz–偏振因子 (LP)",
    "advanced.multiplicity": "正交晶系多重度",
    "advanced.volume": "按单胞体积缩放 (1/V)",
    # Pattern
    "pattern.title": "理论粉末衍射谱",
    "pattern.mode": "谱图模式",
    "pattern.mode.static": "静态谱",
    "pattern.mode.live": "实时演化",
    "pattern.axis": "横轴",
    "pattern.intensity": "强度",
    "pattern.intensity.relative": "相对强度",
    "pattern.intensity.model": "模型强度",
    "pattern.display": "显示方式",
    "pattern.display.combined": "叠加",
    "pattern.display.line": "连续谱线",
    "pattern.display.sticks": "棒图",
    "pattern.hkl_labels": "HKL 标注",
    "pattern.live_caption": "滑块每一档对应后端精确预计算帧，不进行帧间插值。",
    "pattern.static_caption": (
        "模型强度为理论计算的未标定强度。"
        "q_primary 与 d_primary 使用主波长换算。"
    ),
    "pattern.download_spectrum": "下载谱图 CSV",
    "pattern.download_peaks": "下载峰表 CSV",
    "export.csv_excel_hint.current": (
        "CSV 用于 Origin/Python 或其它机器处理；如需用 Excel 查看，请使用当前结果 ZIP "
        "中的 analysis.xlsx，以保留 021 等前导零并阅读说明页。"
    ),
    # Plot state
    "plot.display_range": "显示范围",
    "plot.display_caption": "仅裁剪显示。模拟窗口与导出数据行保持不变。",
    "plot.x_min": "X 下限",
    "plot.x_max": "X 上限",
    "plot.y_auto": "自动 Y 轴范围",
    "plot.y_min": "Y 下限",
    "plot.y_max": "Y 上限",
    "plot.reset": "重置显示范围",
    "plot.x_error": "X 上限必须大于 X 下限。",
    "plot.y_error": "Y 上限必须大于 Y 下限。",
    "plot.x_title.2theta": "2θ (°)",
    "plot.x_title.q_primary": "q_primary (Å⁻¹)",
    "plot.x_title.d_primary": "d_primary (Å)",
    "plot.y_title.model": "模型强度 I_model（理论计算单位）",
    "plot.y_title.relative": "相对强度 I_rel (%)",
    "plot.trace.model": "剖面 · 模型",
    "plot.trace.relative": "剖面 · 相对",
    "plot.trace.bragg": "布拉格反射",
    "plot.trace.selected": "已选反射",
    # Peaks
    "peaks.title": "布拉格峰",
    "peaks.caption": (
        "显示 {shown:,} / {total:,} 条计算峰行。"
        "可横向滚动查看全部字段；CSV 导出包含全部列。"
    ),
    "peaks.empty_filtered": "当前筛选没有匹配的峰。请放宽 HKL、辐射线、强度或 2θ 条件。",
    "peaks.selected": "已选 {line} {hkl} | 2θ={two_theta:.6f}° | {series_id}",
    "peaks.hkl_filter": "HKL 过滤",
    "peaks.hkl_placeholder": "例如 110 或 02",
    "peaks.line_filter": "辐射线",
    "peaks.min_irel": "最小 I_rel (%)",
    "peaks.angle_filter": "2θ 过滤 (°)",
    "peaks.download_all": "全部峰 CSV",
    "peaks.download_filtered": "筛选峰 CSV",
    # F2
    "f2.title": "结构因子演化",
    "f2.caption": (
        "Cmcm 4c 单位散射体解析 F²。"
        "有意排除峰形、LP、多重度、成分与体积因子。"
    ),
    "f2.hkls": "HKL 系列（最多 12 条）",
    "f2.axis": "演化坐标轴",
    "f2.branch": "shuffle 分支",
    "f2.empty": "请至少选择一条 HKL 系列。",
    "f2.preview": "数据预览",
    "f2.download": "F² 演化 CSV",
    "f2.download_excel": "F² 演化 Excel",
    "export.csv_excel_hint.f2": (
        "CSV 用于 Origin/Python 或其它机器处理；在 Excel 中请使用 f2_evolution.xlsx，"
        "以保留 021 等前导零，并查看 Parameters 与 Columns 说明页。"
    ),
    "f2.start": "演化起点",
    "f2.stop": "演化终点",
    "f2.points": "演化点数",
    "f2.structure_preview.title": "##### Cmcm 4c 基面位移结构示意",
    "f2.structure_preview.slider": "结构示意预览坐标",
    "f2.structure_preview.caption": (
        "灰色为同一 Cmcm 晶胞中 y=0.25 的零-shuffle 参考位点，青色为当前位点；"
        "位移严格沿 b 轴，单原子 |Δb| = b|y−0.25|。"
        "此滑块只更新结构示意，不写回顶部主结构参数。"
    ),
    "f2.structure_preview.help": (
        "拖动后只预览所选 Wyckoff y、有符号 shuffle 或 shuffle 幅度坐标对应的"
        "真实 4c 位点与位移路径；"
        "不会重算当前模拟或改变导出。"
    ),
    "f2.stop_error": "演化终点必须大于起点。",
    "f2.x_title.y": "Wyckoff y",
    "f2.x_title.signed_shuffle": "有符号 shuffle = 2(y − 0.25)",
    "f2.x_title.shuffle_magnitude": "shuffle 幅度",
    "f2.y_title": "单位散射体 F²",
    # Live
    "live.stale": (
        '<div class="xrd-state xrd-state--warning">实时预览已过期。'
        "请在更改非活动物理量或范围设置后重建。</div>"
    ),
    "live.valid": (
        '<div class="xrd-state xrd-state--valid">实时预览与当前科学配置一致。</div>'
    ),
    "live.rebuild": "重建实时预览",
    "live.stale_caption": "仍保留上一版预览，但交互与导出已禁用。",
    "live.frames_caption": (
        "{frames} 个精确帧 | 每帧 {points} 点 | "
        "{cells:,} 个浏览器预览单元"
    ),
    "live.baseline_caption": "基线 {baseline:.7g} | 当前 {current:.7g}",
    "live.set_baseline": "将当前设为基线",
    "live.spinner": "正在准备精确实时帧…",
    "live.parameter": "实时扫描参数",
    "live.branch": "shuffle 分支",
    "live.start": "实时起点",
    "live.stop": "实时终点",
    "live.step": "实时步长",
    "live.points": "预览点数",
    "live.caption": (
        "滑块在本地切换预计算精确帧。"
        "仅在松开滑块时将最终帧写回 Python 主参数。"
    ),
    "live.export.prepare": "准备实时演化 ZIP",
    "live.export.spinner": "正在构建 schema 2.2 实时分析包…",
    "live.export.caption_prepare": "按需生成全精度实时 ZIP。",
    "live.export.caption_changed": "实时选择已变更，请重新准备 ZIP。",
    "live.export.download": "下载 live_evolution.zip",
    "live.export.size": "{kib:.1f} KiB | SHA-256 {sha}…",
    "live.ui.intensity": "强度",
    "live.ui.global": "全局相对",
    "live.ui.local": "局部相对",
    "live.ui.model": "模型强度",
    "live.ui.difference": "差值",
    "live.ui.baseline": "基线",
    "live.ui.current": "当前",
    "live.ui.aria_canvas": "实时理论 XRD 谱图",
    "live.ui.aria_slider": "实时参数帧",
    # Sweep
    "sweep.title": "参数扫描与轨迹",
    "sweep.empty": "配置扫描参数后点击「运行扫描」。不会自动执行批量计算。",
    "sweep.stale": (
        '<div class="xrd-state xrd-state--warning">'
        "结果已过期：当前配置已变更。"
        "预览仍可查看，但导出已禁用，需重新运行。"
        "</div>"
    ),
    "sweep.valid": (
        '<div class="xrd-state xrd-state--valid">扫描结果与当前配置一致。</div>'
    ),
    "sweep.result_view": "扫描结果视图",
    "sweep.view.heatmap": "热图",
    "sweep.view.waterfall": "瀑布图",
    "sweep.view.peak_evolution": "峰演化",
    "sweep.view.data_preview": "数据预览",
    "sweep.kpi.steps": "步数",
    "sweep.kpi.peak_rows": "峰行数",
    "sweep.kpi.spectrum_cells": "谱图单元数",
    "sweep.kpi.global_max": "全局剖面最大值",
    "sweep.peak_metric": "峰度量",
    "sweep.metric.F2": "F²",
    "sweep.metric.N_F2": "N·F²（多重度 × 结构因子）",
    "sweep.metric.R_hkl_with_LP": "R_hkl（含 LP，理论参考）",
    "sweep.metric.R_hkl_no_LP": "R_hkl_no_LP（理论参考）",
    "sweep.metric.I_model": "模型峰强度",
    "sweep.metric.I_rel_global": "全局相对峰强度",
    "sweep.peak_series": "峰系列（最多 12 条）",
    "sweep.steps_header": "##### 扫描步",
    "sweep.peak_sample_header": "##### 峰演化样例",
    "sweep.preview_caption": "预览最多 500 行峰数据。ZIP 含完整表格。",
    "sweep.prepare": "准备扫描 ZIP",
    "sweep.spinner": "正在将 schema 2.2 文件写入 ZIP…",
    "sweep.prepare_caption": "先运行当前配置，再准备 schema 2.2 ZIP。",
    "sweep.download": "下载扫描 ZIP",
    "sweep.export_size": "{kib:.1f} KiB | SHA-256 {sha}…",
    "sweep.calc_spinner": "正在计算参数扫描…",
    "sweep.err.no_trajectory": "运行前请先选择轨迹 CSV。",
    "sweep.err.incomplete_range": "范围扫描配置不完整。",
    "sweep.spectrum_points": "扫描谱图采样点数",
    "sweep.input_mode": "扫描输入方式",
    "sweep.input.range": "范围扫描",
    "sweep.input.trajectory": "CSV 轨迹",
    "sweep.normalization": "热图归一化",
    "sweep.norm.global": "扫描全局归一化",
    "sweep.norm.local": "逐步局部归一化",
    "sweep.norm.model": "模型强度",
    "sweep.local_warning": (
        "局部归一化会独立重标定每一步；"
        "不能比较不同步之间的振幅。"
    ),
    "sweep.axis": "扫描坐标轴",
    "sweep.branch": "shuffle 分支",
    "sweep.branch_lower": "下分支：y = 0.25 − shuffle_magnitude / 2",
    "sweep.branch_upper": "上分支：y = 0.25 + shuffle_magnitude / 2",
    "sweep.start": "扫描起点",
    "sweep.stop": "扫描终点",
    "sweep.step": "扫描步长",
    "sweep.run": "运行扫描",
    "sweep.estimate": "估计：{steps:,} 步 | {cells:,} 谱图单元 | 最多 {peaks:,} 峰行。",
    "sweep.trajectory_file": "轨迹 CSV",
    "sweep.trajectory_template": "轨迹模板 CSV",
    "sweep.trajectory_caption": (
        "列：step_label, a_A, b_A, c_A, y, shuffle_magnitude, "
        "shuffle_branch, energy_keV, wavelength_A。限制：1–1001 行。"
    ),
    "sweep.display_range": "扫描显示范围",
    "sweep.display_coordinate": "结构显示坐标",
    "sweep.display_coordinate_cross_branch": (
        "该 y 扫描跨过 y=0.25；shuffle 幅度会把上下分支折叠到同一数值，"
        "因此仅提供 y 与有符号 shuffle。"
    ),
    "sweep.display_caption": "仅裁剪显示。ZIP 始终包含完整模拟窗口。",
    "sweep.display_tth_min": "扫描 2θ 下限",
    "sweep.display_tth_max": "扫描 2θ 上限",
    "sweep.display_axis_min": "扫描轴下限",
    "sweep.display_axis_max": "扫描轴上限",
    "sweep.display_reset": "重置扫描显示范围",
    "sweep.display_tth_error": "扫描 2θ 上限必须大于下限。",
    "sweep.display_axis_error": "扫描轴上限必须大于下限。",
    "sweep.plot.i_model": "I 模型",
    "sweep.plot.i_global": "I 全局 (%)",
    "sweep.plot.i_local": "I 局部 (%)",
    "sweep.plot.two_theta": "2θ (°)",
    "sweep.plot.step": "扫描步",
    "sweep.plot.intensity": "强度",
    # Export current
    "export.prepare": "准备当前结果 ZIP",
    "export.spinner": "正在准备当前模拟导出…",
    "export.caption": "Schema 2.2 导出按需生成。",
    "export.expired": "已准备的导出已失效，请重新准备。",
    "export.download": "下载当前 ZIP",
    "export.size": "{kib:.1f} KiB | SHA-256 {sha}…",
    # Discrete peak intensity fit
    "fit.title": "离散峰强拟合",
    "fit.subtitle": (
        "由观测峰强估计 Wyckoff y 与标度因子 S。"
        "不是 Rietveld / 不是全谱剖面精修。"
    ),
    "fit.empty": (
        "加载或编辑观测表，设置拟合选项，然后点击「运行拟合」。"
        "反向计算不会自动开始。"
    ),
    "fit.stale": (
        '<div class="xrd-note xrd-note-warn">拟合结果已相对当前配置或观测表过期。'
        "请在应用 y* 或导出前重新运行拟合。</div>"
    ),
    "fit.valid": (
        '<div class="xrd-note">拟合结果与当前配置及观测表一致。</div>'
    ),
    "fit.context.header": "##### 拟合固定上下文（请先核对）",
    "fit.context.details": (
        "拟合不会优化这些量：a={a:.6g} Å，b={b:.6g} Å，c={c:.6g} Å；"
        "辐射={radiation}；散射={scattering}（{composition}）；"
        "2θ={tth_min:.6g}–{tth_max:.6g}°，HKL 上限={hkl_max}；"
        "LP={lp}，多重度={multiplicity}，1/V={volume}。"
    ),
    "fit.context.profile_excluded": (
        "这是离散峰强拟合：峰形、FWHM、背景和峰位偏移不参与优化。"
        "峰高模式仅使用等宽近似；有积分强度时应选峰面积。"
    ),
    "fit.observable.header": "##### 1. 先选择实验观测量",
    "fit.obs.header": "##### 2. 输入至少两个真实观测峰",
    "fit.obs.upload": "观测 CSV",
    "fit.obs.editor": "观测表（CSV 文本）",
    "fit.obs.template": "下载观测表模板 CSV",
    "fit.obs.caption": (
        "必填列：h, k, l, I_obs。可选：line / line_id, weight, sigma, notes。"
        "Miller 指数采用非负粉末约定。"
        "上传上限约 2 MiB / {max_rows} 行；同一 (HKL, 辐射线) 仅允许一行。"
    ),
    "fit.obs.multiline_warning": (
        "当前入射源为多辐射线（{lines}）。"
        "每行必须填写 line 或 line_id（如 line_00），否则匹配将因多线歧义失败。"
    ),
    "fit.obs.invalid": "当前观测表无法运行：{error}",
    "fit.obs.need_two": "当前识别 {count} 条有效观测；至少需要 2 条真实峰数据才能运行。",
    "fit.options.header": "##### 3. 设置权重与 y 扫描",
    "fit.options.scan_note": (
        "完整 y 网格用于暴露多个局部极小；局部细化只在网格最优附近提高精度。"
    ),
    "fit.observable_mode": "观测量模式",
    "fit.mode.peak_area": "峰面积（推荐）",
    "fit.mode.peak_height": "峰高（等宽近似）",
    "fit.weight_mode": "权重模式",
    "fit.weight.poisson": "类 Poisson（1 / max(I_obs, ε)）",
    "fit.weight.equal": "等权",
    "fit.y_start": "y 网格起点",
    "fit.y_stop": "y 网格终点",
    "fit.grid_points": "网格点数",
    "fit.peak_height_note": (
        "峰高模式假定峰宽相等，因而峰高 ∝ 面积。v1 中数值目标与峰面积模式相同，"
        "公共常数由 S 吸收。若有积分强度，请优先使用峰面积模式。"
    ),
    "fit.run": "4. 运行拟合",
    "fit.err.y_range": "y 网格终点必须大于或等于起点。",
    "fit.err.obs_encoding": (
        "观测文件不是有效的 UTF-8 文本。请另存为 UTF-8 编码的 CSV/TXT 后重新上传。"
    ),
    "fit.err.obs_too_large": (
        "观测文件过大（{size_kib:.1f} KiB）。请压缩到不超过 {max_mib:.0f} MiB。"
    ),
    "fit.err.obs_too_many_rows": (
        "观测表数据行过多（{rows} 行）。请控制在 {max_rows} 行以内（不含表头）。"
    ),
    "fit.calc_spinner": "正在运行离散峰强拟合…",
    "fit.kpi.y_star": "y*",
    "fit.kpi.s_star": "S*",
    "fit.kpi.chi2_star": "χ²*",
    "fit.kpi.shuffle_signed": "有符号 shuffle",
    "fit.kpi.shuffle_mag": "shuffle |s|",
    "fit.kpi.source": "来源",
    "fit.kpi.peaks": "使用峰数",
    "fit.kpi.mode": "观测量",
    "fit.plot.chi2": "χ²(y)",
    "fit.plot.scale": "最优标度因子 S(y)",
    "fit.plot.refine_trace": "局部细化轨迹",
    "fit.plot.best": "最优点",
    "fit.plot.local_minima": "局部极小",
    "fit.plot.x_y": "Wyckoff y",
    "fit.plot.y_chi2": "χ²(y)",
    "fit.plot.y_scale": "最优标度因子 S(y)",
    "fit.plot.parity_line": "理想一致线",
    "fit.plot.observations": "观测峰与拟合峰",
    "fit.plot.x_observed": "观测峰强 I_obs",
    "fit.plot.y_fitted": "拟合峰强 S* · I_model",
    "fit.plot.chi2_contribution": "逐峰 χ² 贡献",
    "fit.plot.x_hkl": "HKL",
    "fit.plot.y_chi2_contribution": "w · residual²",
    "fit.diagnostics.header": "##### 拟合过程与一致性诊断",
    "fit.display_coordinate": "结构显示坐标",
    "fit.display_coordinate_magnitude_note": (
        "shuffle 幅度在 y=0.25 两侧是二对一映射；图中上下分支分开绘制，"
        "不会跨零-shuffle 点错误连线。"
    ),
    "fit.diagnostics.chi2": "χ² 网格、局部细化轨迹、局部极小与最终最优点。",
    "fit.diagnostics.scale": "每个结构坐标处闭式求得的最优标度因子 S(y)。",
    "fit.diagnostics.parity": "观测峰强与最优拟合峰强；越接近对角线，一致性越好。",
    "fit.diagnostics.contributions": "每个 HKL 的 w·residual²；柱高之和等于最优 χ²。",
    "fit.local_minima.header": "##### 局部极小候选",
    "fit.local_minima.empty": "网格 χ² 曲线上未找到邻域极小。",
    "fit.residuals.header": "##### 最优点残差",
    "fit.apply": "将 y* 应用到结构",
    "fit.apply_caption": (
        "应用仅为手动操作：运行拟合不会改写结构面板。"
        "应用 y* 会更新 Wyckoff y 与 shuffle 幅度。"
    ),
    "fit.apply_success": "已将 y* = {y:.6f} 写入结构参数。",
    "fit.prepare": "准备拟合 ZIP",
    "fit.spinner": "正在将拟合过程表写入 ZIP…",
    "fit.prepare_caption": "先用当前配置运行拟合，再准备过程表 ZIP。",
    "fit.download": "下载拟合 ZIP",
    "fit.export_size": "{kib:.1f} KiB | SHA-256 {sha}…",
    # Method
    "method.title": "方法与解读",
    "method.workflow": """
#### 首次使用顺序

1. **核对输入**：分析或导出前先核对入射辐射、晶格、Wyckoff y、有符号 shuffle、shuffle 幅度，以及材料与计算设置。
2. **选择问题**：峰位看晶格与辐射，峰强看 Wyckoff y、有符号/幅度 shuffle、散射模型与修正，连续演化使用实时或扫描。
3. **先图后表**：先确认趋势与异常，再到峰表或数据预览核对具体 HKL 和数值。
4. **复核后导出**：确认活动模型摘要、归一化方式与结果有效状态，再准备导出包。
""",
    "method.view_guide": """
#### 各分区用途

- **衍射谱**：查看当前模型的峰位、峰形、棒图，以及单参数实时演化。
- **布拉格峰**：筛选具体辐射线与 HKL，核对 F²、峰位和各强度因子。
- **F² 演化**：隔离单位散射体结构因子，并用真实 Cmcm 4c 晶胞示意对照 Wyckoff y 与有符号/幅度 shuffle 的原子移动。
- **参数扫描**：计算范围扫描或逐行 CSV 轨迹；热图、瀑布图和峰演化可切换 y / 有符号 shuffle / 安全的幅度显示。
- **峰强拟合**：由实验峰面积或等宽近似峰高估计 y 与标度 S，并检查 χ²、S、观测-拟合一致性及逐峰残差；不是全谱精修。
- **方法与解读**：查公式、归一化定义、拟合假设与模型边界。
""",
    "method.left": """
#### Cmcm 4c 模型

正交相 Cmcm 4c 位点的分数坐标由 Wyckoff 参数生成。该参数控制基面 shuffle：

**shuffle_signed = 2(y − 0.25)**

**shuffle_magnitude = abs(shuffle_signed)**

改变 y 会改变结构因子，但不改变 d 间距。
改变 a、b 或 c 会改变 d 间距与布拉格位置。

结构示意中的 **y=0.25** 是同一 Cmcm 晶胞内的零-shuffle 特殊位置参考，
不代表在没有额外证据时把它指定为另一母相。每个 4c 位点相对参考的单原子位移为
**±b(y−0.25) = ±b·shuffle_signed/2**，严格沿 b 轴。

#### 峰强度

**I_model_peak = F² × 多重度 × LP × 体积因子 × 辐射线权重**

各 applied 因子在导出中单独给出。applied_volume 为 1/V 或 1，以保持所选模型约定。

另提供不受修正开关和辐射线权重影响的理论参考因子：

**R_hkl（含 LP）= N × F² × LP / V²**

**R_hkl_no_LP = N × F² / V²**

若实验积分已完成 LP、偏振或相应几何校正，才使用 no-LP 口径。两者都不是仪器绝对标定强度。

#### 离散峰强拟合（非 Rietveld）

在固定 a、b、c、辐射与修正开关的前提下，由 HKL 匹配的观测峰强估计 **y** 与单一标度 **S ≥ 0**：

**χ²(y, S) = Σ_i w_i (I_obs,i − S · I_model,i(y))²**

**S(y) = Σ w I_obs I_model / Σ w I_model²**（闭式解；S 截断为 ≥ 0）

默认 **类 Poisson** 权重：`w = 1 / max(I_obs, ε)`。可选等权；单峰 `weight` 或 `sigma` 覆盖全局模式。搜索为均匀 **y 网格**（默认完整 [0, 0.5]）加局部细化。网格上的局部极小仅为候选，不会自动当作物理解。
""",
    "method.right": """
#### 峰形与归一化

**I_profile_model** 为未归一化的峰形剖面叠加。

**I_rel_local** 对每个谱图或扫描步使用各自最大值。适合形状比较，不适合跨步振幅比较。

**I_rel_global** 对整次扫描使用同一最大值。适合观察强度随步演化。

#### 观测量模式与注意点

**峰面积模式** 是与 `I_model_peak` 对齐的积分强度路径（推荐）。**峰高模式** 为等宽近似（v1 中峰高 ∝ 面积）；不要把它当成自由峰形精修。该拟合是离散峰表反演，不是全谱剖面拟合，也不含背景、零点、微应变、织构、吸收或绝对标定。

#### 模型边界

输出为理论模型强度，不是测量原始强度、绝对标定强度、相分数或 Rietveld 拟合结果。
模型不含织构、吸收、异常散射、择优取向、微应变、晶粒尺寸宽化、零点漂移或背景。将 y* 写入结构面板始终是显式操作。
""",
    "method.info": (
        "若需论文式正交相 F²(y) 趋势，请使用「单位散射体 F²」。"
        "若需考虑成分的 X 射线谱，请使用「成分散射因子」。"
        "若需由测量峰强反演 y，请使用「峰强拟合」（非 Rietveld）。"
    ),
}

ZH_HELP: dict[str, str] = {
    "lang.label": _h(
        "切换界面显示语言（中文 / English）。",
        "便于中英文写作、汇报与对照说明书。",
        "默认中文；需要英文截图时切到 English。",
        "切换语言不会重置 a/b/c/y 等科学参数。",
    ),
    "nav.label": _h(
        "在衍射谱、峰表、F² 演化、参数扫描、峰强拟合与方法说明之间切换。",
        "仅当前视图会触发对应计算路径，避免无关重算。",
        "新手通常从「衍射谱」开始，再看「布拉格峰」。",
        "「参数扫描」与「峰强拟合」都不会自动运行，需显式点击运行。",
    ),
    "radiation.source": _h(
        "选择实验室靶材双线、同步辐射或自定义能量/波长。",
        "入射波长决定布拉格 2θ 位置与可用反射范围。",
        "同步辐射研究可选「30 keV 同步辐射」；实验室 Cu 靶选 Cu K-α。",
        "自定义能量与波长通过 E·λ = hc 相互换算。",
    ),
    "radiation.energy": _h(
        "以 keV 设定入射光子能量，并换算主波长。",
        "能量改变会移动峰位（2θ）并改变可观测 HKL 集合。",
        "硬 X 射线常用 20–40 keV；示例默认 30 keV。",
        "合法范围 1–200 keV；多线源相对权重在缩放时保持。",
    ),
    "radiation.wavelength": _h(
        "以 Å 直接设定主波长。",
        "与能量互为倒数关系，决定峰位与 Ewald 几何。",
        "Cu K-α1 ≈ 1.5406 Å；高能同步辐射可到 0.4 Å 量级。",
        "合法范围 0.05–5 Å。",
    ),
    "radiation.include_k_alpha2": _h(
        "在 K-α 双线预设中是否叠加 K-α2 分量。",
        "关闭后仅保留 K-α1，便于与单色谱比较。",
        "高分辨实验室数据通常保留双线；理论讨论可只留主线。",
        "权重比遵循预设（常见约 2:1）。",
    ),
    "structure.preset": _h(
        "载入文献或示例晶格常数与初始 y。",
        "快速对齐论文表格中的结构，减少手工录入错误。",
        "可从「S08 Table 5.5」开始，再微调 a/b/c。",
        "切换预设会覆盖当前 a/b/c/y/shuffle 输入。",
    ),
    "structure.a": _h(
        "正交晶胞 a 轴长度（Å）。",
        "改变 a 会改变含 h 指数反射的 d 间距与 2θ。",
        "Ti-Nb α'' 相常见 a ≈ 3.2 Å。",
        "合法范围 1–20 Å。",
    ),
    "structure.b": _h(
        "正交晶胞 b 轴长度（Å）。",
        "b 方向与 Wyckoff y 的基面位移相关，同时影响 d 间距。",
        "示例预设中 b 多在 4.7–4.8 Å。",
        "合法范围 1–20 Å。",
    ),
    "structure.c": _h(
        "正交晶胞 c 轴长度（Å）。",
        "改变 c 影响含 l 指数反射的峰位。",
        "示例预设中 c 多在 4.66–4.75 Å。",
        "合法范围 1–20 Å。",
    ),
    "structure.y": _h(
        "Cmcm 4c 位点的 Wyckoff y 分数坐标。",
        "主要调制结构因子 F² 与相对峰强，不改变 d 间距。",
        "Ti-Nb 下分支常见 y = 0.167…0.250。",
        "与 shuffle 联动：signed = 2(y−0.25)。",
    ),
    "structure.shuffle": _h(
        "基面原子位移幅度 |2(y−0.25)|。",
        "物理上对应 shuffle 大小；与 y 一一对应（选定分支后）。",
        "从 0（y=0.25）扫到 0.166 可复现常见下分支路径。",
        "幅度不区分上下分支符号，符号由 y 相对 0.25 决定。",
    ),
    "structure.branch": _h(
        "指定非负 shuffle 幅度映射到哪个 y 分支。",
        "在 y=0.25 时仅凭幅度无法判断分支，因此该选择始终可见。",
        "下分支 y=0.25-s/2；上分支 y=0.25+s/2。",
        "编辑 y 会同步分支；回到零-shuffle 参考点时保留最近一次有效分支。",
    ),
    "advanced.scattering": _h(
        "选择单位散射体或按成分加权的原子散射因子。",
        "单位散射体用于解析 F² 趋势；成分模式更接近真实 X 射线权重。",
        "写 F²(y) 曲线用「单位散射体 F²」；模拟合金谱用「成分散射因子」。",
        "成分模式依赖 s=1/(2d) 的有效散射因子。",
    ),
    "advanced.composition": _h(
        "以「元素=分数」列表给出化学计量权重。",
        "决定成分模式下各原子对散射振幅的贡献。",
        "示例：Ti=64, Nb=24, Zr=4, Sn=8（可按摩尔或质量比例约定使用）。",
        "分数须为正；用逗号分隔。",
    ),
    "advanced.tth_min": _h(
        "模拟与导出使用的 2θ 窗口下限。",
        "低于该角的反射不参与计算。",
        "低角讨论可设 1–5°。",
        "必须小于 2θ 上限；影响峰表与谱图长度。",
    ),
    "advanced.tth_max": _h(
        "模拟与导出使用的 2θ 窗口上限。",
        "决定最高可观测角与 HKL 覆盖。",
        "同步辐射短波长可用较小最大角覆盖高 q。",
        "必须大于下限。",
    ),
    "advanced.hkl_max": _h(
        "枚举反射时 |h|,|k|,|l| 的上限。",
        "限制计算成本与峰表规模。",
        "常规粉末谱 4–6 足够；高角需要可调高。",
        "过大将显著增加反射数与导出体积。",
    ),
    "advanced.points": _h(
        "连续谱在 2θ 轴上的采样点数。",
        "影响剖面光滑度与导出矩阵大小。",
        "屏幕查看 2000–4000；批量扫描可降到 800 以控内存。",
        "范围 200–10000。",
    ),
    "advanced.cutoff": _h(
        "峰表显示/过滤的相对强度下限（%）。",
        "抑制极弱峰，便于阅读。",
        "默认 0.1% 可滤掉数值噪声级弱峰。",
        "设为 0 保留全部计算峰。",
    ),
    "advanced.profile": _h(
        "用于叠加连续谱的峰形函数类型。",
        "决定峰宽形态：高斯、洛伦兹或 Pseudo-Voigt。",
        "实验峰常接近 Pseudo-Voigt；教学演示可用高斯。",
        "η 仅在 Pseudo-Voigt 时生效。",
    ),
    "advanced.fwhm": _h(
        "峰形半高全宽（° 2θ）。",
        "控制理论峰的宽度，非仪器完整展宽模型。",
        "高分辨数据可试 0.05–0.1°。",
        "本模型不含晶粒尺寸/微应变各向异性宽化。",
    ),
    "advanced.eta": _h(
        "Pseudo-Voigt 中洛伦兹成分权重 η。",
        "η=0 近高斯，η=1 近洛伦兹。",
        "常见起点 η=0.5。",
        "非 Pseudo-Voigt 峰形时控件禁用。",
    ),
    "advanced.lp": _h(
        "是否乘以 Lorentz–偏振几何因子。",
        "影响高/低角相对强度。",
        "常规粉末 XRD 建议开启。",
        "关闭后强度更接近纯 |F|² 权重（仍可含其它因子）。",
    ),
    "advanced.multiplicity": _h(
        "是否乘以正交晶系粉末多重度。",
        "等价取向反射合并时的统计权重。",
        "粉末谱必须考虑多重度；单晶讨论可关闭。",
        "与空间群系统消光相互独立处理。",
    ),
    "advanced.volume": _h(
        "是否按 1/V 对强度缩放。",
        "反映单胞体积对运动学强度的贡献。",
        "比较不同晶格体积时建议开启。",
        "导出中会写明 applied_volume 实际取值。",
    ),
    "pattern.mode": _h(
        "静态单谱与单参数实时演化之间切换。",
        "实时模式用于直观观察某一物理量连续变化的影响。",
        "先看静态谱确认峰位，再开实时演化拖动 y 或能量。",
        "实时帧在后端精确预计算，浏览器只做切帧显示。",
    ),
    "pattern.axis": _h(
        "选择 2θ、q 或 d 作为横轴。",
        "不同坐标便于与文献/实验习惯对照。",
        "实验室谱多用 2θ；PDF/高能数据常用 q。",
        "q、d 由主波长换算；能量扫描时每帧波长可不同。",
    ),
    "pattern.intensity": _h(
        "在相对强度（本地归一）与未归一模型强度间切换。",
        "相对强度便于看峰形；模型强度保留绝对理论幅度尺度。",
        "写论文对比形状用相对；检查计算幅度用模型。",
        "二者皆为理论值，非实验标定强度。",
    ),
    "pattern.display": _h(
        "连续剖面、棒图或二者叠加。",
        "棒图突出离散反射，剖面模拟观测谱。",
        "汇报可先棒图再叠加剖面。",
        "棒高对应所选强度标度。",
    ),
    "pattern.hkl_labels": _h(
        "在强峰附近显示 HKL 标注。",
        "帮助识别主要反射指数。",
        "教学演示建议开启。",
        "峰过密时标注可能重叠，可关闭。",
    ),
    "pattern.download_spectrum": _h(
        "导出当前理论谱图 CSV。",
        "便于 Origin/Python 后处理。",
        "文件名 spectrum.csv，列名保持 schema 英文。",
        "列语义见 Method 与导出 manifest。",
    ),
    "pattern.download_peaks": _h(
        "导出当前布拉格峰表 CSV。",
        "含 HKL、2θ、F²、强度分量等。",
        "用于制表或挑选跟踪峰。",
        "字段名为英文 schema，勿与界面语言混淆。",
    ),
    "plot.display_range": _h(
        "仅裁剪图上显示的 X/Y 范围。",
        "不改变模拟窗口、峰表与导出矩阵。",
        "放大某一 2θ 区间时调节 X 上下限。",
        "重置可回到当前谱的默认全范围。",
    ),
    "plot.x_min": _h("显示横轴下限。", "与上限共同决定视窗。", "例如只看 5–15°。", "须小于 X 上限。"),
    "plot.x_max": _h("显示横轴上限。", "与下限共同决定视窗。", "例如扩展到 40°。", "须大于 X 下限。"),
    "plot.y_auto": _h("按数据自动设定纵轴。", "快速浏览时避免裁切峰值。", "默认开启。", "关闭后可手动设 Y 范围。"),
    "plot.y_min": _h("手动纵轴下限。", "用于放大弱信号区。", "相对强度常从 0 起。", "须小于 Y 上限。"),
    "plot.y_max": _h("手动纵轴上限。", "防止强峰占满导致弱峰不可见时可略抬高。", "相对强度常用 105%。", "须大于 Y 下限。"),
    "plot.reset": _h("恢复默认显示范围。", "撤销临时缩放。", "切换轴类型后也可重置。", "不影响科学输入参数。"),
    "peaks.hkl_filter": _h(
        "按 HKL 字符串子串过滤峰表。",
        "快速定位特定反射族。",
        "输入 110 或 02 过滤相关峰。",
        "区分大小写不敏感于数字串匹配。",
    ),
    "peaks.line_filter": _h(
        "按辐射线标签筛选（如 K-α1/K-α2）。",
        "双线源时便于分开检查。",
        "只勾选 K-α1 可隐藏次线峰。",
        "默认全选全部辐射线。",
    ),
    "peaks.min_irel": _h(
        "相对强度下限过滤。",
        "隐藏过弱峰以聚焦主峰。",
        "设 1 表示只看 ≥1% 的峰。",
        "与高级设置中的表截断相互独立（此处为交互过滤）。",
    ),
    "peaks.angle_filter": _h(
        "按 2θ 区间过滤峰表。",
        "聚焦某一角区的反射。",
        "拖到 8–18° 查看中角区。",
        "范围受当前模拟窗口限制。",
    ),
    "peaks.download_all": _h("下载未过滤完整峰表。", "存档与复核。", "peaks_all.csv。", "schema 英文字段。"),
    "peaks.download_filtered": _h("下载当前筛选结果。", "只保留关心的峰。", "peaks_filtered.csv。", "筛选条件不写入文件名。"),
    "f2.hkls": _h(
        "选择最多 12 条 HKL 绘制 F² 随坐标演化。",
        "用于观察结构因子随 y/shuffle 的消光与增强。",
        "默认 110/020/021/131 适合教学。",
        "此视图使用单位散射体解析 F²，不含峰形。",
    ),
    "f2.axis": _h(
        "选择 F² 曲线的自变量。",
        "y 与 shuffle 通过解析关系互相对应。",
        "论文常见横轴为 shuffle 幅度。",
        "幅度轴需指定上下分支。",
    ),
    "f2.branch": _h(
        "shuffle 幅度到 y 的映射分支。",
        "同一幅度对应 y=0.25±s/2 两个可能。",
        "Ti-Nb 默认研究下分支。",
        "切换分支会改变 y 路径。",
    ),
    "f2.start": _h("演化横轴起点。", "定义曲线采样区间。", "下分支 shuffle 0→0.166。", "须小于终点。"),
    "f2.stop": _h("演化横轴终点。", "与起点组成闭区间采样。", "y 可取 0.25。", "须大于起点。"),
    "f2.points": _h("曲线采样点数。", "影响平滑度。", "301 点通常足够。", "范围 10–2000。"),
    "f2.download": _h(
        "导出 F² 演化长表。",
        "同时保留所选显示轴与 canonical y，便于后处理作图。",
        "f2_evolution.csv。",
        "列含 axis_value、hkl、F2、axis_code、y、有符号/幅度 shuffle 与 branch。",
    ),
    "f2.download_excel": _h(
        "把同一份 F² 演化长表导出为原生 Excel 工作簿。",
        "021 等 HKL 以文本保存，不丢失前导零。",
        "README、Parameters 与 Columns 分页解释模型、路径和全部字段。",
        "Origin/Python 自动处理仍建议使用 CSV。",
    ),
    "f2.structure_preview.slider": _h(
        "选择结构示意中显示的 Wyckoff y、有符号 shuffle 或 shuffle 幅度坐标。",
        "把抽象演化坐标映射为真实 Cmcm 4c 位点沿 b 轴的移动。",
        "可对照 F² 曲线上的某个坐标观察原子位置。",
        "仅预览，不写回顶部主结构参数，也不触发模拟或导出变化。",
    ),
    "live.parameter": _h(
        "选择实时演化的单一活动参数。",
        "一次只扫一个轴，保证帧语义清晰。",
        "研究 shuffle 对峰强影响时选 shuffle 幅度。",
        "其它物理量在扫描期间保持为当前配置。",
    ),
    "live.branch": _h("幅度轴对应的 y 分支。", "决定 y 映射方向。", "默认下分支。", "与结构面板 y 一致。"),
    "live.start": _h("实时扫描起点。", "预计算帧范围下界。", "应覆盖当前参数值。", "与终点、步长共同决定帧数。"),
    "live.stop": _h("实时扫描终点。", "预计算帧范围上界。", "略大于当前值以便拖动。", "帧数受 401 上限约束。"),
    "live.step": _h("相邻帧参数步长。", "步长越小帧越密、计算越重。", "y 常用 0.001。", "须为正。"),
    "live.points": _h("每帧谱图点数（预览）。", "浏览器载荷与平滑度权衡。", "1600 为常用上限附近。", "导出使用全精度 float64。"),
    "live.rebuild": _h("按当前非活动配置重建全部帧。", "配置过期后必须重建才能交互。", "改了 FWHM 后点击重建。", "活动轴本身变化由帧覆盖，不必因此重建。"),
    "live.set_baseline": _h("把当前帧固定为灰色基线。", "便于与之后拖动结果对比。", "先拖到参考态再设基线。", "差值迹线相对该基线。"),
    "live.export.prepare": _h(
        "打包 float64 扫描表与基线/当前对比。",
        "用于论文附图与可重复分析。",
        "确认基线与当前帧后准备 ZIP。",
        "选择变更后需重新准备。",
    ),
    "live.export.download": _h("下载已准备的 live_evolution.zip。", "离线分析。", "含 live_state.json 等。", "schema 2.2。"),
    "sweep.spectrum_points": _h(
        "扫描中每一步谱图采样点数。",
        "控制内存与 ZIP 体积。",
        "大批量用 800；精细剖面可提高。",
        "受总单元数限额约束。",
    ),
    "sweep.input_mode": _h(
        "一维等步扫描或按行 CSV 轨迹。",
        "轨迹可表达任意路径，不做笛卡尔积。",
        "单参数灵敏度用范围扫描；多参数路径用 CSV。",
        "空单元格继承当前 base 配置。",
    ),
    "sweep.normalization": _h(
        "热图/瀑布图强度归一化方式。",
        "全局归一化保留步间振幅演化；局部则逐步重标定。",
        "比较演化务必选全局或模型强度。",
        "局部模式会显示不可跨步比较的警告。",
    ),
    "sweep.axis": _h(
        "范围扫描的自变量。",
        "决定每一步改写的物理量。",
        "研究 y 路径选 Wyckoff y。",
        "能量/波长扫描会改变峰位。",
    ),
    "sweep.branch": _h("shuffle 幅度扫描的分支。", "映射到 y 的公式不同。", "默认下分支。", "与 Method 中公式一致。"),
    "sweep.start": _h("扫描起点。", "含端点的等步网格起点。", "Ti-Nb y 从 0.167。", "须 ≤ 终点。"),
    "sweep.stop": _h("扫描终点。", "含端点。", "y 到 0.250。", "须 ≥ 起点。"),
    "sweep.step": _h("扫描步长。", "步数 ≈ floor((stop−start)/step)+1。", "0.001 得到细网格。", "须为正；注意步数上限。"),
    "sweep.run": _h("显式启动批量计算。", "避免误触重算。", "改完轴与范围后点击。", "配置变更会使旧结果过期。"),
    "sweep.trajectory_file": _h(
        "上传逐步覆盖参数的 CSV。",
        "按行顺序执行，不扩展为网格。",
        "先下载模板再填 step_label 与参数。",
        "step_label 必须唯一；y 与 shuffle 若同时给出须一致。",
    ),
    "sweep.trajectory_template": _h("下载合法列头的示例轨迹。", "减少格式错误。", "trajectory_template.csv。", "列名保持英文。"),
    "sweep.result_view": _h("在热图、瀑布图、峰演化与数据预览间切换。", "同一结果多视角解读。", "先热图总览再峰演化。", "显示范围裁剪不影响导出全量。"),
    "sweep.peak_metric": _h("峰演化曲线的纵轴度量。", "F²、N·F²、R 与模型强度口径不同。", "实验峰面积后处理可按是否已校正 LP 选择两种 R。", "R 是未归一化理论参考因子，不是仪器绝对标定强度。"),
    "sweep.peak_series": _h("最多选择 12 条峰系列绘制演化。", "跟踪关键 HKL。", "勾选 110/020 等。", "消光峰以 0 保留以不断线。"),
    "sweep.prepare": _h("生成 schema 2.2 扫描 ZIP。", "完整可复现数据包。", "结果有效且未过期时准备。", "过期结果按钮禁用。"),
    "sweep.download": _h("下载已准备的扫描 ZIP。", "Origin/Python 后处理。", "含矩阵与 checksum。", "文件名保持英文。"),
    "sweep.display_range": _h("仅裁剪热图/瀑布图显示窗。", "导出仍为全模拟窗口。", "放大局部 2θ。", "上下限须有序。"),
    "sweep.display_coordinate": _h(
        "只改变扫描结果图的结构横轴/纵轴显示坐标。",
        "同一组 canonical y 结果可显示为 y、有符号 shuffle 或安全的 shuffle 幅度。",
        "需要区分 y=0.25 两侧时使用有符号 shuffle。",
        "不会重算、修改扫描结果或改变导出的 axis_value。",
    ),
    "sweep.display_tth_min": _h("显示用 2θ 下限。", "视窗控制。", "例如 5°。", "须小于上限。"),
    "sweep.display_tth_max": _h("显示用 2θ 上限。", "视窗控制。", "例如 20°。", "须大于下限。"),
    "sweep.display_axis_min": _h("扫描轴显示下限。", "裁剪纵轴/扫描轴。", "对准关心区间。", "须小于上限。"),
    "sweep.display_axis_max": _h("扫描轴显示上限。", "裁剪纵轴/扫描轴。", "对准关心区间。", "须大于下限。"),
    "sweep.display_reset": _h("恢复扫描显示默认范围。", "撤销缩放。", "一键复位。", "不改计算结果。"),
    "export.prepare": _h(
        "按需打包当前谱图、峰表、config 与 manifest。",
        "保证导出与当前配置哈希一致。",
        "调参满意后点击准备。",
        "配置变更会使旧包失效。",
    ),
    "export.download": _h("下载 current_simulation.zip。", "存档与制图。", "含 Origin 辅助文件。", "schema 2.2。"),
    "fit.obs.upload": _h(
        "上传离散峰观测 CSV。",
        "把实验峰强导入反演拟合。",
        "先下模板，填入若干 HKL 的 I_obs。",
        "上限约 2 MiB / 500 行；多线源须填 line/line_id；未匹配 HKL 按行号硬失败。",
    ),
    "fit.obs.editor": _h(
        "在页面中直接编辑观测 CSV 文本。",
        "改错不必重新上传。",
        "必填 h,k,l,I_obs。",
        "可选 line/line_id、weight、sigma、notes。",
    ),
    "fit.obs.template": _h(
        "下载稳定的观测 CSV 模板。",
        "明确必填列。",
        "observation_template.csv。",
        "列名保持英文。",
    ),
    "fit.observable_mode": _h(
        "选择峰面积或峰高观测量。",
        "决定 I_obs 的科学含义。",
        "有积分强度时优先峰面积。",
        "v1 峰高仅为等宽近似。",
    ),
    "fit.display_coordinate": _h(
        "只改变 χ² 与 S 曲线的结构坐标显示方式。",
        "拟合始终以 canonical Wyckoff y 计算；显示可切换为 y、有符号 shuffle 或幅度。",
        "比较 y=0.25 两侧候选极小值时优先使用有符号 shuffle。",
        "不会重算拟合或修改 y*；幅度模式会把上下分支拆开。",
    ),
    "fit.weight_mode": _h(
        "在行未给出 weight/sigma 时的全局权重方案。",
        "类 Poisson 会削弱极强峰的主导。",
        "等权便于对照教材。",
        "单峰 weight 或 sigma 覆盖全局模式。",
    ),
    "fit.y_start": _h(
        "y 网格扫描下界。",
        "默认 0 覆盖两个 shuffle 分支。",
        "除非有意裁剪，否则保持 0.0。",
        "须 ≤ 终点，且在 [0, 0.5]。",
    ),
    "fit.y_stop": _h(
        "y 网格扫描上界。",
        "默认 0.5 为完整 Wyckoff 定义域。",
        "保持 0.5 以便观察多峰性。",
        "须 ≥ 起点，且在 [0, 0.5]。",
    ),
    "fit.grid_points": _h(
        "y 网格均匀采样点数。",
        "决定局部细化前的 χ²(y) 密度。",
        "201 为均衡默认。",
        "点数越大前向计算越多。",
    ),
    "fit.run": _h(
        "显式启动离散峰强拟合。",
        "避免误触发反向计算。",
        "检查观测与模式后再点。",
        "不会在运行时自动写入结构 y*。",
    ),
    "fit.apply": _h(
        "将最优 y* 与 |shuffle| 写入结构面板。",
        "仅在你确认后提交反演结果。",
        "先查看 χ²(y) 与残差再应用。",
        "结果过期时按钮禁用。",
    ),
    "fit.prepare": _h(
        "按需生成拟合过程表 ZIP。",
        "便于离线复现与制图。",
        "结果有效时再准备。",
        "默认不含每个网格 y 的完整残差长表。",
    ),
    "fit.download": _h(
        "下载 discrete_peak_fit.zip。",
        "论文式过程表打包。",
        "含 observations、grid_scan、残差、config、manifest。",
        "文件名为英文；schema 2.x 家族。",
    ),
}
