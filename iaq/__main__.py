from pathlib import Path
import argparse,json,csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .model import solve,Config

def main():
    p=argparse.ArgumentParser(); p.add_argument('--nx',type=int,default=80); p.add_argument('--nz',type=int,default=30); p.add_argument('--output',default='results'); a=p.parse_args()
    if a.nx<16 or a.nz<10: p.error('Use nx>=16, nz>=10 to resolve vents')
    out=Path(a.output); out.mkdir(parents=True,exist_ok=True)
    runs=[solve(s,Config(nx=a.nx,nz=a.nz)) for s in ['cross_room','short_circuit']]
    plt.rcParams.update({'font.size':10,'figure.facecolor':'#f5f7fb'})
    for key,label,cmap in [('speed','Air speed (m/s)','viridis'),('T','Air temperature (°C)','inferno'),('age','Local mean age (s)','magma'),('pmv','Predicted mean vote','coolwarm')]:
        fig,axes=plt.subplots(2,1,figsize=(12,7),constrained_layout=True)
        vmin=min(r[key].min() for r in runs); vmax=max(r[key].max() for r in runs)
        for ax,r in zip(axes,runs):
            im=ax.pcolormesh(r['x'],r['z'],r[key],shading='nearest',cmap=cmap,vmin=vmin,vmax=vmax)
            if key=='speed': ax.streamplot(r['x'],r['z'],r['u'],r['w'],color='white',density=.7,linewidth=.6)
            ax.set(title=r['metrics']['layout'].replace('_',' ').title(),xlabel='Room length (m)',ylabel='Height (m)',aspect='equal')
            ax.axhline(1.8,color='cyan',ls='--',lw=.8)
        fig.colorbar(im,ax=axes,label=label); fig.suptitle('Indoor Air Lab • 2-D potential-flow screening • NOT validated RANS')
        fig.savefig(out/f'{key}.png',dpi=160); plt.close(fig)
    for r in runs:
        np.savez_compressed(out/(r['metrics']['layout']+'.npz'),**{k:v for k,v in r.items() if isinstance(v,np.ndarray)})
    (out/'summary.json').write_text(json.dumps([r['metrics'] for r in runs],indent=2))
    with (out/'comparison.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=runs[0]['metrics']); w.writeheader(); w.writerows(r['metrics'] for r in runs)
    print((out/'summary.json').read_text())
if __name__=='__main__': main()
