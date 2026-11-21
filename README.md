# COMP4330SEF — P01 Group 9

> **GitHub upload status (2026-11-21):** Partial upload: README, .gitignore, requirements.txt, src/core.py, src/restore_data.py, and tests/test_core.py are published. The remaining source files, datasets, model weights, experiment records, and presentation assets have **not yet been uploaded**. The inventory below describes the full project archive, not the GitHub contents.


## 已完成的内容
- YOLOv8n / YOLOv8s 基线，验证集选择模型；180/60/60 张训练、验证、测试图像。
- 小样本微调、验证集置信度调节、原图/人工变暗/模糊共 9 组测试。
- 固定摄像头视频中的 polygon 区域进入提示，20 秒演示。
- 18 项自动检查全部通过。结果、预测、模型权重和日志均保留。
- 英文 PPT（8 页主讲 + 4 页隐藏答疑附录）、英文报告和演示视频。

当前成果是公开数据上的 prototype。未开展 HKMU 实拍、真实夜间或遮挡分层评测，也没有多随机种子实验。不能把合成变暗叫作真实夜间测试，不能把区域进入提示叫作碰撞预测。视频的 24 帧由助手在看到预测之前目视标注，组员尚未独立复核；不是 24 个独立事故样本。

## 主要结果
| 模型 | 测试 mAP50–95 | P@0.25 | R@0.25 | CPU call FPS |
|---|---:|---:|---:|---:|
| YOLOv8n | 0.309 | 0.730 | 0.427 | 21.8 |
| YOLOv8s | 0.393 | 0.719 | 0.535 | 14.2 |
| Fine-tuned v8s | 0.388 | 0.689 | 0.553 | 15.4 |

微调没有改善本次测试 AP。阈值 0.30 由验证集选定，使 v8s 测试 precision 为 0.768、recall 为 0.502。FPS 仅包含内存中的单次预测流程，不含读取、画框和编码；不同机器会变化。

## 文件及证据
- `src/`: 数据恢复、实验、几何规则、视频演示代码。
- `tests/`: 几何、匹配、已知答案 AP、数据完整性检查。
- `data/manifest.json`: 精确图片 URL、SHA256 和 split；300 张图和目标类标签已包含。
- `weights/`: 原始 n / s 权重。
- `results/training/finetuned/weights/best.pt`: 这次训练最佳 checkpoint。
- `results/summary.json`: 全部最终指标；`validation.json`：选择依据；`thresholds.json`：阈值扫描。
- `results/predictions_*.json`: 逐图原始预测和耗时。
- `results/tests.log`: 18 项测试记录；`logs/`：原始运行日志。
- `configs/video_roi_labels.json`: 标注及边界说明。
- `deliverables/`: PPT、报告、视频；PPT notes 含英文讲稿和来源。
- `authoring/`: 文档和 PPT 生成源代码。PPT 生成依赖托管环境的 Artifact Tool；实验运行不依赖它。

## 安装与运行（Windows PowerShell）
推荐 Python 3.12，在解压后的项目根目录执行：

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install torch==2.5.1 torchvision==0.20.1 --index-url https://download.pytorch.org/whl/cpu
python -m pip install -r requirements.txt
python src/restore_data.py
python -m unittest discover -s tests -v
python src/demo.py run
```

`restore_data.py` 校验已有图像并更新当前机器绝对路径。完整数据已包含，通常无需重新下载图片；如果缺失或损坏，会用 curl 按 manifest 恢复。Windows 自带 curl 可用。Linux/macOS 使用 `python3 -m venv .venv` 和 `source .venv/bin/activate`。原始运行是 Linux CPU；Windows 路径和处理器读取做了兼容，但未在 Windows 实机测试。

### 从现有预测重新计算指标

```powershell
python src/experiment.py validation
python src/experiment.py final
```

这两步默认使用附带的缓存预测，因此保留原实验耗时。不能将其视为新机器速度测试。

### 全部重新运行
先复制解压目录，保留原始证据。在副本中移除缓存再运行：

```powershell
Remove-Item results/predictions_*.json
python src/experiment.py validation
python src/experiment.py train
python src/experiment.py final
python src/demo.py run
python -m unittest discover -s tests -v
```

修改模型、输入尺寸或图像后必须清除对应预测缓存。重训可能有数值差异，速度也可能影响模型选择；保留新日志并重新生成报告数据，不能直接沿用旧 PPT。训练配置为最多 10 epochs、patience 4，原运行第 5 epoch 停止，best 为 epoch 1。训练输出日志可能带有原机器绝对路径，仅用于追溯。

## 五人讲解与复核建议（沿用 proposal）
| 人员 | Proposal 职责 | 建议主讲页 | 时长 | 需要掌握/复核 |
|---|---|---|---:|---|
| LI DAOBO | Leader / integration | 1、2、8 | 100 秒 | 问题、系统边界、总结、整合 |
| GAO SHUN | Data / ethics | 3 | 45 秒 | 数据来源、split、重复检查、公开数据限制 |
| LI RUNZE | Baseline models | 4 | 45 秒 | n/s、P/R、mAP、速度定义、模型选择 |
| LI CHENYUAN | Evaluation / presentation | 5 | 40 秒 | 变暗/模糊对照、指标与图表 |
| WANG JIALE | Improvement / demo | 6、7 | 105 秒 | 微调设置、负结果、ROI、播放约15秒视频 |

合计约 335 秒，保留约 25 秒用于换人和操作，控制在 6 分钟内。第 9–12 页为隐藏答疑页，可在 PowerPoint 编辑或跳转时打开。视频为单独 MP4，未内嵌；展示第 7 页时播放约 15 秒即可。先在实际汇报电脑排练并检查媒体播放。

以上是任务安排，不是已完成的个人贡献证明。最终报告的分工附录需由各成员按实际参与情况确认。

## 常见答辩问题
1. 为什么用了 COCO，而不是校园？当前是可复现公开数据 pilot；校园泛化仍需授权采集和独立测试。
2. 为什么选择 v8s？验证 AP 增益超过 0.05 且延迟不到 n 的两倍，符合预先设定规则。
3. 为什么微调没提升？本次只180张训练图、冻结部分模块、单次短训练，且已有 COCO 预训练；无法确定单一原因。报告如实保留负结果。
4. 0.393 是准确率39.3%吗？不是，它是 IoU 0.50–0.95 多阈值平均的六类 AP，不能等同分类 accuracy。
5. 24帧全对是不是100%可靠？不是，样本小、同一摄像头、帧间相关，且标签只经过一次助手目视复核。
6. 什么叫 zone alert？person 框底边中点进入配置的多边形就提示，不预测车速或碰撞。

## 来源与许可说明
- YOLOv8 models/docs: https://docs.ultralytics.com/models/yolov8/
- Weights: https://github.com/ultralytics/assets/releases/tag/v8.3.0
- COCO images: http://images.cocodataset.org/val2017/ ; exact IDs/URLs in manifest.
- Label archive: https://github.com/ultralytics/assets/releases/download/v0.0.0/coco2017labels.zip
- Video: https://github.com/opencv/opencv/blob/4.x/samples/data/vtest.avi
- `licenses/Ultralytics_LICENSE.txt` 是所用软件包的原始许可；`licenses/LabelArchive_LICENSE.txt` 是标签下载归档附带的原文，不代表 COCO 图片统一适用该许可。原图片权利归各自作者，参见 COCO 原始图片记录。

实现、报告和演示材料由助手协助生成；实验数值来自实际执行，视频标签来源如上记录。

## 2026年11月12日范围确认
真实低光、遮挡、远距离目标分组以及漏检/误检案例分析列为当前不足与未来工作。人工变暗和模糊测试保留为已完成实验。阈值按检测 F1 选择，尚未证明其降低区域提示误报，跨阈值的区域误报/漏报对照列为未来工作。本次不追加该实验，所有已记录指标保持不变。

### 视频输出在哪里
`deliverables/Campus_Traffic_Demo.mp4` 是原始公开视频前 200 帧的程序处理结果，共20秒。绿色框为检测结果，红点为 person 框底边中点，黄色多边形为配置区域，顶部文字显示区域内是否检测到人。视频文件单独提供，PPT第7页仅放静态截图。
`results/video_evaluation.json` 是24个等间隔抽样帧的区域判定对照，来自原始795帧完整视频，包含19个正例、5个负例，模型与当前标签一致。24帧不全部出现在20秒演示片段里，且并非独立安全事件。