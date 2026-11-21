import fs from 'node:fs/promises';
import path from 'node:path';
import {readFileSync} from 'node:fs';
import {Presentation,PresentationFile} from '@oai/artifact-tool';
import {finalizePresentation} from '/home/agent/.codex/skills/builtins/presentations/container_tools/artifact_tool_utils.mjs';
const root=path.resolve('comp4330');
const read=async p=>JSON.parse(await fs.readFile(path.join(root,p),'utf8'));
const summary=await read('results/summary.json'),m=await read('data/manifest.json'),video=await read('results/video_evaluation.json'),thresholds=await read('results/thresholds.json');
const r=summary.results,env=summary.environment,chosen=env.selected_baseline;
const p=Presentation.create({slideSize:{width:1280,height:720}});
const C={navy:'#102C46',teal:'#147D92',orange:'#DE8B35',ink:'#172C3C',gray:'#546776',light:'#EDF3F6',white:'#FFFFFF'};
const FONT='Arial';let index=0;
const pct=x=>(100*x).toFixed(1)+'%';const f=x=>x.toFixed(3);
function text(s,name,value,x,y,w,h,size=26,bold=false,color=C.ink){const a=s.shapes.add({name,geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});a.text=value;a.text.style={typeface:FONT,fontSize:size,bold,color,wrap:'square',autoFit:'none',verticalAlignment:'top',insets:0};return a;}
function slide(title,notes,appendix=false){const s=p.slides.add();index++;s.background.fill=C.white;text(s,'title',title,64,46,1152,78,43,true,C.navy);text(s,'page',appendix?'Appendix  '+(index-8):String(index).padStart(2,'0'),1120,676,96,24,16,false,C.gray);s.speakerNotes.text=notes;s.hidden=appendix;return s;}
function table(s,values,x,y,widths,rowh=65,size=24){const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:widths.reduce((a,b)=>a+b,0),height:rowh*values.length,columnWidths:widths,values});t.borders.assign({fill:'#CEDBE3',width:1,style:'solid'});for(let i=0;i<values.length;i++)for(let j=0;j<values[0].length;j++){const c=t.getCell(i,j);c.fill=i===0?C.navy:(i%2?C.white:C.light);c.text.style={typeface:FONT,fontSize:size,color:i===0?C.white:C.ink,bold:i===0,alignment:j===0?'left':'center',verticalAlignment:'middle',insets:12};}return t;}
function image(s,name,file,x,y,w,h){s.images.add({blob:readFileSync(path.join(root,file)),contentType:'image/jpeg',alt:name,fit:'contain',position:{left:x,top:y,width:w,height:h}});}
function chart(s,title,categories,series,x=64,y=180,w=760,h=390){return s.charts.add('bar',{position:{left:x,top:y,width:w,height:h},title,titleTextStyle:{typeface:FONT,fontSize:22,bold:true},categories,series:series.map(v=>({...v,values:v.values.map(x=>Number(x.toFixed(6)))})),barOptions:{direction:'column',grouping:'clustered',gapWidth:100},hasLegend:series.length>1,legend:{position:'bottom',textStyle:{typeface:FONT,fontSize:20}},xAxis:{textStyle:{typeface:FONT,fontSize:20}},yAxis:{min:0,max:1,numberFormatCode:'0.0',textStyle:{typeface:FONT,fontSize:18},majorGridlines:{style:'solid',fill:'#DCE5EB',width:1}},dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0.000',textStyle:{typeface:FONT,fontSize:18}},chartLine:{style:'solid',fill:'none',width:0}});}
const urls={yolo:'https://docs.ultralytics.com/models/yolov8/',coco:'https://docs.ultralytics.com/datasets/detect/coco/',video:'https://github.com/opencv/opencv/blob/4.x/samples/data/vtest.avi',paper:'https://arxiv.org/abs/1506.02640',cocopaper:'https://arxiv.org/abs/1405.0312'};

{
const s=p.slides.add();index++;s.background.fill=C.navy;
text(s,'course','COMP 4330SEF     P01 Group 9',64,54,590,35,23,false,'#D1DFEA');
text(s,'cover-title','YOLO for campus\ntraffic monitoring',64,158,600,190,59,true,C.white);
text(s,'subtitle','Evaluation and improvement\nPublic-data pilot',64,385,540,100,30,false,'#D1DFEA');
image(s,'Public fixed-camera road scene','build/video_source_frame.jpg',710,125,510,385);
text(s,'cover-caption','Public OpenCV sample, not HKMU footage',710,530,510,40,18,false,'#D1DFEA');
text(s,'group','LI DAOBO   GAO SHUN   LI RUNZE\nLI CHENYUAN   WANG JIALE',64,574,650,64,22,false,C.white);
s.speakerNotes.text=`Timing: 20 seconds. This project evaluates YOLO for detecting people and road vehicles and adds a simple zone-entry alert. The current experiments use public COCO images and an OpenCV video. They demonstrate a campus-oriented prototype, but do not validate performance on HKMU footage.\nSources: proposal supplied by the group. Cover image: ${urls.video}, first frame. Image unmodified.`;
}
{
const s=slide('Detection and zone-entry alerts',`Timing: 40 seconds. The detector recognizes six road-user classes. For each detected person, the system takes the bottom-centre of the bounding box as an approximate ground-contact point. A point-in-polygon test triggers an alert when that point enters the configured zone. The zone is specific to one camera. This rule does not estimate speed, intent or collision probability. Our questions concern model size, robustness and whether adaptation helps. Source: group proposal; ${urls.yolo}.`);
text(s,'question','Which detector offers a useful accuracy–speed trade-off?',64,162,1152,62,32,true,C.teal);
table(s,[['Stage','Operation'],['Detection','Person, bicycle, car, motorcycle, bus, truck'],['Geometry','Bottom-centre of each person box'],['Alert','Point inside a camera-specific polygon']],64,255,[230,922],66,26);
text(s,'boundary','An entry alert does not estimate collision risk.',64,570,1130,48,28,true,C.navy);
}
{
const s=slide('Public-data experiment',`Timing: 45 seconds. We sampled 300 unique images from COCO val2017 using a fixed seed. The class-based selection contributes 50 unique images per target class, although images can contain multiple classes, so instance counts are not balanced. We split these into 180 training, 60 validation and 60 test images. All splits have distinct IDs and file hashes. Model selection and confidence tuning use validation only. The original COCO class indices and 80-output head remain intact, but scoring is restricted to the six target classes. Because these models already use COCO, this is a public benchmark-family pilot rather than independent campus generalization. Source: data/manifest.json; ${urls.coco}.`);
table(s,[['Split','Images','Purpose'],['Train','180','Small-sample adaptation'],['Validation','60','Model choice and threshold selection'],['Test','60','Final comparison, fixed before testing']],64,168,[230,190,732],70,25);
text(s,'conditions',`416 × 416 input | CPU FP32 | Batch 1\nSeed 4330 | Six target classes`,64,480,1152,85,28,false,C.teal);
text(s,'scope','COCO-derived pilot. Results do not establish campus deployment accuracy.',64,600,1152,40,22,false,C.gray);
}
{
const n=r.yolov8n.original,sr=r.yolov8s.original;
const s=slide('Model size changes accuracy and speed',`Timing: 45 seconds. These are the held-out test results, not the validation scores used for selection. YOLOv8n reaches mAP50-95 ${f(n.map50_95)} and YOLOv8s reaches ${f(sr.map50_95)}. The larger model changes AP by ${(100*(sr.map50_95-n.map50_95)).toFixed(1)} percentage points. Timing covers an in-memory prediction call, excluding image loading, drawing and video encoding. CPU measurements describe this environment only. Precision and recall use confidence 0.25 and class-matched IoU 0.5. AP uses COCO evaluation with a low prediction floor of 0.001. Source: results/summary.json, raw prediction JSON files.`);
table(s,[['Model','P @ .25','R @ .25','mAP50','mAP50–95','FPS*'],['YOLOv8n',f(n.precision),f(n.recall),f(n.map50),f(n.map50_95),n.pipeline_fps.toFixed(1)],['YOLOv8s',f(sr.precision),f(sr.recall),f(sr.map50),f(sr.map50_95),sr.pipeline_fps.toFixed(1)]],64,205,[220,170,170,170,220,202],82,25);
text(s,'takeaway',`Validation selected ${chosen.replace('yolov8','YOLOv8')} for the adaptation experiment.`,64,510,1152,65,30,true,C.teal);
text(s,'fps-footnote','*In-memory detection pipeline. Excludes file I/O, drawing and encoding.',64,600,1152,35,20,false,C.gray);
}
{
const s=slide('Image degradation reduces detection quality',`Timing: 40 seconds. We apply the same transformations to every held-out test image and keep its original labels. Artificial darkness multiplies pixel intensity by 0.35. Blur uses a 9 by 9 Gaussian kernel with sigma 3. These controlled stress tests quantify sensitivity, not real night-time or natural occlusion performance. The chart compares the pretrained models under identical conditions. Source: src/experiment.py; results/summary.json.`);
chart(s,'Test mAP50–95',['Original','Darkened','Blurred'],[{name:'YOLOv8n',values:['original','dark','blur'].map(c=>r.yolov8n[c].map50_95),fill:C.teal},{name:'YOLOv8s',values:['original','dark','blur'].map(c=>r.yolov8s[c].map50_95),fill:C.orange}],64,170,790,405);
text(s,'transforms','Darkened\nIntensity × 0.35\n\nBlurred\nGaussian 9 × 9, σ = 3',900,210,310,260,27,false,C.ink);
text(s,'caveat','Synthetic stress tests. Real low-light and occlusion evaluation remains necessary.',64,612,1152,38,21,false,C.gray);
}
{
const b=r[chosen].original,t=r.finetuned.original,delta=t.map50_95-b.map50_95;
const s=slide(delta>=0?'Small-sample adaptation improves this test score':'Small-sample adaptation lowers this test score',`Timing: 50 seconds. We fine-tuned ${chosen} on 180 images with brightness and geometric augmentation. The first ten model modules were frozen, SGD started at 0.001 and early stopping used validation performance. The best validation checkpoint is evaluated here. Original-condition AP changes from ${f(b.map50_95)} to ${f(t.map50_95)}. This single run measures the combined adaptation package. It cannot isolate the causal contribution of augmentation. Confidence is tuned separately on validation F1, and changes operating precision and recall rather than the reported AP protocol. Sources: training/finetuned/args.yaml and results.csv; summary.json; thresholds.json.`);
chart(s,'Test mAP50–95',['Original','Darkened','Blurred'],[{name:'Pretrained '+chosen.replace('yolov8','v8'),values:['original','dark','blur'].map(c=>r[chosen][c].map50_95),fill:C.teal},{name:'Fine-tuned',values:['original','dark','blur'].map(c=>r.finetuned[c].map50_95),fill:C.orange}],64,170,790,405);
text(s,'change',`${delta>=0?'+':''}${(100*delta).toFixed(1)} pp`,900,205,300,85,57,true,C.navy);
text(s,'change-context','Change on original\ntest images',900,300,300,85,27,false,C.gray);
text(s,'training','180 training images\nBest validation\ncheckpoint | One seed',900,421,300,130,25,false,C.ink);
text(s,'limitation','Combined fine-tuning and augmentation experiment. No augmentation ablation.',64,612,1152,36,21,false,C.gray);
}
{
const s=slide('Zone alerts on a fixed-camera video',`Timing: 55 seconds, including about 15 seconds of the separate video. The yellow polygon is an illustrative road zone. A red point marks the bottom-centre of each person box. We inspected 24 evenly spaced source frames before looking at predictions and labelled whether a person was inside the zone. At the validation-selected threshold, the model produced ${video.tp} true positives, ${video.fp} false positives, ${video.fn} false negatives and ${video.tn} true negatives. This is a small, correlated single-camera sample. The labels came from a single visual review and need independent group checking, especially near boundaries. It does not measure collision risk. Source video: ${urls.video}. Evidence: configs/video_roi_labels.json, results/video_evaluation.json. Demonstration: Campus_Traffic_Demo.mp4.`);
image(s,'Detection and illustrative ROI','results/demo_80.jpg',64,166,735,410);
text(s,'video-count','24 labelled frames',850,180,360,52,31,true,C.teal);
table(s,[['Outcome','Frames'],['True positive',String(video.tp)],['False positive',String(video.fp)],['False negative',String(video.fn)],['True negative',String(video.tn)]],850,257,[240,120],55,23);
text(s,'video-caveat','One public video, one illustrative zone, single-review labels. Correlated frames.',64,612,1152,36,21,false,C.gray);
}
{
const delta=r.finetuned.original.map50_95-r[chosen].original.map50_95;
const s=slide('Findings and limits',`Timing: 40 seconds. The larger model improves detection AP at lower CPU speed, while this adaptation run does not improve AP. Future work includes campus footage and real low-light, occlusion and distance tests, supported by missed-detection and false-positive examples. The threshold was selected using detection F1. We have not established whether it reduces zone false alerts, so that comparison remains future work. Video labels also need independent review. Current evidence supports a public-data prototype. Source: experiment outputs and supplied proposal.`);
text(s,'finding1','Model size affects the accuracy–speed balance.',64,181,1152,70,33,true,C.navy);
text(s,'finding2',`Adaptation ${delta>=0?'improved':'reduced'} original-condition test AP by ${Math.abs(delta*100).toFixed(1)} pp.`,64,280,1152,70,33,true,C.teal);
text(s,'limit1','Evidence covers public images and one fixed-camera video.',64,396,1152,60,28,false,C.ink);
text(s,'limit2','Future work: real low-light, occlusion and distance tests.\nCompare zone false alerts across thresholds.',64,485,1152,100,28,false,C.ink);
}
{
const s=slide('Full test results',`Backup only. Precision/recall are micro-averaged at confidence 0.25 with same-class IoU >= 0.5. AP is the six-class macro average from pycocotools, maxDets 100. Converted Ultralytics labels do not preserve COCO crowd/ignore metadata, so these are custom-subset scores, not official COCO benchmark scores. Source: results/summary.json.`,true);
table(s,[['Model / condition','P','R','mAP50','mAP50–95'],...Object.entries(r).flatMap(([name,conditions])=>['original','dark','blur'].map(c=>[`${name} / ${c}`,f(conditions[c].precision),f(conditions[c].recall),f(conditions[c].map50),f(conditions[c].map50_95)]))],64,160,[420,170,170,190,202],45,21);
}
{
const s=slide('Reproducibility and operating thresholds',`Backup only. ${env.cpu_model}; ${env.threads} PyTorch CPU threads, Python ${env.python}, torch ${env.torch}, Ultralytics ${env.ultralytics}, OpenCV ${env.opencv}. Thresholds maximize validation detection F1 over 0.10, 0.20, 0.25, 0.30, 0.40, 0.50, 0.60 and 0.70. Ties prefer the lower threshold. No test-based tuning. Source: results/environment_packages.txt; thresholds.json; summary.json.`,true);
table(s,[['Model','Chosen confidence','Test P','Test R'],...Object.keys(r).map(name=>[name,thresholds[name].chosen_threshold.toFixed(2),f(r[name].tuned.precision),f(r[name].tuned.recall)])],64,180,[420,250,241,241],64,24);
text(s,'runtime',`${env.cpu_model}\nUltralytics ${env.ultralytics}     PyTorch ${env.torch}\nCPU, ${env.threads} threads, FP32, 416 × 416, batch 1`,64,490,1152,125,24,false,C.gray);
}
{
const s=slide('Team responsibilities',`Backup only. The roles below reproduce the submitted proposal. They describe assigned responsibilities, not a verified account of individual work already performed. Each member should review and be able to explain their section before presentation and final submission. Source: COMP4330SEF_Project_Proposal_P01_Group9_English.docx.`,true);
table(s,[['Member','Student ID','Proposal responsibility'],['LI DAOBO','13407753','Leadership and integration'],['GAO SHUN','13408577','Data and ethics'],['LI RUNZE','13420474','Baseline models'],['LI CHENYUAN','13365825','Evaluation and presentation'],['WANG JIALE','13253888','Improvement and demonstration']],64,175,[270,220,662],65,25);
}
{
const s=slide('References and evidence',`Backup only. Full references and raw evidence are included with the report and code package. All numeric result claims in this deck derive from locally executed experiments, not published benchmark tables.`,true);
const refs=[['1','Ultralytics YOLOv8 documentation',urls.yolo],['2','COCO dataset and annotations',urls.coco],['3','Redmon et al. (2016), You Only Look Once',urls.paper],['4','Lin et al. (2014), Microsoft COCO',urls.cocopaper],['5','OpenCV public video sample',urls.video]];
refs.forEach((q,i)=>{text(s,'reference-'+i,`${q[0]}. ${q[1]}\n${q[2]}`,64,160+i*88,1152,75,23,false,C.ink);});
}
await fs.mkdir(path.join(root,'build/slides'),{recursive:true});
for(let i=0;i<p.slides.items.length;i++){const b=await p.export({slide:p.slides.items[i],format:'png',scale:1});await fs.writeFile(path.join(root,'build/slides',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()));}
const candidate=path.join(root,'build/candidate.pptx');await(await PresentationFile.exportPptx(p)).save(candidate);
const output=path.join(root,'output/COMP4330_P01_Group9_Presentation_v3.pptx');
const final=await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath:output,pythonExecutable:process.env.CODEX_PRIMARY_RUNTIME_PYTHON,
 integrityValidatorPath:'/home/agent/.codex/skills/builtins/presentations/container_tools/inspect_presentation_package_integrity.py',
 layoutValidatorPath:'/home/agent/.codex/skills/builtins/presentations/container_tools/inspect_presentation_layout_geometry.py',
 layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...[2,3,4,7,9,10,11].flatMap(n=>['--require-native-table-slide',String(n)])],
 explicitTotalSlideCount:12,requiredNativeTableOwnerSlides:[2,3,4,7,9,10,11],requiredNativeChartOwnerSlides:[5,6],materializeLiteralChartWorkbooks:true,
 fontPolicy:{basis:'design',families:[FONT]},verifyArtifactToolImport:true,receiptPath:path.join(root,'build/deck_validation_v3.json')});
console.log(JSON.stringify(final));
await fs.writeFile(path.join(root,'build/slide_notes.json'),JSON.stringify(p.slides.items.map((s,i)=>({slide:i+1,notes:s.speakerNotes.text})),null,2));
