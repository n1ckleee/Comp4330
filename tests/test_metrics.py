import sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import experiment
class MetricTests(unittest.TestCase):
    def score(self,detections):
        with patch.object(experiment,'manifest',return_value={'images':{'x':{'width':100,'height':100}}}),patch.object(experiment,'ground_truth',return_value={'x':[{'class':0,'box':[10,10,30,40]}]}):
            return experiment.evaluate({'x':{'detections':detections}},['x'])
    def test_perfect_coco_ap(self):
        r=self.score([{'class':0,'box':[10,10,30,40],'score':.99}]);self.assertAlmostEqual(r['map50_95'],1);self.assertEqual(r['recall'],1)
    def test_empty_coco_ap(self):
        r=self.score([]);self.assertEqual(r['map50'],0);self.assertEqual(r['fn'],1)
    def test_wrong_class_coco_ap(self):
        r=self.score([{'class':2,'box':[10,10,30,40],'score':.99}]);self.assertEqual(r['map50'],0);self.assertEqual(r['fp'],1)
if __name__=='__main__':unittest.main()
