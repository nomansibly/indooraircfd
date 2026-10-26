"""Python dashboard: streamlit run streamlit_app.py"""
import json
from dataclasses import asdict
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from iaq.model import Config, solve
from iaq.transient import Workday,run_workday
from iaq.comfort import pmv_ppd
st.set_page_config(page_title='Indoor Air Lab',page_icon='🌿',layout='wide')
st.title('Indoor Air Lab')
st.caption('Sibly Noman · Reproducible finite-volume ventilation screening')
st.info('This dashboard solves a 2-D potential-flow screening model. It does not run 3-D RANS. Transient solar gains are prescribed absorbed heat, not a radiation solution.')
with st.sidebar:
    st.header('Room and ventilation')
    length=st.slider('Length (m)',4.,12.,8.,.5)
    depth=st.slider('Depth (m)',3.,8.,5.,.5)
    height=st.slider('Height (m)',2.5,4.5,3.,.1)
    ach=st.slider('Air changes per hour',1.,10.,3.6,.2)
    supply=st.slider('Supply temperature (°C)',16.,24.,19.,.5)
    wall=st.slider('Wall / radiant temperature (°C)',20.,30.,26.,.5)
    layout=st.selectbox('Return arrangement',['cross_room','short_circuit'])
    mode=st.radio('Analysis',['Steady screening','8-hour workday'])
c=Config(nx=40,nz=20,length=length,depth=depth,height=height,flow=ach*length*depth*height/3600,supply_c=supply,wall_c=wall)
@st.cache_data(max_entries=24,show_spinner='Solving conservative transport equations…')
def steady(config,layout):return solve(layout,Config(**config))
@st.cache_data(max_entries=12,show_spinner='Integrating eight-hour heat transport…')
def transient(config,layout,solar,swing):return run_workday(layout,Config(**config),Workday(solar_peak_w=solar,supply_swing_c=swing))
if mode=='Steady screening':
    r=steady(asdict(c),layout); T=r['T']; speed=r['speed']; m=r['metrics']
    a,b,d=st.columns(3); a.metric('Mean occupied temperature',f"{m['occupied_mean_temperature_c']:.2f} °C");b.metric('Mean PMV',f"{m['occupied_mean_pmv']:.2f}");d.metric('Mean local PPD',f"{m['occupied_mean_ppd']:.1f}%")
else:
    solar=st.sidebar.slider('Peak absorbed window gain (W)',0,1800,900,100)
    swing=st.sidebar.slider('Supply temperature swing (°C)',0.,3.,1.5,.5)
    r=transient(asdict(c),layout,solar,swing)
    hour=st.slider('Workday hour',0.,8.,4.,1/6)
    index=int(np.argmin(np.abs(np.array([s['hour'] for s in r['stats']])-hour)))
    T=r['frames'][index];speed=r['speed']
    history=pd.DataFrame(r['stats'])
    st.line_chart(history.set_index('hour')[['mean_c']]);st.caption(f"Conservation residual: {r['max_energy_balance_error_w']:.2e} W. Initial air: 22°C. Equipment: 150 W. Occupants: 75 W/person.")
    st.download_button('Download workday history CSV',history.to_csv(index=False),'workday.csv','text/csv')
pmv,ppd=pmv_ppd(T,wall,np.maximum(speed,.05))
field=st.selectbox('Contour field',['Temperature (°C)','PMV','PPD (%)','Air speed (m/s)'])
values={'Temperature (°C)':T,'PMV':pmv,'PPD (%)':ppd,'Air speed (m/s)':speed}[field]
fig=go.Figure(go.Contour(x=r['x'],y=r['z'],z=values,colorscale='RdBu_r' if field=='PMV' else 'Viridis',colorbar_title=field,contours_coloring='heatmap'))
fig.update_layout(xaxis_title='Room length (m)',yaxis_title='Height (m)',height=480,margin=dict(l=20,r=20,t=20,b=20));fig.update_yaxes(scaleanchor='x',scaleratio=1)
st.plotly_chart(fig,width='stretch')
st.caption('Comfort assumptions: RH 50%, 1.2 met, 0.5 clo, mean radiant temperature = chosen wall temperature; speed floored at 0.05 m/s. Vent heights scale with room height.')
st.download_button('Download configuration JSON',json.dumps(asdict(c),indent=2),'config.json','application/json')
st.link_button('Source and 3-D OpenFOAM case','https://github.com/siblynoman2003-beep/indooraircfd')
