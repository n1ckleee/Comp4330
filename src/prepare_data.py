"""Build a reproducible, class-balanced COCO val2017 proxy experiment.

This is a public-image pilot, not a campus dataset or an official COCO score.
The pretrained checkpoints use COCO; this is not external-domain validation.
"""
from pathlib import Path
import concurrent.futures as cf
import hashlib, json, random, subprocess, zipfile
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]
TARGET = [0, 1, 2, 3, 5, 7]
NAMES = ['person', 'bicycle', 'car', 'motorcycle', 'bus', 'truck']
SEED = 4330

def fetch(image_id):
    path = ROOT / 'data/images' / (image_id + '.jpg')
    if not path.exists():
        url = 'http://images.cocodataset.org/val2017/' + image_id + '.jpg'
        subprocess.run(['curl','-fLsS','--retry','2','--max-time','60',url,'-o',str(path)],check=True)
    from PIL import Image
    with Image.open(path) as im:
        im.verify()
    return image_id

def main():
    import yaml
    coco = yaml.safe_load((ROOT/'configs/coco_source.yaml').read_text())
    out=ROOT/'data'; (out/'images').mkdir(exist_ok=True); (out/'labels').mkdir(exist_ok=True)
    with zipfile.ZipFile(out/'coco2017labels.zip') as z:
        rows={}
        for name in z.namelist():
            if '/labels/val2017/' in name and name.endswith('.txt'):
                lines=[s for s in z.read(name).decode().splitlines() if s.strip()]
                selected=[s for s in lines if int(float(s.split()[0])) in TARGET]
                if selected: rows[Path(name).stem]=selected
    if not rows: raise RuntimeError('No validation labels in archive')
    rng=random.Random(SEED); assigned=set(); splits={'train':[], 'val':[], 'test':[]}
    # Assign rare classes first. Every stratum contributes 30/10/10 images.
    order=sorted(TARGET,key=lambda c:sum(any(int(float(s.split()[0]))==c for s in v) for v in rows.values()))
    for c in order:
        candidates=sorted(k for k,v in rows.items() if k not in assigned and any(int(float(s.split()[0]))==c for s in v))
        rng.shuffle(candidates); picked=candidates[:50]
        if len(picked)<50: raise RuntimeError('Insufficient unique images for class '+str(c))
        assigned.update(picked)
        for split,ids in [('train',picked[:30]),('val',picked[30:40]),('test',picked[40:])]: splits[split].extend(ids)
    manifest={'seed':SEED,'source':'COCO val2017','scope':'Public proxy pilot, not campus validation',
              'target_coco_indices':TARGET,'target_names':NAMES,'splits':splits,'images':{}}
    for ids in splits.values():
        for k in ids: (out/'labels'/f'{k}.txt').write_text('\n'.join(rows[k])+'\n')
    with cf.ThreadPoolExecutor(max_workers=10) as pool:
        for i,k in enumerate(pool.map(fetch,sorted(assigned))):
            if (i+1)%25==0: print('downloaded',i+1,'/',len(assigned),flush=True)
    from PIL import Image
    for split,ids in splits.items():
        (out/f'{split}.txt').write_text(''.join('./images/'+k+'.jpg\n' for k in ids))
        counts=Counter()
        for k in ids:
            p=out/'images'/f'{k}.jpg'
            with Image.open(p) as im: w,h=im.size
            counts.update(int(float(s.split()[0])) for s in rows[k])
            manifest['images'][k]={'split':split,'width':w,'height':h,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
                'url':f'http://images.cocodataset.org/val2017/{k}.jpg','label_count':len(rows[k])}
        manifest.setdefault('instance_counts',{})[split]={coco['names'][c]:counts[c] for c in TARGET}
    # Retain original 80-class indexing and output head. Only target annotations
    # and predictions participate; this avoids a silent six-class index mismatch.
    cfg={'path':str(out.resolve()),'train':'train.txt','val':'val.txt','test':'test.txt','names':coco['names']}
    (ROOT/'configs/data.yaml').write_text(yaml.safe_dump(cfg,sort_keys=False))
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest['instance_counts'],indent=2),flush=True)

if __name__=='__main__': main()
