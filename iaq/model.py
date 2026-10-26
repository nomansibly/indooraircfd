"""Conservative 2-D potential-flow and upwind scalar screening model (SI units)."""
from dataclasses import dataclass, asdict
import numpy as np
from scipy.sparse import lil_matrix
from scipy.sparse.linalg import spsolve

@dataclass
class Config:
    nx: int = 80
    nz: int = 30
    length: float = 8.
    height: float = 3.
    depth: float = 5.
    flow: float = .12  # m3/s, shared by both layouts
    supply_c: float = 19.
    wall_c: float = 26.
    sensible_w: float = 600.
    diffusivity: float = .01  # effective scalar mixing, not a turbulence closure


def solve(layout='cross_room', c=None):
    c = c or Config()
    if layout not in ('cross_room', 'short_circuit'):
        raise ValueError('Unknown layout')
    validate(c)
    nx,nz=c.nx,c.nz; dx,dz=c.length/nx,c.height/nz
    N=nx*nz; vol=dx*dz*c.depth
    idx=lambda j,i:j*nx+i
    # Face volume flow: positive right/up. Uniform total supply for each layout.
    qx=np.zeros((nz,nx+1)); qz=np.zeros((nz+1,nx))
    inlet=np.arange(nz)[(np.arange(nz)+.5)*dz>.8*c.height]
    outlet=inlet if layout=='short_circuit' else np.arange(nz)[(np.arange(nz)+.5)*dz<.2*c.height]
    qx[inlet,0]=c.flow/len(inlet)
    if layout=='cross_room': qx[outlet,-1]=c.flow/len(outlet)
    else: qx[np.arange(nz)[((np.arange(nz)+.5)*dz>(1.6/3)*c.height)&((np.arange(nz)+.5)*dz<(2.2/3)*c.height)],0]=-c.flow/sum(((np.arange(nz)+.5)*dz>(1.6/3)*c.height)&((np.arange(nz)+.5)*dz<(2.2/3)*c.height))
    A=lil_matrix((N,N)); b=np.zeros(N)
    for j in range(nz):
        for i in range(nx):
            k=idx(j,i)
            for jj,ii,g in [(j,i-1,dz*c.depth/dx),(j,i+1,dz*c.depth/dx),(j-1,i,dx*c.depth/dz),(j+1,i,dx*c.depth/dz)]:
                if 0<=jj<nz and 0<=ii<nx: A[k,k]+=g; A[k,idx(jj,ii)]-=g
            b[k]=-(qx[j,i+1]-qx[j,i]+qz[j+1,i]-qz[j,i])
    A[0,:]=0; A[0,0]=1; b[0]=0
    p=spsolve(A.tocsr(),b).reshape(nz,nx)
    qx[:,1:-1]=(p[:,:-1]-p[:,1:])*dz*c.depth/dx
    qz[1:-1,:]=(p[:-1,:]-p[1:,:])*dx*c.depth/dz
    divergence=qx[:,1:]-qx[:,:-1]+qz[1:,:]-qz[:-1,:]
    def scalar(source,inlet_value,heat=False):
        M, supply_rhs, wall_rhs = scalar_operator(c,qx,qz,heat)
        rhs=np.full(N,source*vol)+supply_rhs*inlet_value+wall_rhs*c.wall_c
        return spsolve(M,rhs).reshape(nz,nx)
    T=scalar(c.sensible_w/(c.length*c.height*c.depth*1.2*1005),c.supply_c,True)
    age=scalar(1.,0.)
    u=(qx[:,:-1]+qx[:,1:])/(2*dz*c.depth)
    w=(qz[:-1,:]+qz[1:,:])/(2*dx*c.depth)
    speed=np.hypot(u,w)
    x=(np.arange(nx)+.5)*dx; z=(np.arange(nz)+.5)*dz
    occupied=(z[:,None]>=.1)&(z[:,None]<=1.8)&(x[None,:]>=.5)&(x[None,:]<=c.length-.5)
    from .comfort import pmv_ppd
    pmv,ppd=pmv_ppd(T,c.wall_c,np.maximum(speed,.05))
    nominal=c.length*c.height*c.depth/c.flow
    metrics=dict(layout=layout,ach=c.flow*3600/(c.length*c.height*c.depth),max_cell_mass_imbalance_m3_s=float(abs(divergence).max()),occupied_mean_temperature_c=float(T[occupied].mean()),occupied_mean_age_s=float(age[occupied].mean()),occupied_air_change_index=float(nominal/age[occupied].mean()),whole_room_air_exchange_efficiency=float(nominal/(2*age.mean())),low_speed_fraction=float((speed[occupied]<.05).mean()),high_speed_fraction=float((speed[occupied]>.2).mean()),occupied_mean_pmv=float(pmv[occupied].mean()),occupied_mean_ppd=float(ppd[occupied].mean()))
    return dict(x=x,z=z,u=u,w=w,T=T,age=age,speed=speed,pmv=pmv,ppd=ppd,metrics=metrics,config=asdict(c),qx=qx,qz=qz)


def validate(c):
    values=[c.length,c.height,c.depth,c.flow,c.diffusivity,c.supply_c,c.wall_c,c.sensible_w]
    if not np.isfinite(values).all() or min(c.length,c.depth)<=1 or c.height<2 or c.flow<=0 or c.diffusivity<=0 or c.nx<16 or c.nz<10:
        raise ValueError('Use finite inputs, length/depth >1 m, height >=2 m, positive flow/diffusivity, nx>=16, nz>=10')


def scalar_operator(c,qx,qz,heat=False):
    """Return conservative transport matrix plus unit supply/wall-temperature RHS."""
    nx,nz=c.nx,c.nz; dx,dz=c.length/nx,c.height/nz; N=nx*nz
    M=lil_matrix((N,N)); supply=np.zeros(N); wall=np.zeros(N)
    for j in range(nz):
        for i in range(nx):
            k=j*nx+i
            faces=[(j,i-1,-qx[j,i],dz*c.depth/dx),(j,i+1,qx[j,i+1],dz*c.depth/dx),(j-1,i,-qz[j,i],dx*c.depth/dz),(j+1,i,qz[j+1,i],dx*c.depth/dz)]
            for jj,ii,f,g in faces:
                M[k,k]+=max(f,0)
                if 0<=jj<nz and 0<=ii<nx:
                    M[k,jj*nx+ii]+=min(f,0)
                    d=c.diffusivity*g; M[k,k]+=d; M[k,jj*nx+ii]-=d
                elif f<0: supply[k]-=f
                elif heat and abs(f)<1e-14:
                    area=dz*c.depth if ii<0 or ii>=nx else dx*c.depth
                    conductance=area/(1.2*1005)
                    M[k,k]+=conductance; wall[k]+=conductance
    return M.tocsr(),supply,wall
