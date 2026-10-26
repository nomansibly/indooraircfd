import unittest
import numpy as np
from iaq.model import Config,solve
from iaq.transient import Workday,run_workday,boundary_schedule
class TransientTests(unittest.TestCase):
    def test_uniform_preservation(self):
        c=Config(nx=24,nz=12,supply_c=19,wall_c=19)
        r=run_workday(c=c,day=Workday(hours=.2,initial_c=19,equipment_w=0,watts_per_person=0,solar_peak_w=0,supply_swing_c=0))
        np.testing.assert_allclose(r['frames'],19,atol=1e-9)
        self.assertLess(r['max_energy_balance_error_w'],1e-7)
    def test_heating_and_timestep(self):
        c=Config(nx=24,nz=12)
        coarse=run_workday(c=c,day=Workday(hours=1,dt_s=120))
        fine=run_workday(c=c,day=Workday(hours=1,dt_s=60))
        self.assertGreater(coarse['frames'][-1].mean(),coarse['frames'][0].mean())
        self.assertLess(abs(coarse['frames'][-1].mean()-fine['frames'][-1].mean()),.04)
        self.assertLess(coarse['max_energy_balance_error_w'],1e-7)
    def test_solar_and_occupancy(self):
        c=Config(); day=Workday()
        noon=boundary_schedule(4,c,day)
        self.assertAlmostEqual(noon['solar_w'],900)
        self.assertEqual(noon['people'],0)
        self.assertEqual(boundary_schedule(1,c,day)['people'],8)
    def test_resize(self):
        for h in [2.5,4.5]:
            r=solve(c=Config(nx=24,nz=16,height=h))
            self.assertLess(r['metrics']['max_cell_mass_imbalance_m3_s'],1e-9)
    def test_invalid(self):
        with self.assertRaises(ValueError): solve(c=Config(flow=0))
