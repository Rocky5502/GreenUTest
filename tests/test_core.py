import unittest
from greenutest.harness import *
from greenutest.metrics import brier_score, expected_calibration_error

class CoreTests(unittest.TestCase):
    def test_energy(self): self.assertAlmostEqual(integrate_joules([PowerSample(0,100),PowerSample(1,100),PowerSample(2,100)]),200)
    def test_metrics(self): self.assertEqual(brier_score([0.,1.],[0,1]),0.); self.assertAlmostEqual(expected_calibration_error([0.,1.],[0,1],2),0.)
    def test_policy(self):
        p=GreenUTestPolicy(); self.assertEqual(p.decide(DecisionState(.1,10,.5)),Action.ACCEPT); self.assertEqual(p.decide(DecisionState(.8,10,.5)),Action.ESCALATE)
    def test_voi(self): self.assertTrue(value_of_information(.8,.5,10,.01).acquire); self.assertFalse(value_of_information(.6,.5,20,.01).acquire)
if __name__=='__main__': unittest.main()
