# 3-D OpenFOAM extension specification — not executed

The current repository does not ship an unverified OpenFOAM case disguised as a completed simulation. The Python pipeline is independently runnable. To replace the screening approximation with a design-grade study, the following is the proposed specification:

1. Select and pin a supported OpenCFD release and its `buoyantBoussinesqSimpleFoam` tutorial conventions. Do not mix Foundation/OpenCFD dictionaries.
2. Use the supplied 8×5×3 m OBJ shell as a geometry reference. Split supply and return boundary patches using the positions in methodology.md. Resolve finite-size diffusers rather than full-depth 2-D slots for realistic design.
3. Generate a hexahedral mesh with local refinement at diffuser exits, occupied heat sources and wall layers. Select wall treatment consistently with achieved y-plus.
4. Set supply volume flow 0.12 m³/s, supply temperature 292.15 K, outlet fixed reduced pressure with suitable backflow conditions; wall no-slip velocity. Match the scalar wall heat-transfer assumption or explicitly document a replacement.
5. Start with buoyant incompressible RANS, Boussinesq density and a documented turbulence closure. Specify inlet turbulence from diffuser characteristics, not arbitrary defaults. Model 600 W sensible load through resolved sources or verified source terms.
6. Add passive age transport with unit source and zero inlet age. Export cell centers, velocity, temperature and age to the same occupied-zone postprocessing definitions. Set mean radiant temperature from a radiation model or measurements rather than from air temperature.
7. Run at least three meshes and assess integral metrics and occupied profiles. Require stable monitors, small continuity/energy imbalance and solver residuals justified for the case; residual magnitude alone is insufficient.
8. Validate a ventilation benchmark and obtain diffuser/room measurements before applying real design recommendations. Use a transient solver if a steady solution is physically unstable.

Until those steps are actually run and verified, list this project as **Python finite-volume ventilation screening**, not OpenFOAM/Fluent expertise or a completed turbulent simulation.
