"""Restore exact public images and regenerate machine-local paths."""
from pathlib import Path
import concurrent.futures as cf,hashlib,json,subprocess
import yaml
ROOT=Path(__file__).resolve().parents[1]
def fetch(item):
    k,record=item;p=ROOT/'data/images'/f'{k}.jpg';p.parent.mkdir(exist_ok=True)
    if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=record['sha256']:
        subprocess.run(['curl','-fLsS','--retry','2','--max-time','120',record['url'],'-o',str(p)],check=True)
    if hashlib.sha256(p.read_bytes()).hexdigest()!=record['sha256']:raise ValueError('Hash mismatch '+k)
    return k
def main():
    m=json.loads((ROOT/'data/manifest.json').read_text())
    with cf.ThreadPoolExecutor(max_workers=8) as pool:
        for i,_ in enumerate(pool.map(fetch,m['images'].items())):
            if (i+1)%25==0:print('Verified',i+1,flush=True)
    cfg=yaml.safe_load((ROOT/'configs/data.yaml').read_text());cfg['path']=str((ROOT/'data').resolve())
    (ROOT/'configs/data.yaml').write_text(yaml.safe_dump(cfg,sort_keys=False))
    for split,ids in m['splits'].items():(ROOT/'data'/f'{split}.txt').write_text(''.join('./images/'+k+'.jpg\n' for k in ids))
if __name__=='__main__':main()
