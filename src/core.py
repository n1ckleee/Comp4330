"""Dependency-free geometry and operational precision/recall functions."""
import math

TARGET = (0,1,2,3,5,7)

def iou(a,b):
    x=max(0.,min(a[2],b[2])-max(a[0],b[0]));y=max(0.,min(a[3],b[3])-max(a[1],b[1]))
    inter=x*y; area=max(0.,a[2]-a[0])*max(0.,a[3]-a[1])+max(0.,b[2]-b[0])*max(0.,b[3]-b[1])-inter
    return inter/area if area else 0.

def inside_polygon(point, polygon):
    """Ray casting, with polygon boundary counted as inside."""
    if len(polygon)<3: raise ValueError('At least three polygon vertices required')
    x,y=point; inside=False
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        ax,ay=a;bx,by=b
        cross=(x-ax)*(by-ay)-(y-ay)*(bx-ax)
        if abs(cross)<1e-8 and min(ax,bx)-1e-8<=x<=max(ax,bx)+1e-8 and min(ay,by)-1e-8<=y<=max(ay,by)+1e-8: return True
        if (ay>y)!=(by>y) and x<(bx-ax)*(y-ay)/(by-ay)+ax: inside=not inside
    return inside

def alert(detections, polygon, threshold=.25):
    return any(int(d['class'])==0 and d['score']>=threshold and inside_polygon(((d['box'][0]+d['box'][2])/2,d['box'][3]),polygon) for d in detections)

def detection_counts(pred,gt,threshold=.25):
    used=set();tp=fp=0
    for d in sorted((p for p in pred if p['score']>=threshold),key=lambda p:p['score'],reverse=True):
        candidates=[(iou(d['box'],g['box']),i) for i,g in enumerate(gt) if i not in used and d['class']==g['class']]
        overlap,index=max(candidates,default=(0,-1))
        if overlap>=.5: tp+=1;used.add(index)
        else: fp+=1
    return tp,fp,len(gt)-len(used)

def rates(tp,fp,fn):
    p=tp/(tp+fp) if tp+fp else 0.;r=tp/(tp+fn) if tp+fn else 0.
    return {'tp':tp,'fp':fp,'fn':fn,'precision':p,'recall':r,'f1':2*p*r/(p+r) if p+r else 0.}
