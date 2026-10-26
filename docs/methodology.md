# Methodology and interpretation

## Scope
A reproducible numerical **screening study**, not a validated HVAC design. The solver computes a 2-D vertical section extruded to 5 m depth. Actual computed fields are included; no contours are hand drawn or generated from decorative analytic functions. The room has no furniture or resolved occupants.

## Governing equations
Potential flow: q = -A grad(phi), with div(q)=0 solved by a sparse finite-volume Laplacian and a single pressure-potential gauge. Wall normal flux is zero. Supply and return volume flow are prescribed equally. This is irrotational flow with slip walls: it does **not** solve the Navier–Stokes momentum equations, jet entrainment, turbulence, buoyancy or wall boundary layers.

Scalar transport: div(u s - D grad(s)) = source, discretized using conservative first-order upwind advection and centered diffusion. D=0.01 m²/s is an assumed effective mixing coefficient, not a calibrated turbulence model. Temperature source is 600 W / (rho cp V), rho=1.2 kg/m³ and cp=1005 J/(kg K). Supply temperature is 19°C. Solid walls exchange heat with a 26°C surface using h=1 W/(m² K); vents use inflow prescribed scalar and outflow advective flux, with zero diffusive vent flux.

Air age solves the same scalar equation with a unit time source and zero supply age. ACH=Q/V*3600. Occupied air change index = (V/Q)/mean occupied age. Whole-room air exchange efficiency = (V/Q)/(2 mean room age); these are distinct measures. No contaminant concentration or CO2 removal effectiveness is calculated.

## Geometry and comparison
Room 8×5×3 m, 120 m³. Total supply 0.12 m³/s (3.6 ACH). The left wall supply occupies z=2.4–3 m across the full depth. Cross-room return is on the right wall z=0–0.6 m. Short-circuit return is left wall z=1.6–2.2 m. Vent positions are snapped to cell faces; recorded configurations identify mesh resolution. The occupied mask is x=0.5–7.5 m and z=0.1–1.8 m, representing a section rather than actual occupancy.

## Comfort
Fanger heat-balance PMV and PPD are evaluated per cell, with RH=50%, met=1.2, clo=0.5, zero external work, mean radiant temperature fixed at 26°C. Air speed is floored at 0.05 m/s for comfort calculations. Reported mean PPD is the average of local PPD, not PPD of the mean PMV. These assumptions are not measured. Results are indicative and do not establish ISO 7730 or ASHRAE 55 compliance. Low-speed fraction (<0.05 m/s) and high-speed fraction (>0.2 m/s) are screening indicators, not formal dead-zone/draft criteria.

## Verification versus validation
Tests verify cell mass conservation, uniform temperature preservation with zero load and matching wall/supply temperatures, positive finite age, and one Fanger reference point (25°C, 0.1 m/s, 50% RH, 1.2 met, 0.5 clo: PMV about 0.08). Mesh sensitivity compares 80×30 with 120×45 cells; agreement does not validate the physical assumptions. No experimental benchmark or OpenFOAM/Fluent run has been performed.

## Engineering next steps
Use the comparison to prioritize cross-room distribution for further study. Both layouts show low occupied speed; do not infer that simply increasing fan flow will fix distribution. Test diffuser direction, multiple diffusers and occupied geometry in 3-D buoyant RANS; establish mesh independence, residual/flux/energy criteria and compare against measurements before design selection. Include humidity transport, radiation, sensible occupant gains and contaminant sources for an IAQ design study.

## Primary references
- OpenFOAM standard solvers: https://www.openfoam.com/documentation/user-guide/a-reference/a.1-standard-solvers
- OpenFOAM buoyantSimpleFoam documentation: https://doc.openfoam.com/2306/tools/processing/solvers/rtm/heat-transfer/buoyantSimpleFoam/
- EnergyPlus Fanger heat balance and PPD: https://energyplus.readthedocs.io/en/stable/guides/engineering-reference/19.1-occupant-thermal-comfort.html
