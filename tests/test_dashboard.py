import unittest
from pathlib import Path
try:
    from streamlit.testing.v1 import AppTest
except ImportError:
    AppTest=None
@unittest.skipIf(AppTest is None,'Optional dashboard dependencies not installed')
class DashboardTests(unittest.TestCase):
    def test_parameter_updates_and_transient(self):
        at=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'streamlit_app.py'),default_timeout=45).run()
        self.assertEqual(len(at.exception),0)
        old=at.metric[0].value
        next(s for s in at.sidebar.slider if s.label=='Supply temperature (°C)').set_value(23.).run()
        self.assertEqual(len(at.exception),0)
        self.assertNotEqual(old,at.metric[0].value)
        at.sidebar.radio[0].set_value('8-hour workday').run()
        self.assertEqual(len(at.exception),0)
        self.assertTrue(any(s.label=='Workday hour' for s in at.slider))
