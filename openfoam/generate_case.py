"""Generate 3-D OpenCFD v1912 buoyantBoussinesqSimpleFoam kOmegaSST cases.
Not compatible with arbitrary Foundation releases. Dimensions in metres/Kelvin.
"""
from pathlib import Path
import argparse,json

def header(name,cls='dictionary'):
    return f'FoamFile {{ version 2.0; format ascii; class {cls}; object {name}; }}\n'

def generate(root,layout='cross_room',scale=1,end=1000,transient=False):
    root=Path(root)
    if (root/'system/blockMeshDict').exists():
        raise FileExistsError(f'Case already exists: {root}; use a new output directory')
    for d in ['0','constant','system']: (root/d).mkdir(parents=True,exist_ok=True)
    def write(name,body,cls='dictionary'):
        (root/name).write_text(header(Path(name).name,cls)+body+'\n')
    xs=[0.,8.];ys=[0.,2.,3.,5.];zs=[0.,.6,1.6,2.2,2.4,3.]
    vertices=[(x,y,z) for z in zs for y in ys for x in xs]
    index=lambda i,j,k:k*8+j*2+i
    patches={'supply':[],'return':[],'walls':[]}
    blocks=[]
    for k in range(5):
        for j in range(3):
            v=[index(0,j,k),index(1,j,k),index(1,j+1,k),index(0,j+1,k),index(0,j,k+1),index(1,j,k+1),index(1,j+1,k+1),index(0,j+1,k+1)]
            nx=max(8,round(40*scale));ny=max(2,round((ys[j+1]-ys[j])*5*scale));nz=max(2,round((zs[k+1]-zs[k])*10*scale))
            blocks.append('hex ('+' '.join(map(str,v))+f') ({nx} {ny} {nz}) simpleGrading (1 1 1)')
            left=[v[n] for n in [0,4,7,3]];right=[v[n] for n in [1,2,6,5]]
            lpatch='supply' if j==1 and k==4 else 'return' if layout=='short_circuit' and j==1 and k==2 else 'walls'
            rpatch='return' if layout=='cross_room' and j==1 and k==0 else 'walls'
            patches[lpatch].append(left);patches[rpatch].append(right)
            if j==0: patches['walls'].append([v[n] for n in [0,1,5,4]])
            if j==2: patches['walls'].append([v[n] for n in [3,7,6,2]])
            if k==0: patches['walls'].append([v[n] for n in [0,3,2,1]])
            if k==4: patches['walls'].append([v[n] for n in [4,5,6,7]])
    body='scale 1;\nvertices (\n'+'\n'.join('('+ ' '.join(map(str,v))+')' for v in vertices)+'\n);\nblocks (\n'+'\n'.join(blocks)+'\n);\nedges ();\nboundary (\n'
    for patch,faces in patches.items():
        body+=patch+' { type '+('wall' if patch=='walls' else 'patch')+'; faces (\n'+'\n'.join('('+' '.join(map(str,f))+')' for f in faces)+'\n); }\n'
    write('system/blockMeshDict',body+');\nmergePatchPairs ();')
    def field(name,dimensions,internal,bcs,vector=False):
        write('0/'+name,f'dimensions [{dimensions}];\ninternalField uniform {internal};\nboundaryField {{\n'+''.join(p+' { '+bcs[p]+' }\n' for p in patches)+'}', 'volVectorField' if vector else 'volScalarField')
    field('U','0 1 -1 0 0 0 0','(0 0 0)',{'supply':'type fixedValue; value uniform (0.2 0 0);','return':'type pressureInletOutletVelocity; value uniform (0 0 0);','walls':'type noSlip;'},True)
    field('p_rgh','0 2 -2 0 0 0 0','0',{'supply':'type fixedFluxPressure; value uniform 0;','return':'type fixedValue; value uniform 0;','walls':'type fixedFluxPressure; value uniform 0;'})
    field('T','0 0 0 1 0 0 0','295.15',{'supply':'type fixedValue; value uniform 292.15;','return':'type inletOutlet; inletValue uniform 299.15; value uniform 295.15;','walls':'type fixedValue; value uniform 299.15;'})
    for name,dim,val,wall in [('k','0 2 -2 0 0 0 0','0.00015','kqRWallFunction'),('omega','0 0 -1 0 0 0 0','0.32','omegaWallFunction'),('nut','0 2 -1 0 0 0 0','0','nutkWallFunction'),('alphat','0 2 -1 0 0 0 0','0','alphatJayatillekeWallFunction')]:
        field(name,dim,val,{'supply':f'type '+('calculated' if name in ['nut','alphat'] else 'fixedValue')+f'; value uniform {val};','return':f'type '+('calculated' if name in ['nut','alphat'] else 'inletOutlet')+f'; '+(f'inletValue uniform {val}; ' if name not in ['nut','alphat'] else '')+f'value uniform {val};','walls':f'type {wall}; '+('Prt 0.85; ' if name=='alphat' else '')+f'value uniform {val};'})
    write('constant/g','dimensions [0 1 -2 0 0 0 0]; value (0 0 -9.81);','uniformDimensionedVectorField')
    write('constant/transportProperties','transportModel Newtonian;\nnu [0 2 -1 0 0 0 0] 1.5e-5;\nbeta [0 0 0 -1 0 0 0] 0.003333333;\nTRef [0 0 0 1 0 0 0] 295.15;\nPr [0 0 0 0 0 0 0] 0.71;\nPrt [0 0 0 0 0 0 0] 0.85;')
    write('constant/turbulenceProperties','simulationType RAS;\nRAS { RASModel kOmegaSST; turbulence on; printCoeffs on; }')
    write('constant/fvOptions','roomHeat { type scalarSemiImplicitSource; active yes; selectionMode all; volumeMode absolute; injectionRateSuSp { T (0.4975124378 0); } }')
    write('system/controlDict',f'application buoyantBoussinesqSimpleFoam;\nstartFrom startTime; startTime 0; stopAt endTime; endTime {end}; deltaT 1; writeControl timeStep; writeInterval {end}; purgeWrite 2; writeFormat ascii; writePrecision 8; runTimeModifiable true;\nfunctions {{\n residuals {{ type residuals; libs ("libutilityFunctionObjects.so"); fields (p_rgh U T k omega); }}\n yPlus {{ type yPlus; libs ("libfieldFunctionObjects.so"); writeControl writeTime; }}\n inletFlow {{ type surfaceFieldValue; libs ("libfieldFunctionObjects.so"); regionType patch; name supply; operation sum; fields (phi); writeControl timeStep; writeInterval 20; }}\n outletFlow {{ type surfaceFieldValue; libs ("libfieldFunctionObjects.so"); regionType patch; name return; operation sum; fields (phi); writeControl timeStep; writeInterval 20; }}\n}}')
    write('system/fvSchemes','ddtSchemes { default steadyState; }\ngradSchemes { default Gauss linear; }\ndivSchemes { default none; div(phi,U) bounded Gauss upwind; div(phi,T) bounded Gauss upwind; div(phi,k) bounded Gauss upwind; div(phi,omega) bounded Gauss upwind; div((nuEff*dev2(T(grad(U))))) Gauss linear; }\nlaplacianSchemes { default Gauss linear corrected; }\ninterpolationSchemes { default linear; }\nsnGradSchemes { default corrected; }\nwallDist { method meshWave; }\nfluxRequired { default no; p_rgh; }')
    write('system/fvSolution','solvers { p_rgh { solver GAMG; tolerance 1e-8; relTol 0.05; smoother GaussSeidel; } "(U|T|k|omega)" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-8; relTol 0.05; } }\nSIMPLE { nNonOrthogonalCorrectors 0; pRefCell 0; pRefValue 0; residualControl { p_rgh 1e-5; U 1e-6; T 1e-6; "(k|omega)" 1e-6; } }\nrelaxationFactors { fields { p_rgh 0.3; } equations { U 0.5; T 0.5; k 0.5; omega 0.5; } }')
    if transient:
        control=(root/'system/controlDict').read_text().replace('buoyantBoussinesqSimpleFoam','buoyantBoussinesqPimpleFoam').replace('deltaT 1;','deltaT 0.2; adjustTimeStep yes; maxCo 0.5; maxDeltaT 0.5;').replace('writeControl timeStep; writeInterval '+str(end)+';', 'writeControl adjustableRunTime; writeInterval '+str(end)+';')
        (root/'system/controlDict').write_text(control)
        schemes=(root/'system/fvSchemes').read_text().replace('default steadyState;','default Euler;')
        (root/'system/fvSchemes').write_text(schemes)
        solution=(root/'system/fvSolution').read_text()
        solution=solution.replace('solvers {','solvers { p_rghFinal { solver GAMG; tolerance 1e-8; relTol 0; smoother GaussSeidel; } "(U|T|k|omega)Final" { solver smoothSolver; smoother symGaussSeidel; tolerance 1e-8; relTol 0; } ')
        solution+='\nPIMPLE { nOuterCorrectors 2; nCorrectors 2; nNonOrthogonalCorrectors 0; pRefCell 0; pRefValue 0; }\n'
        (root/'system/fvSolution').write_text(solution)
    (root/'case.foam').touch()
    (root/'case.json').write_text(json.dumps(dict(layout=layout,dimensions_m=[8,5,3],flow_m3_s=.12,supply_c=19,wall_c=26,sensible_w=600,solver='buoyantBoussinesqPimpleFoam' if transient else 'buoyantBoussinesqSimpleFoam',release='OpenCFD v1912 (Ubuntu package 1912.200626)',turbulence='kOmegaSST',mesh_scale=scale,end_value=end,end_units='s' if transient else 'iteration',validation_status='not experimentally validated'),indent=2))
    return root
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--output',default='openfoam/cases/cross_room');p.add_argument('--layout',choices=['cross_room','short_circuit'],default='cross_room');p.add_argument('--scale',type=float,default=1.);p.add_argument('--end','--iterations',dest='iterations',type=int,default=1000);p.add_argument('--transient',action='store_true');a=p.parse_args()
    if a.scale<=0 or a.iterations<1:p.error('Positive scale and iterations required')
    print(generate(a.output,a.layout,a.scale,a.iterations,a.transient))
