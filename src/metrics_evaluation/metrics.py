import cv2
import re
import numpy as np
from abc import ABC, abstractmethod

class MetricCalculator(ABC):
    """
    Abstract class to calculate metrics on objects tracked in video frames.
    Each subclass should implement the compute_metric method.
    """

    def __init__(self, files, video_path, video_stride):
        """
        :param files: list of .txt file paths for each frame's YOLO detections
        :param video_path: path to the source video
        :param video_stride: frame stride (not always used, but left here for reference)
        """
        self.video_stride = video_stride
        self.files = files  # Expecting a list of strings (paths)
        self.video_path = video_path

        self.width, self.height = self._get_video_dimensions(video_path)
        # Build dictionaries to track bounding boxes, frames, etc.
        self.tracks_dict, self.frames_info, self.tracks_info = self._process_files(self.files)

    @staticmethod
    def _get_video_dimensions(video_path):
        """Return (width, height) of the video."""
        video = cv2.VideoCapture(video_path)
        if not video.isOpened():
            print(f"Error: Could not open video file {video_path}")
            return None, None

        width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT))
        video.release()
        return width, height

    def _process_files(self, file_paths):
        """
        Reads each YOLO .txt detection file; extracts bounding boxes,
        organizes them by track ID, by frame, etc.
        
        Returns:
            tracks_dict: {track_id: [list_of_frame_indices]}
            frames_info: {frame_index: {track_id: (x1, x2, y1, y2)}}
            tracks_info: {track_id: (class_id, 'salesman'/'other')}
        """
        tracks_dict = {}
        frames_info = {}
        tracks_info = {}

        for file_path in file_paths:
            # 1) Parse the frame index from file name, e.g. "video_123.txt" -> frame_index=123
            match = re.search(r'_(\d+)\.txt$', file_path)
            if not match:
                print(f"Warning: Could not parse frame index from {file_path}")
                continue

            frame_index = int(match.group(1))

            # 2) Read each detection line
            with open(file_path, 'r') as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) < 6:
                        # Expecting at least: class_id, x_center, y_center, w, h, track_id
                        continue

                    class_id = int(parts[0])
                    x_center, y_center, w, h = map(float, parts[1:5])

                    # Convert track_id to int (assuming -1 for salesman)
                    try:
                        track_id = int(parts[5])
                    except ValueError:
                        # If not parseable, store as string
                        track_id = parts[5]

                    # 3) Convert YOLO-normalized coords into pixel bounding box
                    x1 = int((x_center - w * 0.5) * self.width)
                    x2 = int((x_center + w * 0.5) * self.width)
                    y1 = int((y_center - h * 0.5) * self.height)
                    y2 = int((y_center + h * 0.5) * self.height)

                    # Ensure track dict entry
                    if track_id not in tracks_dict:
                        tracks_dict[track_id] = []
                    tracks_dict[track_id].append(frame_index)

                    # Ensure frames_info entry
                    if frame_index not in frames_info:
                        frames_info[frame_index] = {}
                    frames_info[frame_index][track_id] = (x1, x2, y1, y2)

                    # Ensure tracks_info entry (class label, role, etc.)
                    if track_id not in tracks_info:
                        if track_id == -1:
                            tracks_info[track_id] = (class_id, 'salesman')
                        else:
                            tracks_info[track_id] = (class_id, 'other')

        return tracks_dict, frames_info, tracks_info

    @abstractmethod
    def compute_metric(self):
        """Compute the metric using the provided tracking data."""
        pass


class AreaMetricCalculator(MetricCalculator):
    """
    Example metric:
    - Compare each person's maximum bounding-box area to the salesman's average area.
    - Count how many persons exceed the salesman's area threshold.
    """

    def compute_metric(self):
        # Helper to get area of track_id at a specific frame
        def find_area(tid, fidx):
            x1, x2, y1, y2 = self.frames_info[fidx][tid]
            return abs(x2 - x1) * abs(y2 - y1)

        # 1) Salesman track is -1
        if -1 not in self.tracks_dict or len(self.tracks_dict[-1]) == 0:
            # No salesman track found
            return 0

        salesman_frames = self.tracks_dict[-1]
        # Average bounding-box area of the salesman across all frames he appears
        salesman_areas = [find_area(-1, f) for f in salesman_frames]
        salesman_area_mean = np.mean(salesman_areas) if salesman_areas else 0

        # 2) Count how many other tracks have a max area > salesman's mean area
        bigger_count = 0
        for tid, frames in self.tracks_dict.items():
            if tid == -1:
                continue  # skip the salesman
            track_areas = [find_area(tid, f) for f in frames if f in self.frames_info and tid in self.frames_info[f]]
            if track_areas and max(track_areas) > salesman_area_mean:
                bigger_count += 1

        return bigger_count


class SpeedReductionMetricCalculator(MetricCalculator):
    """
    Example metric:
    - For each track, compute speeds between consecutive frames.
    - If there's a "significant slowdown" (threshold-based) from one step to the next, we count it.
    - The metric returns how many distinct tracks had at least one such slowdown.
    """

    def compute_metric(self):
        significant_reduction_count = 0
        threshold = 0.5  # 50% slowdown threshold

        def compute_center(box):
            x1, x2, y1, y2 = box
            cx = (x1 + x2) / 2
            cy = (y1 + y2) / 2
            return (cx, cy)

        def compute_speed(track_id, f1, f2):
            box1 = self.frames_info[f1][track_id]
            box2 = self.frames_info[f2][track_id]
            cx1, cy1 = compute_center(box1)
            cx2, cy2 = compute_center(box2)
            return np.sqrt((cx2 - cx1)**2 + (cy2 - cy1)**2)

        for tid, frames in self.tracks_dict.items():
            # Sort frames so we measure speeds in chronological order
            sorted_frames = sorted(frames)
            speeds = []
            # Compute speeds between consecutive frames
            for i in range(1, len(sorted_frames)):
                f_prev = sorted_frames[i - 1]
                f_curr = sorted_frames[i]
                if (f_prev in self.frames_info and f_curr in self.frames_info and
                        tid in self.frames_info[f_prev] and tid in self.frames_info[f_curr]):
                    s = compute_speed(tid, f_prev, f_curr)
                    speeds.append(s)
            
            slowdown_detected = False
            for i in range(1, len(speeds)):
                prev_s, curr_s = speeds[i - 1], speeds[i]
                if prev_s > 0 and (prev_s - curr_s) / prev_s > threshold:
                    slowdown_detected = True
                    break
            if slowdown_detected:
                significant_reduction_count += 1

        return significant_reduction_count


class SalesmanInteractionMetricCalculator(MetricCalculator):
    """
    Example metric:
    - Count how many distinct other tracks physically intersect
      the salesman bounding box in at least one frame.
    """

    def compute_metric(self):
        salesman_id = -1
        if salesman_id not in self.tracks_dict:
            # No salesman present
            return 0

        def _normalize_box(box):
            x1, x2, y1, y2 = box
            left = min(x1, x2)
            right = max(x1, x2)
            top = min(y1, y2)
            bottom = max(y1, y2)
            return (left, right, top, bottom)

        def _intersection_area(boxA, boxB):
            Ax1, Ax2, Ay1, Ay2 = _normalize_box(boxA)
            Bx1, Bx2, By1, By2 = _normalize_box(boxB)

            inter_left = max(Ax1, Bx1)
            inter_right = min(Ax2, Bx2)
            inter_top = max(Ay1, By1)
            inter_bottom = min(Ay2, By2)

            if inter_right > inter_left and inter_bottom > inter_top:
                return (inter_right - inter_left) * (inter_bottom - inter_top)
            return 0

        salesman_frames = self.tracks_dict[salesman_id]
        interacting_tracks = set()

        for frame_idx in salesman_frames:
            if frame_idx not in self.frames_info:
                continue
            salesman_box = self.frames_info[frame_idx].get(salesman_id, None)
            if salesman_box is None:
                continue
            # Check other TIDs in the same frame
            for other_tid, other_box in self.frames_info[frame_idx].items():
                if other_tid == salesman_id:
                    continue
                if _intersection_area(salesman_box, other_box) > 0:
                    interacting_tracks.add(other_tid)

        return len(interacting_tracks)


class SalesmanAttendanceMetricCalculator(MetricCalculator):
    """
    Example metric:
    - Measures how frequently the salesman (track_id = -1) appears 
      among all frames for which we have detection files.
    - Returns a fraction: (number_of_frames_with_salesman) / (total_detected_frames).
    """

    def compute_metric(self):
        salesman_id = -1
        # Gather all frame indices from the detection files (keys of frames_info)
        all_frames = sorted(list(self.frames_info.keys()))
        total_frames_count = len(all_frames)
        if total_frames_count == 0:
            return 0.0  # No frames to analyze

        if salesman_id not in self.tracks_dict:
            # No salesman at all
            return 0.0

        # Unique frames in which salesman appears
        salesman_frames = set(self.tracks_dict[salesman_id])
        # Intersection with all_frames just in case
        # But presumably all frames in tracks_dict are in frames_info anyway
        frames_with_salesman = salesman_frames.intersection(all_frames)
        salesman_frames_count = len(frames_with_salesman)

        # Return fraction of frames that include salesman
        return salesman_frames_count / total_frames_count


import os
def calculate_all_metrics(detections_folder, video_path, video_stride):
    """
    Convenience function that:
      - Creates each metric calculator
      - Computes the metric
      - Returns a dictionary of results
    :param detections_folder: path to the folder containing detection files (.txt)
    :param video_path: path to the corresponding video
    :param video_stride: the frame stride, if applicable
    :return: dict with named metric results
    """
    files = [os.path.join(detections_folder, f) for f in os.listdir(detections_folder) if f.endswith(".txt")]
    area_calc = AreaMetricCalculator(files, video_path, video_stride)
    speed_calc = SpeedReductionMetricCalculator(files, video_path, video_stride)
    interaction_calc = SalesmanInteractionMetricCalculator(files, video_path, video_stride)
    attendance_calc = SalesmanAttendanceMetricCalculator(files, video_path, video_stride)

    results = {
        "area_metric": area_calc.compute_metric(),
        "speed_metric": speed_calc.compute_metric(),
        "interaction_metric": interaction_calc.compute_metric(),
        "salesman_attendance": attendance_calc.compute_metric()
    }
    return results


if __name__ == "__main__":
    detections_folder = "/Users/dtikhanovskii/Documents/SalesmanEval/results/runs/track/kek2/labels"  # Path to the folder
    video_path = "/Users/dtikhanovskii/Documents/SalesmanEval/results/runs/track/kek2/salesman_labeled.mp4"
    video_stride = 10  # or whatever you use

    metrics = calculate_all_metrics(detections_folder, video_path, video_stride)
    print("Computed Metrics:", metrics)
