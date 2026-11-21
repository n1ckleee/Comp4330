"""CPU-compatible baseline, fine-tuning and held-out evaluation pipeline."""
import os
os.environ.setdefault('YOLO_AUTOINSTALL','false')
os.environ.setdefault('OMP_NUM_THREADS','4')
from pathlib import Path
import argparse,contextlib,io,json,time,platform,hashlib
import numpy as np
import cv2,torch,ultralytics
from ultralytics import YOLO
from pycocotools.coco import COCO
from pycocotools.cocoeval import COCOeval
from core import TARGET,alert,detection_counts,rates
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results';OUT.mkdir(exist_ok=True)
IMGSZ=416
torch.set_num_threads(4)

def manifest(): return json.loads((ROOT/'data/manifest.json').read_text())
def ground_truth(ids):
    meta=manifest();result={}
    for k in ids:
        w,h=meta['images'][k]['width'],meta['images'][k]['height'];result[k]=[]
        for line in (ROOT/'data/labels'/f'{k}.txt').read_text().splitlines():
            c,x,y,bw,bh=map(float,line.split());x*=w;y*=h;bw*=w;bh*=h
            result[k].append({'class':int(c),'box':[x-bw/2,y-bh/2,x+bw/2,y+bh/2]})
    return result

def evaluate(pred,ids,threshold=.25):
    gt=ground_truth(ids);meta=manifest();images=[];annotations=[];detections=[]
    tp=fp=fn=0;rtp=rfp=rfn=tn=0
    for i,k in enumerate(ids):
        w,h=meta['images'][k]['width'],meta['images'][k]['height'];images.append({'id':i,'width':w,'height':h})
        for g in gt[k]:
            x1,y1,x2,y2=g['box'];annotations.append({'id':len(annotations)+1,'image_id':i,'category_id':g['class'],'bbox':[x1,y1,x2-x1,y2-y1],'area':(x2-x1)*(y2-y1),'iscrowd':0})
        for d in pred[k]['detections']:
            x1,y1,x2,y2=d['box'];detections.append({'image_id':i,'category_id':d['class'],'bbox':[x1,y1,x2-x1,y2-y1],'score':d['score']})
        a,b,c=detection_counts(pred[k]['detections'],gt[k],threshold);tp+=a;fp+=b;fn+=c
        # Generic lower-image ROI for a geometry proxy, not a verified vehicle zone.
        roi=[(.25*w,.5*h),(.75*w,.5*h),(w,h),(0,h)]
        expected=alert([{**g,'score':1.} for g in gt[k]],roi)
        observed=alert(pred[k]['detections'],roi,threshold)
        rtp+=int(expected and observed);rfp+=int(not expected and observed)
        rfn+=int(expected and not observed);tn+=int(not expected and not observed)
    with contextlib.redirect_stdout(io.StringIO()):
        coco=COCO();coco.dataset={'info':{},'images':images,'annotations':annotations,'categories':[{'id':c,'name':str(c)} for c in TARGET]};coco.createIndex()
        if detections:
            dt=coco.loadRes(detections);e=COCOeval(coco,dt,'bbox');e.params.catIds=list(TARGET);e.evaluate();e.accumulate();e.summarize()
            ap50=float(e.stats[1]);ap=float(e.stats[0]);class_ap={}
            for j,c in enumerate(TARGET):
                v=e.eval['precision'][:,:,j,0,-1];class_ap[str(c)]=float(v[v>=0].mean()) if np.any(v>=0) else None
        else:ap50=ap=0.;class_ap={str(c):0. for c in TARGET}
    return {'n_images':len(ids),'n_instances':len(annotations),'threshold':threshold,'map50':ap50,'map50_95':ap,
            **rates(tp,fp,fn),'class_ap':class_ap,'roi_proxy':{**rates(rtp,rfp,rfn),'tn':tn}}

def predict(weight,ids,tag,condition='original'):
    cache=OUT/f'predictions_{tag}_{condition}.json'
    if cache.exists():return json.loads(cache.read_text())
    model=YOLO(str(weight));model.fuse()
    model.predict(np.zeros((IMGSZ,IMGSZ,3),dtype=np.uint8),imgsz=IMGSZ,device='cpu',verbose=False)
    output={}
    for j,k in enumerate(ids):
        im=cv2.imread(str(ROOT/'data/images'/f'{k}.jpg'))
        if im is None: raise RuntimeError('Cannot decode '+k)
        if condition=='dark': im=np.clip(im.astype(np.float32)*.35,0,255).astype(np.uint8)
        elif condition=='blur': im=cv2.GaussianBlur(im,(9,9),3)
        start=time.perf_counter()
        r=model.predict(im,imgsz=IMGSZ,rect=False,device='cpu',conf=.001,iou=.7,max_det=300,classes=list(TARGET),verbose=False)[0]
        elapsed=(time.perf_counter()-start)*1000
        output[k]={'detections':[{'box':[float(v) for v in row[:4]],'score':float(row[4]),'class':int(row[5])} for row in r.boxes.data.cpu().numpy()],
                   'wall_ms':elapsed,'speed':r.speed}
        if (j+1)%20==0:print(tag,condition,j+1,'/',len(ids),flush=True)
    cache.write_text(json.dumps(output))
    return output

def speed_summary(pred,ids):
    return {'mean_inference_ms':float(np.mean([pred[k]['speed']['inference'] for k in ids])),
            'mean_pipeline_ms':float(np.mean([pred[k]['wall_ms'] for k in ids])),
            'pipeline_fps':1000/float(np.mean([pred[k]['wall_ms'] for k in ids]))}

def validation():
    ids=manifest()['splits']['val'];summary={}
    for name in ['yolov8n','yolov8s']:
        pred=predict(ROOT/'weights'/f'{name}.pt',ids,name+'_val')
        summary[name]={**evaluate(pred,ids),**speed_summary(pred,ids)}
    # Select by validation AP with an explicit speed trade-off, using a fixed rule.
    # Fine-tune n unless s delivers >0.05 AP gain with <=2x pipeline latency.
    n,s=summary['yolov8n'],summary['yolov8s']
    chosen='yolov8s' if s['map50_95']-n['map50_95']>.05 and s['mean_pipeline_ms']<=2*n['mean_pipeline_ms'] else 'yolov8n'
    (OUT/'validation.json').write_text(json.dumps({'models':summary,'selected':chosen,'selection_rule':'s only if validation AP gain > 0.05 and latency <= 2x n, otherwise n'},indent=2))
    print('SELECTED',chosen,flush=True)

def train():
    chosen=json.loads((OUT/'validation.json').read_text())['selected']
    model=YOLO(str(ROOT/'weights'/f'{chosen}.pt'))
    start=time.perf_counter()
    model.train(data=str(ROOT/'configs/data.yaml'),epochs=10,patience=4,imgsz=IMGSZ,batch=8,device='cpu',workers=0,
        seed=4330,deterministic=True,freeze=10,optimizer='SGD',lr0=.001,lrf=.1,momentum=.9,weight_decay=.0005,
        warmup_epochs=1,hsv_h=.015,hsv_s=.5,hsv_v=.6,scale=.25,translate=.1,fliplr=.5,mosaic=.5,close_mosaic=2,
        mixup=0,copy_paste=0,amp=False,cache=False,plots=True,classes=list(TARGET),
        project=str(OUT/'training'),name='finetuned',exist_ok=True,verbose=False)
    (OUT/'training_elapsed.json').write_text(json.dumps({'seconds':time.perf_counter()-start,'base_model':chosen}))

def final():
    meta=manifest();vids=meta['splits']['val'];tids=meta['splits']['test']
    selected=json.loads((OUT/'validation.json').read_text())['selected']
    fw=OUT/'training/finetuned/weights/best.pt'
    models={'yolov8n':ROOT/'weights/yolov8n.pt','yolov8s':ROOT/'weights/yolov8s.pt','finetuned':fw}
    tuned={};allresults={}
    for name,weight in models.items():
        pred=predict(weight,vids,name+'_val')
        sweep=[evaluate(pred,vids,t) for t in [.1,.2,.25,.3,.4,.5,.6,.7]]
        # Tune operating threshold to maximize detection F1, not test results.
        best=max(sweep,key=lambda x:(x['f1'],-x['threshold']))
        tuned[name]={'chosen_threshold':best['threshold'],'validation_sweep':sweep}
    (OUT/'thresholds.json').write_text(json.dumps(tuned,indent=2))
    for name,weight in models.items():
        allresults[name]={}
        for condition in ['original','dark','blur']:
            pred=predict(weight,tids,name+'_test',condition)
            allresults[name][condition]={**evaluate(pred,tids),**speed_summary(pred,tids)}
            if condition=='original': allresults[name]['tuned']=evaluate(pred,tids,tuned[name]['chosen_threshold'])
    env={'python':platform.python_version(),'torch':torch.__version__,'ultralytics':ultralytics.__version__,'opencv':cv2.__version__,
         'device':'CPU','threads':torch.get_num_threads(),'imgsz':IMGSZ,'batch':1,'precision':'FP32','seed':4330,'selected_baseline':selected,
         'cpu_model':(next((l.split(':',1)[1].strip() for l in Path('/proc/cpuinfo').read_text().splitlines() if l.startswith('model name')),'unknown') if Path('/proc/cpuinfo').exists() else platform.processor())}
    (OUT/'summary.json').write_text(json.dumps({'environment':env,'results':allresults},indent=2))
    print(json.dumps({'environment':env,'results':allresults},indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['validation','train','final']);args=p.parse_args()
    globals()[args.stage]()
