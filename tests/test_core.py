import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from core import iou,inside_polygon,alert,detection_counts,rates

class CoreTests(unittest.TestCase):
    def test_iou_identity(self): self.assertEqual(iou([0,0,10,10],[0,0,10,10]),1)
    def test_iou_disjoint(self): self.assertEqual(iou([0,0,1,1],[2,2,3,3]),0)
    def test_iou_partial(self): self.assertAlmostEqual(iou([0,0,2,2],[1,1,3,3]),1/7)
    def test_polygon(self):
        p=[(0,0),(10,0),(10,10),(0,10)]
        for q in [(0,0),(5,5),(10,5)]: self.assertTrue(inside_polygon(q,p))
        self.assertFalse(inside_polygon((11,5),p))
    def test_concave_polygon(self):
        p=[(0,0),(4,0),(4,1),(1,1),(1,4),(0,4)]
        self.assertFalse(inside_polygon((3,3),p));self.assertTrue(inside_polygon((.5,3),p))
    def test_person_threshold_and_bottom_center(self):
        p=[(0,5),(10,5),(10,10),(0,10)]
        d={'class':0,'box':[1,0,3,6],'score':.5}
        self.assertTrue(alert([d],p,.5));self.assertFalse(alert([d],p,.6))
        self.assertFalse(alert([{**d,'class':2}],p,.25))
    def test_duplicate_detection(self):
        d={'class':0,'box':[0,0,10,10],'score':.9}
        self.assertEqual(detection_counts([d,d],[d]),(1,1,0))
    def test_wrong_class(self):
        d={'class':0,'box':[0,0,10,10],'score':.9}
        self.assertEqual(detection_counts([{**d,'class':2}],[d]),(0,1,1))
    def test_empty_detection(self): self.assertEqual(detection_counts([],[]),(0,0,0))
    def test_rates(self): self.assertEqual(rates(1,1,1)['f1'],.5)

if __name__=='__main__':unittest.main()
