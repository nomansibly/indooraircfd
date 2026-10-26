"""Export cell fields and 3-D URANS cross-sections; requires meshio.
Usage: python openfoam/analyze.py CASE --layout cross_room --log solver.log
"""
from pathlib import Path
import argparse,json,re
import numpy as np
import meshio
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from iaq.comfort import pmv_ppd

def patch_flux(text,patch):
    boundary=text.split('boundaryField',1)[1]
    match=re.search(r'\b'+re.escape(patch)+r'\s*\{(.*?)\n\s*\}',boundary,re.S)
    if not match:raise ValueError('Patch not found')
    values=re.search(r'value\s+nonuniform\s+List<scalar>\s+(\d+)\s*\((.*?)\)',match[1],re.S)
    if values:return float(np.fromstring(values[2],sep=' ').sum())
    raise ValueError('Expected nonuniform flux boundary')

def analyze(case,layout,log,output='results/rans'):
    case=Path(case);out=Path(output);out.mkdir(parents=True,exist_ok=True)
    files=list((case/'VTK').rglob('internal.vtu'))
    if not files:raise FileNotFoundError('Run foamToVTK first')
    file=max(files,key=lambda p:p.stat().st_mtime);mesh=meshio.read(file)
    hexes=mesh.cells_dict['hexahedron'];points=mesh.points[hexes]
    centers=points.mean(axis=1);volumes=np.prod(np.ptp(points,axis=1),axis=1)
    T=mesh.cell_data_dict['T']['hexahedron']-273.15;U=mesh.cell_data_dict['U']['hexahedron'];k=mesh.cell_data_dict['k']['hexahedron'];omega=mesh.cell_data_dict['omega']['hexahedron']
    speed=np.linalg.norm(U,axis=1);pmv,ppd=pmv_ppd(T,26,np.maximum(speed,.05))
    if not np.isfinite(T).all() or not np.isfinite(U).all() or k.min()<0 or omega.min()<0:raise ValueError('Nonphysical or nonfinite fields')
    occupied=(centers[:,0]>.5)&(centers[:,0]<7.5)&(centers[:,2]>.1)&(centers[:,2]<1.8)
    mean=lambda a:float(np.average(a[occupied],weights=volumes[occupied]))
    time=float(mesh.field_data['TimeValue'][0]);phi=(case/f'{time:g}'/'phi').read_text();inflow=patch_flux(phi,'supply');outflow=patch_flux(phi,'return')
    text=Path(log).read_text();matches=re.findall(r'Solving for (\w+), Initial residual = ([\deE+.-]+), Final residual = ([\deE+.-]+)',text)
    last={name:{'initial':float(i),'linear_final':float(f)} for name,i,f in matches}
    continuity=re.findall(r'continuity errors : sum local = ([\deE+.-]+), global = ([\deE+.-]+)',text)
    report=dict(layout=layout,solver='buoyantBoussinesqPimpleFoam',turbulence='kOmegaSST',release='OpenCFD v1912 patch 200626 / Ubuntu 24.04 package',time_s=time,cells=len(T),volume_m3=float(volumes.sum()),occupied_mean_temperature_c=mean(T),occupied_mean_speed_m_s=mean(speed),occupied_mean_pmv=mean(pmv),occupied_mean_ppd=mean(ppd),temperature_range_c=[float(T.min()),float(T.max())],speed_max_m_s=float(speed.max()),inlet_flux_m3_s=inflow,outlet_flux_m3_s=outflow,relative_net_boundary_flux=abs(inflow+outflow)/abs(inflow),last_equation_residuals=last,last_continuity={'local':float(continuity[-1][0]),'global':float(continuity[-1][1])},status='Executed 600 s URANS startup snapshot on coarse mesh. Not steady, time-averaged, mesh-independent, wall-resolution-qualified or experimentally validated.',wall_boundary='Fixed 26°C; differs from Python Robin wall heat exchange.',comfort_assumptions='RH50%, met1.2, clo0.5, MRT26°C, speed floor0.05m/s')
    (out/f'{layout}.json').write_text(json.dumps(report,indent=2))
    np.savez_compressed(out/f'{layout}.npz',centers=centers,volume=volumes,T=T,U=U,k=k,omega=omega,pmv=pmv,ppd=ppd)
    # Sample y=2.5 m through interpolation of computed 3-D cell values.
    x,z=np.meshgrid(np.linspace(.2,7.8,100),np.linspace(.1,2.9,45));query=np.c_[x.ravel(),np.full(x.size,2.5),z.ravel()]
    def section(data):return griddata(centers,data,query,method='linear').reshape(x.shape)
    fig,axes=plt.subplots(2,1,figsize=(11,8),constrained_layout=True)
    image=axes[0].contourf(x,z,section(T),levels=18,cmap='inferno');fig.colorbar(image,ax=axes[0],label='Temperature (°C)')
    image=axes[1].contourf(x,z,section(speed),levels=18,cmap='viridis');fig.colorbar(image,ax=axes[1],label='Speed (m/s)')
    axes[1].streamplot(x[0],z[:,0],section(U[:,0]),section(U[:,2]),color='white',density=.9,linewidth=.6)
    for ax in axes:ax.set(xlabel='Length (m)',ylabel='Height (m)',aspect='equal')
    fig.suptitle(f'3-D k–ω SST URANS • {layout} • t={time:g} s\nCoarse startup snapshot, y=2.5 m section • not a validated design')
    fig.savefig(out/f'{layout}.png',dpi=150);plt.close(fig)
    return report
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('case');p.add_argument('--layout',required=True);p.add_argument('--log',required=True);p.add_argument('--output',default='results/rans');a=p.parse_args();print(json.dumps(analyze(a.case,a.layout,a.log,a.output),indent=2))
