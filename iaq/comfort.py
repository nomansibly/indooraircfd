"""Fanger heat-balance PMV; fixed RH/met/clo defaults are explicit assumptions."""
import numpy as np

def pmv_ppd(ta,tr,vel,rh=50.,met=1.2,clo=.5):
    ta,tr,vel=np.broadcast_arrays(np.asarray(ta,float),np.asarray(tr,float),np.asarray(vel,float))
    if np.any(vel<0) or not 0<=rh<=100 or met<=0 or clo<0: raise ValueError('Invalid comfort inputs')
    pa=rh*10*np.exp(16.6536-4030.183/(ta+235))
    icl=.155*clo; m=met*58.15; fcl=1+1.29*icl if icl<=.078 else 1.05+.645*icl
    # Monotonic clothing-surface balance solved by bisection.
    lo=np.full(ta.shape,-50.); hi=np.full(ta.shape,80.)
    for _ in range(100):
        tc=(lo+hi)/2; hc=np.maximum(12.1*np.sqrt(vel),2.38*np.abs(tc-ta)**.25)
        rad=3.96e-8*fcl*((tc+273)**4-(tr+273)**4)
        conv=fcl*hc*(tc-ta)
        residual=tc-(35.7-.028*m-icl*(rad+conv))
        hi=np.where(residual>0,tc,hi); lo=np.where(residual<=0,tc,lo)
    load=m-3.05e-3*(5733-6.99*m-pa)-max(.42*(m-58.15),0)-1.7e-5*m*(5867-pa)-.0014*m*(34-ta)-rad-conv
    pmv=(.303*np.exp(-.036*m)+.028)*load
    return pmv,100-95*np.exp(-.03353*pmv**4-.2179*pmv**2)
