import unittest,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class DataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.m=json.loads((ROOT/'data/manifest.json').read_text())
    def test_disjoint_splits(self):
        s=[set(v) for v in self.m['splits'].values()]
        self.assertTrue(all(not s[i]&s[j] for i in range(3) for j in range(i)))
        self.assertEqual([len(v) for v in self.m['splits'].values()],[180,60,60])
    def test_unique_content(self):self.assertEqual(len({v['sha256'] for v in self.m['images'].values()}),300)
    def test_labels(self):
        for k in self.m['images']:
            for line in (ROOT/'data/labels'/f'{k}.txt').read_text().splitlines():
                c,x,y,w,h=map(float,line.split());self.assertIn(int(c),[0,1,2,3,5,7])
                self.assertTrue(0<=x<=1 and 0<=y<=1 and 0<w<=1 and 0<h<=1)
    def test_image_hashes(self):
        for k,v in self.m['images'].items():self.assertEqual(hashlib.sha256((ROOT/'data/images'/f'{k}.jpg').read_bytes()).hexdigest(),v['sha256'])
    def test_each_class_present(self):
        for d in self.m['instance_counts'].values():self.assertTrue(all(v>0 for v in d.values()))
if __name__=='__main__':unittest.main()
