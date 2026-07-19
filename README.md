<p align="center">
  <img src="assets/readme/hero.svg" width="100%" alt="CrystalShift XRD: Cmcm 4c theoretical powder XRD workbench.">
</p>

# CrystalShift XRD

**How lattice, Wyckoff `y`, basal shuffle, and energy move powder peaks and F².**

Streamlit workbench for theoretical powder XRD of orthorhombic **`Cmcm 4c`**. Version `2.2.0` · export schema `2.2`.

> Theoretical model only — not Rietveld, not absolute intensity calibration.

<p align="center">
  <img src="assets/readme/section-01-model.svg" width="100%" alt="01 Model: Cmcm 4c structure contract.">
</p>

```text
(0, y, 1/4), (0, -y, 3/4),
(1/2, 1/2+y, 1/4), (1/2, 1/2-y, 3/4)

shuffle_signed = 2*(y-0.25)
wavelength_A   = 12.398419843320026 / energy_keV
I_model_peak   = F2 · mult · LP · V · line_weight
```

`R_hkl` with/without LP for experimental area post-processing (theoretical only).

### Quick start

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m streamlit run app.py --server.port 8508
```

Open http://localhost:8508/

<p align="center">
  <img src="assets/readme/section-02-explore.svg" width="100%" alt="02 Explore: live frames, sweeps, peak fit.">
</p>

- **Pattern** — static 2θ / q / d  
- **Live evolution** — exact precomputed frames; browser switches locally  
- **F² evolution** + structure preview along `b`  
- **Sweep / trajectory** CSV · **discrete-peak fit** diagnostics  
- Schema 2.2 ZIP + `analysis.xlsx` with hashes and checksums  

Does **not** implement Rietveld/Le Bail/Pawley, texture, absorption, size/strain, zero shift, background, phase fractions, or absolute calibration.

```bash
python -m pytest -q && python -m ruff check .
```

No open-source license selected yet — publication of source does not grant redistribution of modified versions until `LICENSE` is added. Cite the structure source and keep export manifests with figures.
