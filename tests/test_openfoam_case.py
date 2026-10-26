import importlib.util,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('generate_case',Path(__file__).resolve().parents[1]/'openfoam/generate_case.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class CaseGeneration(unittest.TestCase):
    def test_transient_case_and_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=m.generate(tmp,transient=True,end=600,scale=.5)
            self.assertIn('buoyantBoussinesqPimpleFoam',(p/'system/controlDict').read_text())
            self.assertIn('kOmegaSST',(p/'constant/turbulenceProperties').read_text())
            self.assertIn('Prt 0.85',(p/'0/alphat').read_text())
            self.assertIn('PIMPLE',(p/'system/fvSolution').read_text())
            with self.assertRaises(FileExistsError):m.generate(tmp)
