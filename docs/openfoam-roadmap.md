# OpenFOAM implementation status

The earlier extension specification has been implemented and executed. See [the case guide](../openfoam/README.md) for the exact release, inputs, reproduction commands and limitations. The successful runs use buoyantBoussinesqPimpleFoam (URANS), k–ω SST, 3,840 cells and 600 physical seconds for both layouts. Actual outputs and complete compressed logs are in `results/rans`.

Outstanding validation work is now longer transient sampling, wall-resolution qualification, mesh/timestep refinement and experimental comparison. The earlier steady SIMPLE attempt did not converge. No validated wall-jet result or steady-state comfort ranking is claimed.
