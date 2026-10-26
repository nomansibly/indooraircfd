# Transient heat transport and interactive dashboards

## Eight-hour Python model

Run `python -m iaq.transient` to generate actual temperature histories, mean local PMV/PPD, raw fields and a load trace for both layouts. The solver uses the same conservative advection/diffusion matrix as the baseline plus a backward-Euler cell heat-storage term, V/dt. Airflow stays fixed; changing temperature does not change velocity.

Default dt=120 s; initial air=22°C; equipment=150 W; sensible occupant gain=75 W/person. Stepwise occupant count at hours [0,.5,2,3,4,5,6.5,8] is [2,8,8,3,0,8,6,0]. Prescribed absorbed window gain is a 900 W Gaussian spike centered at hour4 with width0.6h, deposited uniformly in cells with x>.85L and .3H<z<.8H. This is a spatial heat-source approximation, not ray-traced solar radiation or a glazing model. Supply temperature is base + 1.5 sin(2pi*h/8) °C. Wall/MRT is fixed. No occupant latent gain, humidity transport, wall capacitance or buoyancy is modeled.

Schedules are evaluated at the backward-Euler step endpoint. Thus discontinuities are smeared over a timestep; decrease dt for temporal sensitivity. Output frames are nominally every600s. Conservation tests check storage + boundary transport = gains within numerical tolerance. A 120/60s timestep comparison and uniform-state preservation tests are included.

## Streamlit + Plotly app

```bash
pip install -r requirements-dashboard.txt
streamlit run streamlit_app.py
```

Controls recompute length, depth, height, ACH and supply/wall temperature, with return choice, steady/workday modes, solar amplitude and a time slider. ACH is converted to volume flow for the selected room. Contour plots show computed temperature, PMV, PPD and speed. CSV history and JSON configuration downloads are available. Tests use Streamlit AppTest to change supply temperature and enter workday mode.

For a self-hosted server: `docker build -t indoor-air-lab .` then `docker run -p 8501:8501 indoor-air-lab`. This repository contains the runnable Streamlit application; it is not currently deployed to Streamlit Community Cloud. Hosting a persistent Python server requires a compatible host; no cloud account or paid service has been provisioned.

## Public browser lab

The published Site uses `web/solver.mjs`, a JavaScript implementation of the same finite-volume operators with a Jacobi-preconditioned BiCGSTAB linear solver, on a 32×16 screening mesh. It runs in a Web Worker, recomputes in the visitor's browser, and needs no Python server. Contour maps are cell heatmaps with interpolated marching-squares isolines. The model is not a surrogate fitted to OpenFOAM and does not run RANS on slider changes.

Parity tests compare full steady temperature/age fields and the final 8 h temperature field with the Python solver at identical grid/settings. T tolerance=1e−5°C; age tolerance=1e−3s. The browser reports solver duration and maximum volume-flux imbalance and supports result JSON download. Typical timings observed here: .13s steady, ~3s workday; hardware affects these timings.

Build the public static assets from this repository using `python scripts/build_site.py --output site-dist` and serve that directory. The Sites host contains the same built assets.
