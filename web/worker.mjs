import {screen} from './solver.mjs';
self.onmessage=e=>{try{self.postMessage({ok:true,result:screen(e.data)})}catch(error){self.postMessage({ok:false,error:error.message})}};
