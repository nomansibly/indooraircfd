import json,shutil,subprocess,unittest
from pathlib import Path
import numpy as np
from iaq.model import Config,solve
from iaq.transient import Workday,run_workday
@unittest.skipUnless(shutil.which('node'),'Node required for browser/Python parity')
class BrowserParity(unittest.TestCase):
    def test_field_parity(self):
        root=Path(__file__).resolve().parents[1]
        for layout in ['cross_room','short_circuit']:
            opts={'nx':32,'nz':16,'layout':layout,'length':6,'height':3.5,'depth':4,'ach':5,'supply_c':21}
            code="import {screen} from './web/solver.mjs'; console.log(JSON.stringify(screen("+json.dumps(opts)+")));"
            web=json.loads(subprocess.check_output(['node','--input-type=module','-e',code],cwd=root,text=True))
            c=Config(nx=32,nz=16,length=6,height=3.5,depth=4,flow=5*6*3.5*4/3600,supply_c=21)
            py=solve(layout,c)
            np.testing.assert_allclose(web['T'],py['T'].ravel(),atol=1e-5)
            np.testing.assert_allclose(web['age'],py['age'].ravel(),atol=1e-3)
            self.assertLess(web['metrics']['max_mass_imbalance'],1e-8)
    def test_workday_parity(self):
        root=Path(__file__).resolve().parents[1]
        code="import {screen} from './web/solver.mjs'; const s=screen({transient:true});console.log(JSON.stringify(s.frames.at(-1)));"
        web=json.loads(subprocess.check_output(['node','--input-type=module','-e',code],cwd=root,text=True))
        py=run_workday(c=Config(nx=32,nz=16))
        np.testing.assert_allclose(web,py['frames'][-1].ravel(),atol=1e-5)
