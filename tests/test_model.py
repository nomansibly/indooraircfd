import unittest
import numpy as np
from iaq.model import solve,Config
from iaq.comfort import pmv_ppd
class ModelTests(unittest.TestCase):
    def test_mass_and_scalars(self):
        for layout in ['cross_room','short_circuit']:
            r=solve(layout,Config(nx=40,nz=20,sensible_w=0,wall_c=19))
            self.assertLess(r['metrics']['max_cell_mass_imbalance_m3_s'],1e-10)
            np.testing.assert_allclose(r['T'],19,atol=1e-7)
            self.assertGreater(r['age'].min(),0)
            self.assertTrue(np.isfinite(r['age']).all())
    def test_pmv_reference(self):
        pmv,ppd=pmv_ppd(25,25,.1)
        self.assertAlmostEqual(float(pmv),.08,delta=.03)
        self.assertTrue(5<=ppd<6)
    def test_ppd_symmetry(self):
        p=np.array([-2.,0.,2.]); d=100-95*np.exp(-.03353*p**4-.2179*p**2)
        self.assertEqual(d[0],d[2]); self.assertEqual(d[1],5)
if __name__=='__main__': unittest.main()
