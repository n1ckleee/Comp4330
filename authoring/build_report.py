from pathlib import Path
import json,re
from docx import Document
from docx.shared import Cm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
ROOT=Path(__file__).resolve().parents[1]
S=json.loads((ROOT/'results/summary.json').read_text());R=S['results'];E=S['environment'];V=json.loads((ROOT/'results/video_evaluation.json').read_text());M=json.loads((ROOT/'data/manifest.json').read_text())
T=json.loads((ROOT/'results/thresholds.json').read_text());B=R[E['selected_baseline']]['original'];F=R['finetuned']['original'];N=R['yolov8n']['original'];Y=R['yolov8s']['original']
f=lambda x:f'{x:.3f}'
d=Document();sec=d.sections[0];sec.page_height=Cm(29.7);sec.page_width=Cm(21);sec.top_margin=Cm(2);sec.bottom_margin=Cm(2);sec.left_margin=Cm(2.1);sec.right_margin=Cm(2.1)
for st in ['Normal','Title','Subtitle','Heading 1','Heading 2']:
 s=d.styles[st];s.font.name='Arial';s.font.color.rgb=RGBColor(0,0,0)
d.styles['Normal'].font.size=Pt(10.5);d.styles['Normal'].paragraph_format.line_spacing=1.1;d.styles['Normal'].paragraph_format.space_after=Pt(6)
d.styles['Title'].font.size=Pt(21);d.styles['Title'].font.bold=True;d.styles['Title'].paragraph_format.space_after=Pt(10)
d.styles['Heading 1'].font.size=Pt(13);d.styles['Heading 1'].paragraph_format.space_before=Pt(10);d.styles['Heading 1'].paragraph_format.space_after=Pt(5)
d.styles['Heading 2'].font.size=Pt(11);d.styles['Heading 2'].font.bold=True
d.core_properties.author='P01 Group 9';d.core_properties.title='Evaluation and Improvement of YOLO Based Campus Traffic and Safety Detection';d.core_properties.subject='COMP 4330SEF public-data pilot';d.core_properties.comments=''
body=[]
def p(t):body.append(t);return d.add_paragraph(t)
def heading(t):d.add_heading(t,1)
def table(rows,widths):
 t=d.add_table(rows=1,cols=len(rows[0]));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
 for j,w in enumerate(widths):t.columns[j].width=Cm(w)
 for i,row in enumerate(rows):
  cells=t.rows[0].cells if i==0 else t.add_row().cells
  for j,(cell,value) in enumerate(zip(cells,row)):
   cell.width=Cm(widths[j]);cell.text=str(value);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
   tcpr=cell._tc.get_or_add_tcPr();shade=OxmlElement('w:shd');shade.set(qn('w:fill'),'173A54' if i==0 else ('F0F4F7' if i%2==0 else 'FFFFFF'));tcpr.append(shade)
   borders=OxmlElement('w:tcBorders')
   for edge in ['top','left','bottom','right']:
    e=OxmlElement('w:'+edge);e.set(qn('w:val'),'single');e.set(qn('w:sz'),'4');e.set(qn('w:color'),'D9D9D9');borders.append(e)
   tcpr.append(borders);marg=OxmlElement('w:tcMar')
   for edge in ['top','left','bottom','right']:
    e=OxmlElement('w:'+edge);e.set(qn('w:w'),'85');e.set(qn('w:type'),'dxa');marg.append(e)
   tcpr.append(marg)
   for q in cell.paragraphs:
    q.paragraph_format.keep_with_next=i<len(rows)-1;q.paragraph_format.space_after=Pt(2);q.paragraph_format.space_before=Pt(2);q.alignment=WD_ALIGN_PARAGRAPH.LEFT if j==0 else WD_ALIGN_PARAGRAPH.CENTER
    for run in q.runs:run.font.size=Pt(9);run.font.bold=i==0;run.font.color.rgb=RGBColor(255,255,255) if i==0 else RGBColor(0,0,0)
  trpr=t.rows[i]._tr.get_or_add_trPr();cant=OxmlElement('w:cantSplit');trpr.append(cant)
  if i==0:repeat=OxmlElement('w:tblHeader');trpr.append(repeat)
 d.add_paragraph().paragraph_format.space_after=Pt(0)
 return t

d.add_paragraph('Evaluation and Improvement of YOLO Based Campus Traffic and Safety Detection',style='Title')
d.add_paragraph('COMP 4330SEF Advanced Programming and AI Algorithms\nP01 Group 9',style='Subtitle')
d.add_paragraph('LI DAOBO 13407753; GAO SHUN 13408577; LI RUNZE 13420474;\nLI CHENYUAN 13365825; WANG JIALE 13253888')
heading('Abstract')
abstract=f'''This project evaluates an open-source YOLO detector for campus-oriented traffic monitoring using public proxy data. A reproducible sample of 300 COCO images covers six road-user classes, with 180 training, 60 validation and 60 test images. Pretrained YOLOv8n and YOLOv8s are compared under fixed CPU inference settings. Controlled darkening and blur test sensitivity to image degradation. YOLOv8s achieves test mAP50-95 of {f(Y['map50_95'])}, compared with {f(N['map50_95'])} for YOLOv8n, at lower processing speed. Small-sample fine-tuning produces {f(F['map50_95'])}, providing no AP improvement in this run. A polygon-based person-entry rule matches all 24 visually labelled frames from one public video. These limited observations support a working prototype, while campus-specific data, independent annotation review and broader environmental testing remain necessary before deployment.'''
p(abstract)
heading('1 Introduction')
p('Campus entrances and shared road spaces contain pedestrians and vehicles with different movement patterns. A detector can help highlight objects in a camera view, but detection alone does not establish whether a situation is dangerous. This project studies a limited monitoring function: detecting common road users and flagging a person whose estimated ground-contact point enters a predefined image region.')
p('The implementation uses Ultralytics YOLOv8 and evaluates person, bicycle, car, motorcycle, bus and truck detections. Three questions guide the work: how model size changes accuracy and speed, how image degradation affects detection, and whether a small adaptation experiment improves the baseline. All numerical findings below come from executed experiments. The current scope uses public images and video rather than recordings from HKMU.')
heading('2 Literature Review')
p('YOLO introduced a unified, one-stage approach to object detection [1]. Ultralytics supplies pretrained YOLOv8 models and interfaces for prediction, training and validation [2]. These tools make a reproducible model-size comparison feasible without implementing the network from scratch. YOLOv8n is smaller than YOLOv8s, but the practical accuracy and latency difference depends on the input and execution environment.')
p('COCO provides annotated everyday objects, including the six classes used here [3]. Its diverse scenes support a public-data pilot, although its images do not represent the distribution of a particular campus camera. The original YOLO paper explains the detection family rather than the exact YOLOv8 architecture. The implementation therefore uses the Ultralytics documentation and source for version-specific behaviour. OpenCV supports video decoding, display and the fixed-camera demonstration [4].')
heading('3 Methodology')
d.add_heading('3.1 Data and evaluation protocol',2)
p('A fixed seed of 4330 selects 300 unique images from COCO val2017. Selection processes rarer target classes first and assigns 50 previously unselected images to each class stratum. Each stratum contributes 30 training, 10 validation and 10 test images. Images may contain several target classes, so object counts are not balanced. The resulting sets contain 180, 60 and 60 images. File hashes and image IDs are distinct across sets. The manifest records every source URL, hash and split.')
p('Labels come from the Ultralytics COCO bounding-box archive. Only the six target categories remain, using their original COCO indices 0, 1, 2, 3, 5 and 7. The network retains its 80-output head. The test set contains 546 annotated target objects. Converted labels do not preserve original crowd and ignore metadata; the reported values are custom-subset scores, not official COCO benchmark results. As the pretrained models already use COCO, this experiment also does not establish independent-domain generalization.')
d.add_heading('3.2 Models and measurements',2)
p(f"Both pretrained models use 416 by 416 square input, FP32 and CPU inference with batch size one. The environment uses {E['cpu_model']}, PyTorch {E['torch']} and Ultralytics {E['ultralytics']}. The inference backend reports {E['threads']} CPU threads. Prediction uses confidence floor 0.001, NMS IoU 0.7 and a maximum of 300 detections. pycocotools calculates six-class mAP50 and mAP50-95 with a maximum of 100 detections per class per image. Operational precision and recall use confidence 0.25 and greedy, same-class, one-to-one IoU matching at 0.5.")
p('Timing follows a warm-up prediction and measures in-memory prediction calls. It includes preprocessing, inference and postprocessing, but excludes image loading, drawing and video encoding. FPS equals 1,000 divided by mean call time in milliseconds. These are single-pass measurements on a shared CPU environment, not a claim of complete real-time system performance.')
d.add_heading('3.3 Adaptation and stress tests',2)
p('A rule fixed before test evaluation selects YOLOv8s only if validation mAP50-95 exceeds YOLOv8n by more than 0.05 and call latency remains within twice that of YOLOv8n. Validation scores of 0.444 versus 0.365 and latency of 70.0 versus 41.7 ms satisfy that rule. YOLOv8s is then fine-tuned on 180 images. The first ten model modules are frozen. Training uses SGD, initial learning rate 0.001, batch size eight, brightness and geometric augmentation, and a ten-epoch maximum. Early stopping with patience four ends training after five epochs and retains the first epoch checkpoint. This tests a combined adaptation package, without an augmentation ablation.')
p('Confidence thresholds from 0.10 to 0.70 are compared on validation detection F1, with ties favouring the lower threshold. The selected values are 0.25 for YOLOv8n and 0.30 for both YOLOv8s and the adapted model. The test set remains excluded from selection. Separate paired stress tests multiply image intensities by 0.35 or apply Gaussian blur with a 9 by 9 kernel and sigma three. These transformations preserve labels but do not substitute for real night-time or natural occlusion annotations.')
d.add_heading('3.4 Region rule and software checks',2)
p('For each detected person, the bottom-centre of its bounding box approximates the ground-contact point. A point-in-polygon test, with the boundary included, generates a visual alert. The demonstration uses a single fixed polygon on OpenCV vtest.avi. Before inspecting detector predictions, a single assistant visual review labels 24 evenly spaced frames as occupied or clear. The group should independently verify these labels, especially boundary cases. This video provides a separate qualitative scene but is not campus deployment evidence. Eighteen automated checks cover geometry, duplicate matching, known-answer AP cases, label validity and split integrity.')
heading('4 Results and Discussion')
d.add_heading('4.1 Baseline accuracy and speed',2)
table([['Model','Precision','Recall','mAP50','mAP50-95','Call FPS'],['YOLOv8n',f(N['precision']),f(N['recall']),f(N['map50']),f(N['map50_95']),f'{N["pipeline_fps"]:.1f}'],['YOLOv8s',f(Y['precision']),f(Y['recall']),f(Y['map50']),f(Y['map50_95']),f'{Y["pipeline_fps"]:.1f}'],['Fine-tuned v8s',f(F['precision']),f(F['recall']),f(F['map50']),f(F['map50_95']),f'{F["pipeline_fps"]:.1f}']],[4.0,2.4,2.0,2.4,2.8,3.2])
p(f"YOLOv8s increases mAP50-95 by {(Y['map50_95']-N['map50_95'])*100:.1f} percentage points relative to YOLOv8n. Recall rises from {f(N['recall'])} to {f(Y['recall'])}, while precision at confidence 0.25 is similar. This improved coverage costs speed: measured prediction throughput falls from {N['pipeline_fps']:.1f} to {Y['pipeline_fps']:.1f} FPS. The choice therefore depends on whether a deployment prioritizes coverage or processing capacity.")
d.add_heading('4.2 Degradation and adaptation',2)
table([['Model','Original AP','Darkened AP','Blurred AP'],*[[name,f(R[key]['original']['map50_95']),f(R[key]['dark']['map50_95']),f(R[key]['blur']['map50_95'])] for key,name in [('yolov8n','YOLOv8n'),('yolov8s','YOLOv8s'),('finetuned','Fine-tuned v8s')]]],[5.2,3.7,3.9,4.0])
p(f"Both transformations reduce AP for both pretrained models. Blur produces the larger decline in this sample. Fine-tuning changes original-image AP from {f(Y['map50_95'])} to {f(F['map50_95'])}, a decrease of {(Y['map50_95']-F['map50_95'])*100:.2f} percentage points. At confidence 0.25, recall increases but precision decreases. The experiment therefore does not demonstrate an AP benefit from the combined adaptation. A small dataset, limited optimization and existing COCO pretraining may contribute, but the experiment cannot identify a single cause.")
p(f"Validation-selected confidence 0.30 changes YOLOv8s test precision from {f(Y['precision'])} to {f(R['yolov8s']['tuned']['precision'])} and recall from {f(Y['recall'])} to {f(R['yolov8s']['tuned']['recall'])}. The higher precision comes with missed detections. Threshold selection changes the operating point, not the AP protocol. One seed and 60 test images do not establish statistical significance for the small adaptation difference. Threshold selection optimizes detection F1. Its effect on zone false alerts has not been established; a controlled comparison across thresholds remains future work.")
d.add_heading('4.3 Video alerts and limitations',2)
p(f"At confidence 0.30, pretrained YOLOv8s matches all 24 video-frame labels: {V['tp']} occupied frames and {V['tn']} clear frames, with {V['fp']} false positives and {V['fn']} false negatives. This is a narrow rule check on correlated frames from one camera, not 24 independent safety events. Single-review annotations and the small number of clear frames limit the finding. The system does not infer pedestrian intent, vehicle speed or collision probability.")
d.add_paragraph().add_run().add_picture(str(ROOT/'results/demo_80.jpg'),width=Cm(12.6))
q=d.add_paragraph('Figure 1. Detection and an illustrative road-zone alert on the public OpenCV sample. Source: [4].');q.paragraph_format.keep_with_next=False
for run in q.runs:run.font.size=Pt(9)
heading('5 Conclusion')
p('The implemented pipeline compares two YOLOv8 models, executes a controlled adaptation experiment and demonstrates a person-entry rule. YOLOv8s achieves higher detection AP at lower CPU throughput. This small fine-tuning run does not improve AP, and artificial degradation exposes sensitivity. The next evaluation should use permitted campus recordings, scene-level splits, independently reviewed annotations and separate real low-light, occlusion and object-distance subsets. Qualitative missed-detection and false-positive case analysis also remains future work. A controlled threshold comparison should measure zone false positives and false negatives directly. Repeated training seeds and sustained-event alert logic would strengthen reliability. Current evidence supports a reproducible prototype rather than a deployed safety system.')
heading('References')
refs=['[1] J. Redmon, S. Divvala, R. Girshick and A. Farhadi, “You Only Look Once: Unified, Real-Time Object Detection,” CVPR, pp. 779–788, 2016. https://arxiv.org/abs/1506.02640',
'[2] Ultralytics, “YOLOv8” and training, prediction and validation documentation. https://docs.ultralytics.com/models/yolov8/ and https://docs.ultralytics.com/modes/train/ (accessed 12 November 2026). Runtime version 8.3.228.',
'[3] T.-Y. Lin et al., “Microsoft COCO: Common Objects in Context,” ECCV, pp. 740–755, 2014. https://arxiv.org/abs/1405.0312. Label archive: https://github.com/ultralytics/assets/releases/download/v0.0.0/coco2017labels.zip. Images: http://images.cocodataset.org/val2017/ (exact IDs in manifest).',
'[4] OpenCV, public sample video vtest.avi. https://github.com/opencv/opencv/blob/4.x/samples/data/vtest.avi (accessed 12 November 2026).']
for t in refs:d.add_paragraph(t)
d.add_page_break()
heading('Appendix A Work allocation')
d.add_paragraph('The following responsibilities reproduce the submitted proposal. They are assigned roles; each member should confirm their actual contribution before final submission.')
table([['Member','Student ID','Assigned responsibility'],['LI DAOBO','13407753','Leadership and integration'],['GAO SHUN','13408577','Data and ethics'],['LI RUNZE','13420474','Baseline models'],['LI CHENYUAN','13365825','Evaluation and presentation'],['WANG JIALE','13253888','Improvement and demonstration']],[4.2,3.2,9.4])
heading('Appendix B Reproduction evidence')
d.add_paragraph('The accompanying code package includes the exact data manifest and selected labels, experiment scripts, original and fine-tuned weights, raw prediction files, training logs, threshold sweeps, 18 test results and video-frame annotations. restore_data.py downloads the exact public images and verifies their hashes. Predictions cached from this run must be cleared before testing modified models or settings. The implementation and visual annotations were prepared with AI assistance. Individual contributions have not yet been verified.')
words=len(re.findall(r"\b[\w'-]+\b",' '.join(body)));aw=len(abstract.split());print('BODY_WORDS',words,'ABSTRACT_WORDS',aw)
assert words<=2000;assert 100<=aw<=150
d.save(ROOT/'output/COMP4330_P01_Group9_Report.docx')
(ROOT/'build/report_word_count.json').write_text(json.dumps({'body_words':words,'abstract_words':aw}))
