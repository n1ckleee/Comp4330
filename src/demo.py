"""Public fixed-camera video demonstration and pre-prediction assistant-labelled ROI frames."""
from pathlib import Path
import argparse,json,time
import cv2,numpy as np,torch
from ultralytics import YOLO
from core import alert,rates,TARGET
ROOT=Path(__file__).resolve().parents[1]
POLY=[(.55,.42),(.97,.46),(.99,.76),(.64,.64)]
def poly(w,h):return [(x*w,y*h) for x,y in POLY]

def extract():
    v=cv2.VideoCapture(str(ROOT/'data/demo_source.avi'));n=int(v.get(cv2.CAP_PROP_FRAME_COUNT));out=ROOT/'build/roi_annotation';out.mkdir(exist_ok=True)
    frames=np.linspace(0,n-1,24,dtype=int).tolist()
    for idx in frames:
        v.set(cv2.CAP_PROP_POS_FRAMES,idx);ok,im=v.read()
        if not ok:raise RuntimeError(idx)
        h,w=im.shape[:2];cv2.polylines(im,[np.int32(poly(w,h))],True,(0,210,255),3)
        cv2.putText(im,f'FRAME {idx}',(18,32),cv2.FONT_HERSHEY_SIMPLEX,.8,(255,255,255),2)
        cv2.imwrite(str(out/f'{idx:04d}.jpg'),im)
    (out/'frames.json').write_text(json.dumps(frames));v.release()

def run():
    torch.set_num_threads(4)
    summary=json.loads((ROOT/'results/summary.json').read_text());selected=summary['environment']['selected_baseline']
    # Use the pretrained selected baseline for an independent public video.
    model=YOLO(str(ROOT/'weights'/f'{selected}.pt'))
    threshold=json.loads((ROOT/'results/thresholds.json').read_text())[selected]['chosen_threshold']
    labels=json.loads((ROOT/'configs/video_roi_labels.json').read_text())
    v=cv2.VideoCapture(str(ROOT/'data/demo_source.avi'));w=int(v.get(3));h=int(v.get(4));fps=v.get(5)
    polygon=poly(w,h);out=ROOT/'output';out.mkdir(exist_ok=True)
    writer=cv2.VideoWriter(str(out/'Campus_Traffic_Demo.mp4'),cv2.VideoWriter_fourcc(*'mp4v'),fps,(w,h))
    measurements={};evaluation=[];tp=fp=fn=tn=0;idx=0;frameset=set(map(int,labels['frames']))
    # Process 20 s for the presentation clip, plus all labelled evaluation frames.
    while True:
        ok,im=v.read()
        if not ok:break
        if idx<200 or idx in frameset:
            t=time.perf_counter();r=model.predict(im,imgsz=416,rect=False,conf=.001,classes=list(TARGET),device='cpu',verbose=False)[0]
            ds=[{'box':[float(x) for x in row[:4]],'score':float(row[4]),'class':int(row[5])} for row in r.boxes.data.cpu().numpy()]
            state=alert(ds,polygon,threshold)
            if idx in frameset:
                expected=labels['frames'][str(idx)];tp+=int(state and expected);fp+=int(state and not expected);fn+=int(not state and expected);tn+=int(not state and not expected)
                evaluation.append({'frame':idx,'expected':expected,'predicted':state})
            if idx<200:
                for d in ds:
                    if d['score']<threshold:continue
                    x1,y1,x2,y2=map(int,d['box']);cv2.rectangle(im,(x1,y1),(x2,y2),(80,230,80),2)
                    cv2.putText(im,f"{model.names[d['class']]} {d['score']:.2f}",(x1,max(18,y1-5)),cv2.FONT_HERSHEY_SIMPLEX,.45,(80,230,80),1)
                    if d['class']==0:cv2.circle(im,((x1+x2)//2,y2),4,(0,0,255),-1)
                cv2.polylines(im,[np.int32(polygon)],True,(0,210,255),3)
                cv2.rectangle(im,(0,0),(w,56),(24,30,39),-1)
                cv2.putText(im,'PERSON IN DEMO ZONE' if state else 'DEMO ZONE CLEAR',(16,23),cv2.FONT_HERSHEY_SIMPLEX,.65,(0,180,255) if state else (180,240,180),2)
                cv2.putText(im,'OpenCV public sample | illustrative zone | no collision prediction',(16,45),cv2.FONT_HERSHEY_SIMPLEX,.43,(235,235,235),1)
                writer.write(im)
                if idx in [0,80,150]:cv2.imwrite(str(ROOT/'results'/f'demo_{idx}.jpg'),im)
            measurements[idx]=(time.perf_counter()-t)*1000
        idx+=1
    writer.release();v.release()
    result={'source':'OpenCV samples/data/vtest.avi','model':selected,'threshold':threshold,'n_labelled_frames':len(evaluation),
        'roi_normalized':POLY,**rates(tp,fp,fn),'tn':tn,'accuracy':(tp+tn)/len(evaluation),'frames':evaluation,
        'note':'One public camera, illustrative zone, manual binary labels. Correlated frames; not independent safety incidents.'}
    (ROOT/'results/video_evaluation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('stage',choices=['extract','run']);a=p.parse_args();globals()[a.stage]()
