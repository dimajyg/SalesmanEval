# Mikel Broström 🔥 Yolo Tracking 🧾 AGPL-3.0 license

__version__ = '10.0.52'

from src.yolo.boxmot.postprocessing.gsi import gsi
from src.yolo.boxmot.tracker_zoo import create_tracker, get_tracker_config
from src.yolo.boxmot.trackers.botsort.bot_sort import BoTSORT
from src.yolo.boxmot.trackers.bytetrack.byte_tracker import BYTETracker
from src.yolo.boxmot.trackers.deepocsort.deep_ocsort import DeepOCSort as DeepOCSORT
from src.yolo.boxmot.trackers.hybridsort.hybridsort import HybridSORT
from src.yolo.boxmot.trackers.ocsort.ocsort import OCSort as OCSORT
from src.yolo.boxmot.trackers.strongsort.strong_sort import StrongSORT

TRACKERS = ['bytetrack', 'botsort', 'strongsort', 'ocsort', 'deepocsort', 'hybridsort']

__all__ = ("__version__",
           "StrongSORT", "OCSORT", "BYTETracker", "BoTSORT", "DeepOCSORT", "HybridSORT",
           "create_tracker", "get_tracker_config", "gsi")
