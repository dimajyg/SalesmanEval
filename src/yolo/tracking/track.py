# Mikel Broström 🔥 Yolo Tracking 🧾 AGPL-3.0 license

import argparse
import cv2
import numpy as np
from functools import partial
from pathlib import Path

import torch

from src.yolo.boxmot import TRACKERS
from src.yolo.boxmot.tracker_zoo import create_tracker
from src.yolo.boxmot.utils import ROOT, WEIGHTS, TRACKER_CONFIGS
from src.yolo.boxmot.utils.checks import TestRequirements
from src.yolo.tracking.detectors import get_yolo_inferer

__tr = TestRequirements()
__tr.check_packages(('ultralytics @ git+https://github.com/mikel-brostrom/ultralytics.git', ))  # install

from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator, colors
from ultralytics.data.utils import VID_FORMATS
from ultralytics.utils.plotting import save_one_box

from types import SimpleNamespace

from metrics_evaluation import utils


def on_predict_start(predictor, persist=False):
    """
    Initialize trackers for object tracking during prediction.

    Args:
        predictor (object): The predictor object to initialize trackers for.
        persist (bool, optional): Whether to persist the trackers if they already exist. Defaults to False.
    """

    assert predictor.custom_args.tracking_method in TRACKERS, \
        f"'{predictor.custom_args.tracking_method}' is not supported. Supported ones are {TRACKERS}"

    tracking_config = TRACKER_CONFIGS / (predictor.custom_args.tracking_method + '.yaml')
    trackers = []
    for i in range(predictor.dataset.bs):
        tracker = create_tracker(
            predictor.custom_args.tracking_method,
            tracking_config,
            predictor.custom_args.reid_model,
            predictor.device,
            predictor.custom_args.half,
            predictor.custom_args.per_class
        )
        # motion only modeles do not have
        if hasattr(tracker, 'model'):
            tracker.model.warmup()
        trackers.append(tracker)

    predictor.trackers = trackers


@torch.no_grad()

def run(yolo_model=WEIGHTS / 'yolov8n', source='0', imgsz=[640], conf=0.5, iou=0.7, device='', show=False, save=True, classes=None, project='', name='exp', exist_ok=False, half=False, vid_stride=1, show_labels=False, show_conf=False, show_trajectories=True, save_txt=True, save_id_crops=False, line_width=None, per_class=False, verbose=True, agnostic_nms=False, reid_model=WEIGHTS / 'osnet_x0_25_msmt17.pt', tracking_method='deepocsort'):

    yolo = YOLO(
        yolo_model if 'yolov8' in str(yolo_model) else 'yolov8n.pt',
    )

    results = yolo.track(
        source=source,
        conf=conf,
        iou=iou,
        agnostic_nms=agnostic_nms,
        show=show,
        stream=True,
        device=device,
        show_conf=show_conf,
        save_txt=save_txt,
        show_labels=show_labels,
        save=save,
        verbose=verbose,
        exist_ok=exist_ok,
        project=project,
        name=name,
        classes=classes,
        imgsz=imgsz,
        vid_stride=vid_stride,
        line_width=line_width
    )

    yolo.add_callback('on_predict_start', partial(on_predict_start, persist=True))

    if 'yolov8' not in str(yolo_model):
        # replace yolov8 model
        m = get_yolo_inferer(yolo_model)
        model = m(
            model=yolo_model,
            device=yolo.predictor.device,
            args=yolo.predictor.args
        )
        yolo.predictor.model = model

    # store custom args in predictor
    yolo.predictor.custom_args = SimpleNamespace(**locals())
    print(yolo.predictor.save_dir)

    for r in results:

        img = yolo.predictor.trackers[0].plot_results(r.orig_img, show_trajectories)

        if show is True:
            cv2.imshow('BoxMOT', img)     
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' ') or key == ord('q'):
                break
    
    utils.find_main_character_tracks(f'{yolo.predictor.save_dir}/labels')
    utils.process_video_and_plot_boxes(source, vid_stride, f'{yolo.predictor.save_dir}/labels',  f'{yolo.predictor.save_dir}/salesman_labeled.mp4')
