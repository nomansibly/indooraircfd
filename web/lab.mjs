import {comfort} from './solver.mjs';
const $=id=>document.getElementById(id),keys=['length','depth','height','ach','supply_c','wall_c','solar_peak_w'],units={length:' m',depth:' m',height:' m',ach:'',supply_c:'°C',wall_c:'°C',solar_peak_w:' W'};
let result=null,worker=null,timer=null,busy=false;
const palette=[[68,1,84],[59,82,139],[33,145,140],[94,201,98],[253,231,37]];
function color(t){t=Math.max(0,Math.min(1,t))*4;const i=Math.min(3,Math.floor(t)),f=t-i;return `rgb(${palette[i].map((v,j)=>Math.round(v+(palette[i+1][j]-v)*f)).join(',')})`;}
function parameters(){return Object.fromEntries(keys.map(k=>[k,+$(k).value]).concat([['layout',$('layout').value],['transient',$('mode').value==='transient']]));}
function run(){
 clearTimeout(timer);if(worker)worker.terminate();busy=true;$('run').disabled=true;$('download').disabled=true;$('status').textContent='Solving airflow and scalar transport…';
 const transient=$('mode').value==='transient';document.querySelectorAll('.transient-only').forEach(el=>el.hidden=!transient);
 worker=new Worker('./worker.mjs',{type:'module'});const start=performance.now();
 worker.onmessage=e=>{busy=false;$('run').disabled=false;if(!e.data.ok){$('status').textContent='Solver error: '+e.data.error;return;}result=e.data.result;result.solve_ms=performance.now()-start;$('download').disabled=false;render();};
 worker.onerror=()=>{busy=false;$('run').disabled=false;$('status').textContent='Could not start browser solver. Please reload or use the Python app.';};worker.postMessage(parameters());
}
function render(){if(!result)return;const r=result,c=r.config,transient=!!r.frames,idx=+$('hour').value;const t=transient?r.frames[idx]:r.T,cp=t.map((v,k)=>comfort(v,c.wall_c,r.speed[k]));
 const field=$('field').value,data={T:t,pmv:cp.map(v=>v[0]),ppd:cp.map(v=>v[1]),speed:r.speed,age:r.age}[field];
 let occupied=[];for(let j=0;j<c.nz;j++)for(let i=0;i<c.nx;i++)if(r.x[i]>=.5&&r.x[i]<=c.length-.5&&r.z[j]>=.1&&r.z[j]<=1.8)occupied.push(j*c.nx+i);
 const mean=a=>occupied.reduce((s,k)=>s+a[k],0)/occupied.length;
 $('mean-t').textContent=mean(t).toFixed(2)+'°C';$('mean-pmv').textContent=mean(cp.map(v=>v[0])).toFixed(2);$('mean-ppd').textContent=mean(cp.map(v=>v[1])).toFixed(1)+'%';
 $('time-area').hidden=!transient;$('history-area').hidden=!transient;
 if(transient){const s=r.history[idx];$('hour-value').textContent=s.hour.toFixed(2)+' h';$('load-status').textContent=`${s.people} occupants · absorbed window gain ${s.solar.toFixed(0)} W · supply ${s.supply.toFixed(1)}°C`;
 const can=$('history'),ctx=can.getContext('2d');ctx.clearRect(0,0,can.width,can.height);const values=r.history.map(s=>s.temperature),min=Math.floor(Math.min(...values)-.5),max=Math.ceil(Math.max(...values)+.5);ctx.strokeStyle='#194c40';ctx.lineWidth=3;ctx.beginPath();values.forEach((v,i)=>{let x=65+i/(values.length-1)*970,y=210-(v-min)/(max-min)*170;i?ctx.lineTo(x,y):ctx.moveTo(x,y)});ctx.stroke();ctx.fillStyle='#67736c';ctx.font='17px system-ui';for(let i=0;i<=8;i++)ctx.fillText(i+' h',55+i/8*970,245);ctx.fillText(max+'°C',5,38);ctx.fillText(min+'°C',5,212);}
 const can=$('contour'),ctx=can.getContext('2d');ctx.clearRect(0,0,can.width,can.height);let min=Math.min(...data),max=Math.max(...data);if(field==='pmv'){max=Math.max(1,Math.abs(min),Math.abs(max));min=-max;}if(field==='ppd'){min=5;max=Math.min(100,Math.max(15,max));}if(Math.abs(max-min)<1e-10)max=min+1;
 const left=70,top=30,width=960,height=390;const dx=width/c.nx,dz=height/c.nz;
 for(let j=0;j<c.nz;j++)for(let i=0;i<c.nx;i++){ctx.fillStyle=color((data[j*c.nx+i]-min)/(max-min));ctx.fillRect(left+i*dx,top+height-(j+1)*dz,dx+.6,dz+.6);}
 // Marching squares: equal-value segments across interpolated cell-centre edges.
 ctx.strokeStyle='rgba(255,255,255,.45)';ctx.lineWidth=.8;
 for(let level=1;level<=9;level++){const v=min+(max-min)*level/10;ctx.beginPath();for(let j=0;j<c.nz-1;j++)for(let i=0;i<c.nx-1;i++){
 const vertices=[[i,j,data[j*c.nx+i]],[i+1,j,data[j*c.nx+i+1]],[i+1,j+1,data[(j+1)*c.nx+i+1]],[i,j+1,data[(j+1)*c.nx+i]]],hits=[];
 for(let a=0;a<4;a++){const p=vertices[a],q=vertices[(a+1)%4];if((p[2]<v)!==(q[2]<v)){const f=(v-p[2])/(q[2]-p[2]);hits.push([left+(p[0]+.5+f*(q[0]-p[0]))*dx,top+height-(p[1]+.5+f*(q[1]-p[1]))*dz]);}}
 for(let a=0;a+1<hits.length;a+=2){ctx.moveTo(...hits[a]);ctx.lineTo(...hits[a+1]);}}
 ctx.stroke();}
 ctx.strokeStyle='#172b28';ctx.strokeRect(left,top,width,height);ctx.fillStyle='#425046';ctx.font='17px system-ui';for(let i=0;i<=4;i++)ctx.fillText((c.length*i/4).toFixed(1),left+i/4*width-10,top+height+27);ctx.fillText('Length (m)',left+width/2-40,top+height+53);for(let j=0;j<=3;j++)ctx.fillText((c.height*j/3).toFixed(1),24,top+height-j/3*height+5);ctx.save();ctx.translate(16,240);ctx.rotate(-Math.PI/2);ctx.fillText('Height (m)',0,0);ctx.restore();for(let i=0;i<300;i++){ctx.fillStyle=color(i/299);ctx.fillRect(730+i,492,1,14);}ctx.fillStyle='#425046';ctx.fillText(min.toFixed(field==='speed'?3:1),650,506);ctx.fillText(max.toFixed(field==='speed'?3:1),1040,506);
 $('plot-title').textContent=$('field').selectedOptions[0].textContent;
 $('status').textContent=`Solved ${c.nx} × ${c.nz} cells in ${(r.solve_ms/1000).toFixed(2)} s · maximum cell volume-flux imbalance ${r.metrics.max_mass_imbalance.toExponential(1)} m³/s. ${transient&&field==='age'?'Air age is the stationary field for the fixed airflow.':''}`;
}
keys.forEach(k=>$(k).addEventListener('input',()=>{$(k+'-value').textContent=$(k).value+units[k];clearTimeout(timer);timer=setTimeout(run,350)}));['layout','mode'].forEach(k=>$(k).addEventListener('change',run));$('run').addEventListener('click',run);$('field').addEventListener('change',render);$('hour').addEventListener('input',render);
$('download').addEventListener('click',()=>{if(!result||busy)return;const blob=new Blob([JSON.stringify(result)],{type:'application/json'}),url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download='indoor-air-result.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000)});run();
