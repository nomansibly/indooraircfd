# Executed 3-D buoyant RANS with k–ω SST

Both supplied cases were executed using **OpenCFD OpenFOAM v1912 patch 200626**, Ubuntu package `1912.200626-2build3`. The successful runs use **buoyantBoussinesqPimpleFoam (URANS)** through 600 physical seconds. They are startup snapshots, not steady or statistically averaged predictions. A preliminary SIMPLE run did not converge; no converged steady result is claimed.

## Reproduce

On Ubuntu 24.04 with the v1912 package installed and executable paths available:

```bash
sudo apt-get update
sudo apt-get install openfoam ripgrep
pip install -r requirements-rans.txt
bash openfoam/Allrun openfoam/cases/cross_room
python openfoam/analyze.py openfoam/cases/cross_room --layout cross_room --log openfoam/cases/cross_room/log.solver
bash openfoam/Allrun openfoam/cases/short_circuit
python openfoam/analyze.py openfoam/cases/short_circuit --layout short_circuit --log openfoam/cases/short_circuit/log.solver
```

`Allrun` sets the packaged etc path if no OpenFOAM environment has been loaded. For another installation, load that installation first. Foundation releases are not interchangeable with this case. The included CI workflow pins Ubuntu 24.04 and checks `kOmegaSST` selection, completion and mesh validity.

## Physical/numerical setup

- Room: x=8 m, y=5 m, z=3 m; gravity −z. Structured 3-D mesh, 3,840 hexahedra, zero nonorthogonality.
- Finite supply patch: x=0, y=2–3 m, z=2.4–3 m. U=(0.2,0,0) m/s, T=292.15 K. Flow=0.12 m³/s.
- Cross-room return: x=8, y=2–3, z=0–0.6. Nearby return: x=0, y=2–3, z=1.6–2.2.
- No-slip walls, fixed wall temperature 299.15 K, return p_rgh=0 with pressure-driven velocity/backflow handling.
- Boussinesq beta=1/300 K⁻¹, reference 295.15 K; nu=1.5e−5 m²/s, Pr=.71, Prt=.85.
- k–ω SST with wall functions. Assumed inlet k=.00015 m²/s² and omega=.32 s⁻¹ correspond approximately to 5% turbulence intensity and 0.07 m length scale at 0.2 m/s. These are assumed diffuser characteristics.
- 600 W uniform sensible source. The temperature equation is per unit rho*cp: absolute integrated source = 600/(1.2*1005) K·m³/s.
- Backward Euler time integration; bounded first-order upwind convection. Adaptive timestep, maxCo=.5, maxDeltaT=.5 s; PIMPLE 2 outer × 2 pressure correctors. First-order choices prioritize robustness and add numerical diffusion.

The 2-D screening baseline uses full-depth slots and Robin wall heat exchange; these 3-D cases use finite patches and fixed wall temperatures. Their numbers are **not** a controlled comparison of solver fidelity alone.

## Evidence and limitations

`results/rans/` includes actual VTK fields, compressed complete solver logs, checkMesh logs, reports and section plots. Relative net boundary flux at final output is about 8.3e−9 for both cases. Small linear solver residuals and continuity error do not establish time convergence, resolved jets or physical validation.

The Ubuntu v1912 build fails in SHA1-stream processing when enabling runtime function objects. Runs use `-noFunctionObjects`; normal equation residuals and continuity still appear in solver logs, and `foamToVTK` works. The separate yPlus postprocessing attempt also failed. **No wall-y-plus qualification has been performed.** The mesh has only six supply faces and is too coarse for resolved wall-jet design claims. Use the supplied generator for refinement and verify near-wall treatment before interpreting wall behavior.

```bash
# Generate separate cases; never overwrite the supplied initial conditions.
python openfoam/generate_case.py --output /tmp/room-medium --scale 1 --transient --end 600
python openfoam/generate_case.py --output /tmp/room-fine --scale 2 --transient --end 600
# Steady SIMPLE is also supported for experimentation; convergence is not guaranteed.
python openfoam/generate_case.py --output /tmp/room-steady --scale 1 --end 2000
```

Extend duration to several room residence times (nominal V/Q=1,000 s), establish sampling/averaging independence, test three meshes and timesteps, qualify yPlus and compare measured diffuser/room profiles. 600 s is less than one nominal residence time. PMV assumes fixed MRT=26°C, RH50%, met1.2, clo0.5 and is also only a startup snapshot. Projected streamlines on the y=2.5 m slice are not 3-D particle paths.
