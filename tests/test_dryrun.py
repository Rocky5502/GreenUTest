import json,tempfile,unittest
from pathlib import Path
from greenutest.runner import run_toy
class DryRunTests(unittest.TestCase):
    def test_dryrun(self):
        with tempfile.TemporaryDirectory() as td:
            rows=[json.loads(x) for x in Path(run_toy(td)).read_text().splitlines() if x.strip()]
            self.assertEqual(len(rows),4); self.assertTrue(all(r["partition"]=="pilot" and r["metadata"]["synthetic"] for r in rows))
if __name__=='__main__': unittest.main()
