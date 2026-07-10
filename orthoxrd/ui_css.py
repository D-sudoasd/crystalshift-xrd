UI_CSS = r"""
<style>
:root {
  color-scheme: dark;
  --xrd-bg: #0b0f14;
  --xrd-surface: #121821;
  --xrd-control: #18202b;
  --xrd-border: #2a3441;
  --xrd-text: #f3f6fa;
  --xrd-muted: #aeb8c5;
  --xrd-accent: #22c7d6;
  --xrd-warning: #f2b84b;
  --xrd-error: #ff5a67;
  --xrd-valid: #48c78e;
}
html, body, [class*="css"] {
  font-variant-numeric: tabular-nums;
}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
  background: var(--xrd-bg);
  color: var(--xrd-text);
}
[data-testid="stHeader"] {
  border-bottom: 1px solid rgba(42,52,65,.45);
}
.block-container {
  width: min(100%, 1480px);
  max-width: 1480px;
  padding: .75rem 1.25rem 1.5rem;
}
h1, h2, h3, h4, h5, p, label {
  letter-spacing: 0;
}
h1 {
  margin: 0;
  font-size: clamp(1.35rem, 2.2vw, 2rem);
  line-height: 1.15;
}
h2 {
  font-size: 1.28rem;
}
h3, h4 {
  font-size: 1.02rem;
}
[data-testid="stVerticalBlockBorderWrapper"] {
  background: var(--xrd-surface);
  border-color: var(--xrd-border);
  border-radius: 8px;
}
[data-baseweb="popover"] {
  background: var(--xrd-surface);
  border: 1px solid var(--xrd-border);
  border-radius: 8px;
}
div[data-baseweb="select"] > div,
div[data-baseweb="input"] > div,
div[data-baseweb="textarea"] > div {
  min-height: 40px;
  background: var(--xrd-control);
  border-color: var(--xrd-border);
  border-radius: 6px;
  color: var(--xrd-text);
}
div[data-baseweb="select"] input,
div[data-baseweb="input"] input,
textarea {
  color: var(--xrd-text) !important;
  font-family: "Cascadia Mono", "Consolas", monospace;
}
button:focus-visible,
input:focus-visible,
textarea:focus-visible,
[role="button"]:focus-visible {
  outline: 2px solid var(--xrd-accent) !important;
  outline-offset: 2px;
}
.stButton > button,
.stDownloadButton > button,
[data-testid="stPopover"] > button {
  min-height: 40px;
  background: var(--xrd-control);
  color: var(--xrd-text);
  border: 1px solid var(--xrd-border);
  border-radius: 6px;
  font-weight: 600;
}
.stButton > button:hover,
.stDownloadButton > button:hover,
[data-testid="stPopover"] > button:hover {
  border-color: var(--xrd-accent);
  color: var(--xrd-text);
}
button:disabled,
.stButton > button:disabled,
.stDownloadButton > button:disabled {
  color: #7f8a98 !important;
  background: #10161e !important;
  border-color: #222b36 !important;
  opacity: 1 !important;
}
[data-testid="stDataFrame"] {
  overflow: hidden;
  border: 1px solid var(--xrd-border);
  border-radius: 6px;
}
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p {
  color: var(--xrd-muted);
}
[data-testid="stAlert"] {
  border-radius: 6px;
}
[data-testid="stFileUploaderDropzone"] {
  background: var(--xrd-control);
  border-color: var(--xrd-border);
  border-radius: 6px;
}
[data-testid="stForm"] {
  border-color: var(--xrd-border);
  border-radius: 8px;
  background: var(--xrd-surface);
}
.xrd-titlebar {
  display: flex;
  align-items: baseline;
  gap: 12px;
  min-width: 0;
}
.xrd-model-tag {
  color: var(--xrd-accent);
  font: 600 .76rem/1 "Cascadia Mono", "Consolas", monospace;
  white-space: nowrap;
}
.xrd-subtitle {
  margin-top: 4px;
  color: var(--xrd-muted);
  font-size: .86rem;
}
.xrd-summary-grid {
  display: grid;
  grid-template-columns: repeat(8, minmax(92px, 1fr));
  gap: 6px;
  margin: 8px 0 10px;
}
.xrd-summary-card {
  min-width: 0;
  background: var(--xrd-surface);
  border: 1px solid var(--xrd-border);
  border-radius: 6px;
  padding: 8px 10px;
}
.xrd-summary-label {
  color: var(--xrd-muted);
  font-size: .68rem;
  line-height: 1.15;
}
.xrd-summary-value {
  margin-top: 4px;
  overflow: hidden;
  color: var(--xrd-text);
  font: 600 .92rem/1.2 "Cascadia Mono", "Consolas", monospace;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.xrd-note, .xrd-readout-card, .xrd-state {
  border: 1px solid var(--xrd-border);
  border-radius: 6px;
  background: var(--xrd-control);
  padding: 8px 10px;
  color: var(--xrd-muted);
  font-size: .8rem;
  line-height: 1.45;
}
.xrd-readout-card {
  min-height: 72px;
}
.xrd-readout-label {
  color: var(--xrd-muted);
  font-size: .72rem;
}
.xrd-readout-value {
  margin-top: 5px;
  color: var(--xrd-text);
  font: 600 1rem/1.2 "Cascadia Mono", "Consolas", monospace;
}
.xrd-readout-meta {
  margin-top: 3px;
  color: var(--xrd-muted);
  font-size: .7rem;
}
.xrd-state--warning {
  border-color: rgba(242,184,75,.65);
  color: #f6d58f;
}
.xrd-state--valid {
  border-color: rgba(72,199,142,.58);
  color: #8be0b7;
}
.xrd-kpi-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(100px, 1fr));
  gap: 6px;
  margin: 8px 0;
}
.xrd-nav [data-testid="stButtonGroup"] {
  margin: 4px 0 8px;
}
code, pre {
  font-family: "Cascadia Mono", "Consolas", monospace;
}
@media (max-width: 900px) {
  .block-container { padding: .65rem .75rem 1.25rem; }
  .xrd-titlebar { flex-wrap: wrap; }
  .xrd-summary-grid { grid-template-columns: repeat(4, minmax(86px, 1fr)); }
  .xrd-kpi-row { grid-template-columns: repeat(2, minmax(100px, 1fr)); }
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
  [data-testid="stColumn"] {
    min-width: min(100%, 260px) !important;
    flex: 1 1 calc(50% - .5rem) !important;
  }
}
@media (max-width: 520px) {
  .block-container { padding: .5rem .55rem 1rem; }
  .xrd-titlebar { align-items: flex-start; flex-direction: column; gap: 4px; }
  .xrd-summary-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .xrd-kpi-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .xrd-summary-card { padding: 7px 8px; }
  [data-testid="stHorizontalBlock"] { flex-wrap: wrap; }
  [data-testid="stColumn"] { min-width: min(100%, 240px) !important; flex: 1 1 100% !important; }
}
</style>
"""
