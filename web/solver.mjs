// Browser counterpart of the Python conservative finite-volume screening model.
// No RANS, no turbulence or buoyancy. Solves actual transport, not interpolated images.
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
function multiply(A,x){return A.map((r,i)=>r.d*x[i]+r.n.reduce((s,[j,v])=>s+v*x[j],0))}
function linear(A,b,initial=null){
 const n=b.length,x=initial?Array.from(initial):Array(n).fill(0),Ax=multiply(A,x),r=b.map((v,i)=>v-Ax[i]),r0=r.slice();
 const tol=1e-10*Math.max(Math.sqrt(dot(b,b)),1e-8);
 if(Math.sqrt(dot(r,r))<tol)return x;
 let rhoOld=1,alpha=1,omega=1,p=Array(n).fill(0),v=Array(n).fill(0);
 for(let it=0;it<3000;it++){
  const rho=dot(r0,r);if(Math.abs(rho)<1e-40)break;
  const beta=(rho/rhoOld)*(alpha/omega);p=p.map((q,i)=>r[i]+beta*(q-omega*v[i]));
  const ph=p.map((q,i)=>q/A[i].d);v=multiply(A,ph);const denominator=dot(r0,v);if(Math.abs(denominator)<1e-40)break;
  alpha=rho/denominator;const s=r.map((q,i)=>q-alpha*v[i]);
  if(Math.sqrt(dot(s,s))<tol){for(let i=0;i<n;i++)x[i]+=alpha*ph[i];return x;}
  const sh=s.map((q,i)=>q/A[i].d),t=multiply(A,sh);omega=dot(t,s)/dot(t,t);
  for(let i=0;i<n;i++){x[i]+=alpha*ph[i]+omega*sh[i];r[i]=s[i]-omega*t[i]}
  if(Math.sqrt(dot(r,r))<tol)return x;
  if(!Number.isFinite(omega)||Math.abs(omega)<1e-35)break;rhoOld=rho;
 }
 throw Error('Linear solver did not converge. Try less extreme settings.');
}
export function comfort(ta,tr,vel){
 const rh=50,m=1.2*58.15,icl=.155*.5,fcl=1+1.29*icl,pa=rh*10*Math.exp(16.6536-4030.183/(ta+235));
 let lo=-50,hi=80,rad=0,conv=0;
 for(let k=0;k<70;k++){let tc=(lo+hi)/2,hc=Math.max(12.1*Math.sqrt(Math.max(.05,vel)),2.38*Math.abs(tc-ta)**.25);rad=3.96e-8*fcl*((tc+273)**4-(tr+273)**4);conv=fcl*hc*(tc-ta);if(tc-(35.7-.028*m-icl*(rad+conv))>0)hi=tc;else lo=tc;}
 const load=m-.00305*(5733-6.99*m-pa)-Math.max(.42*(m-58.15),0)-1.7e-5*m*(5867-pa)-.0014*m*(34-ta)-rad-conv;
 const pmv=(.303*Math.exp(-.036*m)+.028)*load;return [pmv,100-95*Math.exp(-.03353*pmv**4-.2179*pmv**2)];
}
export function screen(input={}){
 const c={nx:32,nz:16,length:8,height:3,depth:5,ach:3.6,supply_c:19,wall_c:26,diffusivity:.01,sensible_w:600,layout:'cross_room',solar_peak_w:900,supply_swing_c:1.5,...input};
 const {nx,nz,length:L,height:H,depth:D}=c,N=nx*nz,dx=L/nx,dz=H/nz,vol=dx*dz*D,Q=c.ach*L*H*D/3600;
 if(!Object.values(c).filter(v=>typeof v==='number').every(Number.isFinite)||L<4||H<2.5||D<3||Q<=0)throw Error('Invalid room parameters');
 const qx=Array.from({length:nz},()=>Array(nx+1).fill(0)),qz=Array.from({length:nz+1},()=>Array(nx).fill(0));
 const x=Array.from({length:nx},(_,i)=>(i+.5)*dx),z=Array.from({length:nz},(_,j)=>(j+.5)*dz);
 const inlet=z.map((v,j)=>v>.8*H?j:-1).filter(j=>j>=0),outlet=z.map((v,j)=>(c.layout==='cross_room'?v<.2*H:v>1.6/3*H&&v<2.2/3*H)?j:-1).filter(j=>j>=0);
 inlet.forEach(j=>qx[j][0]=Q/inlet.length);outlet.forEach(j=>{if(c.layout==='cross_room')qx[j][nx]=Q/outlet.length;else qx[j][0]=-Q/outlet.length});
 let A=[],b=[];
 for(let j=0;j<nz;j++)for(let i=0;i<nx;i++){
  const k=j*nx+i,row={d:0,n:[]};
  for(const [jj,ii,g] of [[j,i-1,dz*D/dx],[j,i+1,dz*D/dx],[j-1,i,dx*D/dz],[j+1,i,dx*D/dz]])if(jj>=0&&jj<nz&&ii>=0&&ii<nx){row.d+=g;row.n.push([jj*nx+ii,-g]);}
  A.push(row);b.push(-(qx[j][i+1]-qx[j][i]+qz[j+1][i]-qz[j][i]));
 }
 A[0]={d:1,n:[]};b[0]=0;const p=linear(A,b);
 for(let j=0;j<nz;j++)for(let i=1;i<nx;i++)qx[j][i]=(p[j*nx+i-1]-p[j*nx+i])*dz*D/dx;
 for(let j=1;j<nz;j++)for(let i=0;i<nx;i++)qz[j][i]=(p[(j-1)*nx+i]-p[j*nx+i])*dx*D/dz;
 let maxMass=0;const speed=[];
 for(let j=0;j<nz;j++)for(let i=0;i<nx;i++){maxMass=Math.max(maxMass,Math.abs(qx[j][i+1]-qx[j][i]+qz[j+1][i]-qz[j][i]));speed.push(Math.hypot((qx[j][i]+qx[j][i+1])/(2*dz*D),(qz[j][i]+qz[j+1][i])/(2*dx*D)));}
 function operator(heat){const M=[],supply=[],wall=[];
 for(let j=0;j<nz;j++)for(let i=0;i<nx;i++){
  const row={d:0,n:[]};let bs=0,bw=0;
  for(const [jj,ii,f,g] of [[j,i-1,-qx[j][i],dz*D/dx],[j,i+1,qx[j][i+1],dz*D/dx],[j-1,i,-qz[j][i],dx*D/dz],[j+1,i,qz[j+1][i],dx*D/dz]]){
   row.d+=Math.max(f,0);
   if(jj>=0&&jj<nz&&ii>=0&&ii<nx){const d=c.diffusivity*g;row.d+=d;row.n.push([jj*nx+ii,Math.min(f,0)-d]);}
   else if(f<0)bs-=f;
   else if(heat&&Math.abs(f)<1e-14){const conductance=(ii<0||ii>=nx?dz*D:dx*D)/(1.2*1005);row.d+=conductance;bw+=conductance;}
  }M.push(row);supply.push(bs);wall.push(bw);
 }return {M,supply,wall};}
 const th=operator(true),ag=operator(false);
 const T=linear(th.M,th.supply.map((v,k)=>v*c.supply_c+th.wall[k]*c.wall_c+c.sensible_w/N/(1.2*1005)));
 const age=linear(ag.M,Array(N).fill(vol));
 const occupied=[];for(let j=0;j<nz;j++)for(let i=0;i<nx;i++)if(x[i]>=.5&&x[i]<=L-.5&&z[j]>=.1&&z[j]<=1.8)occupied.push(j*nx+i);
 const mean=a=>occupied.reduce((s,k)=>s+a[k],0)/occupied.length;
 function summarize(t){const cp=t.map((v,k)=>comfort(v,c.wall_c,speed[k]));return {temperature:mean(t),pmv:mean(cp.map(v=>v[0])),ppd:mean(cp.map(v=>v[1]))};}
 const base={config:c,x,z,speed,T,age,metrics:{...summarize(T),air_age:mean(age),max_mass_imbalance:maxMass}};
 if(!c.transient)return base;
 let now=Array(N).fill(22);const dt=120,implicit=th.M.map(r=>({d:r.d+vol/dt,n:r.n}));
 const window=Array(N).fill(0);let count=0;for(let j=0;j<nz;j++)for(let i=0;i<nx;i++)if(x[i]>.85*L&&z[j]>.3*H&&z[j]<.8*H){window[j*nx+i]=1;count++;}
 const frames=[],history=[];
 function gains(h){let n=0;[0,.5,2,3,4,5,6.5,8].forEach((t,i)=>{if(h>=t)n=i});return {people:[2,8,8,3,0,8,6,0][n],solar:c.solar_peak_w*Math.exp(-.5*((h-4)/.6)**2),supply:c.supply_c+c.supply_swing_c*Math.sin(2*Math.PI*h/8)};}
 function record(h){frames.push(now.slice());history.push({hour:h,...summarize(now),...gains(h)});}
 record(0);
 for(let step=1;step<=240;step++){let h=step*dt/3600,g=gains(h);now=linear(implicit,th.supply.map((v,k)=>v*g.supply+th.wall[k]*c.wall_c+((150+75*g.people)/N+window[k]/count*g.solar)/(1.2*1005)+vol/dt*now[k]),now);if(step%5===0)record(h);}
 return {...base,frames,history};
}
