"""Backward-Euler heat transport with scheduled occupancy, supply and window gains.
Airflow is frozen potential flow; solar is absorbed heat, not ray-traced radiation.
"""
from dataclasses import dataclass, asdict
from pathlib import Path
import json
import numpy as np
from scipy.sparse import eye
from scipy.sparse.linalg import factorized
from .model import Config, solve, scalar_operator
from .comfort import pmv_ppd

@dataclass
class Workday:
    hours: float = 8.
    dt_s: float = 120.
    initial_c: float = 22.
    equipment_w: float = 150.
    watts_per_person: float = 75.
    solar_peak_w: float = 900.
    supply_swing_c: float = 1.5


def boundary_schedule(hour,c,day):
    """Illustrative workday, local hours since start; occupancy step schedule."""
    breaks=np.array([0,.5,2,3,4,5,6.5,8.])
    people=[2,8,8,3,0,8,6,0][min(np.searchsorted(breaks,hour,side='right')-1,7)]
    solar=day.solar_peak_w*np.exp(-.5*((hour-4)/.6)**2)
    supply=c.supply_c+day.supply_swing_c*np.sin(2*np.pi*hour/8)
    return dict(people=people,occupancy_w=people*day.watts_per_person,solar_w=float(solar),supply_c=float(supply))


def run_workday(layout='cross_room',c=None,day=None):
    c=c or Config(nx=40,nz=20); day=day or Workday()
    if not 0<day.dt_s<=600 or not 0<day.hours<=24 or day.solar_peak_w<0 or day.watts_per_person<0 or day.equipment_w<0:
        raise ValueError('Invalid transient settings')
    r=solve(layout,c); M,bs,bw=scalar_operator(c,r['qx'],r['qz'],True)
    vol=c.length*c.height*c.depth/(c.nx*c.nz); N=c.nx*c.nz
    nsteps=int(np.ceil(day.hours*3600/day.dt_s)); dt=day.hours*3600/nsteps
    advance=factorized((M+eye(N)*vol/dt).tocsc())
    T=np.full(N,day.initial_c); X,Z=np.meshgrid(r['x'],r['z'])
    window=(X>.85*c.length)&(Z>.3*c.height)&(Z<.8*c.height)
    window=window.ravel().astype(float); window/=window.sum()
    occupied=(X>=.5)&(X<=c.length-.5)&(Z>=.1)&(Z<=1.8)
    frames=[]; stats=[]; stride=max(1,round(600/dt))
    def record(t,s):
        tc=T.reshape(c.nz,c.nx); pmv,ppd=pmv_ppd(tc,c.wall_c,np.maximum(r['speed'],.05))
        frames.append(tc.copy())
        stats.append(dict(hour=t/3600,mean_c=float(tc[occupied].mean()),mean_pmv=float(pmv[occupied].mean()),mean_ppd=float(ppd[occupied].mean()),**s))
    record(0,boundary_schedule(0,c,day)); max_balance=0.
    for step in range(1,nsteps+1):
        s=boundary_schedule(step*dt/3600,c,day)
        heat=np.full(N,(day.equipment_w+s['occupancy_w'])/N)+window*s['solar_w']
        rhs=bs*s['supply_c']+bw*c.wall_c+heat/(1.2*1005)
        previous=T; T=advance(rhs+vol/dt*previous)
        balance=(vol/dt*(T-previous)+M@T-rhs).sum()*1.2*1005
        max_balance=max(max_balance,abs(float(balance)))
        if step%stride==0 or step==nsteps: record(step*dt,s)
    return dict(x=r['x'],z=r['z'],speed=r['speed'],frames=np.array(frames),stats=stats,config=asdict(c),workday=asdict(day),layout=layout,max_energy_balance_error_w=max_balance)


def export(output='results/transient'):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import csv
    out=Path(output); out.mkdir(parents=True,exist_ok=True)
    reports=[]
    fig,axes=plt.subplots(3,1,figsize=(11,9),sharex=True,constrained_layout=True)
    for layout in ['cross_room','short_circuit']:
        r=run_workday(layout); ss=r['stats']; reports.append({k:v for k,v in r.items() if k not in ['x','z','speed','frames']})
        np.savez_compressed(out/f'{layout}.npz',x=r['x'],z=r['z'],speed=r['speed'],T=r['frames'],hours=[s['hour'] for s in ss])
        with (out/f'{layout}.csv').open('w') as f:
            w=csv.DictWriter(f,fieldnames=ss[0]); w.writeheader(); w.writerows(ss)
        hours=[s['hour'] for s in ss]
        axes[0].plot(hours,[s['mean_c'] for s in ss],label=layout)
        axes[1].plot(hours,[s['mean_ppd'] for s in ss],label=layout)
    axes[2].plot(hours,[s['solar_w'] for s in ss],label='Window absorbed gain')
    axes[2].step(hours,[s['occupancy_w'] for s in ss],where='post',label='Occupancy gain')
    for ax,label in zip(axes,['Occupied mean temperature (°C)','Occupied mean PPD (%)','Heat input (W)']):ax.set_ylabel(label); ax.grid(alpha=.2); ax.legend()
    axes[2].set_xlabel('Hours since start of workday'); fig.suptitle('Eight-hour transient screening • prescribed gains, frozen potential airflow')
    fig.savefig(out/'workday.png',dpi=150); plt.close(fig)
    (out/'report.json').write_text(json.dumps(reports,indent=2))
if __name__=='__main__': export()
