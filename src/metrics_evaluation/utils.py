import cv2
import os
import matplotlib.pyplot as plt
import re

def find_main_character_tracks(folder_path, in_place=True):
    # List all .txt files in the folder, assuming filenames are in the format <filename>_<frame_index>.txt
    files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.txt')]
    # Sort files by their frame index to ensure chronological order
    files.sort(key=lambda x: int(re.search(r'_(\d+)\.txt', x).group(1)))

    # Dictionary to store the frame index where each track was seen: key=index, value=set of frame indices
    track_frames = {}

    # Collect all track data and frame indices
    for file_path in files:
        frame_index = int(re.search(r'_(\d+)\.txt', file_path).group(1))
        with open(file_path, 'r') as file:
            for line in file:
                parts = line.split()
                if len(parts) < 6:
                    continue
                index = int(parts[5])
                if index not in track_frames:
                    track_frames[index] = []
                track_frames[index].append(frame_index)

    # Sort tracks by their length (number of frames) in descending order
    sorted_tracks = sorted(track_frames.items(), key=lambda x: len(x[1]), reverse=True)
    # Concatenate tracks to cover the whole video length without frame overlap
    main_character_tracks = []
    used_frames = set()  # Set to keep track of used frame indices

    for index, frames in sorted_tracks:
        # Filter out track segments whose frames have already been used
        new_segments = len(set(frames) & used_frames) == 0
        if new_segments:
            main_character_tracks.append(index)
            used_frames.update(frames)

    # Sort the final track by frame index to maintain chronological order
    main_character_tracks.sort()
    if in_place:
        for file_path in files:
            with open(file_path, 'r+') as file:
                lines = []
                for line in file:
                    parts = line.split()
                    if len(parts) < 6:
                        continue
                    index = int(parts[5])
                    if index in main_character_tracks:
                        parts[5] = '-1'
                    lines.append(' '.join(parts) + '\n')
            with open(file_path, 'w') as file:
                for line in lines:
                    file.write(line)

    return main_character_tracks

def process_video_and_plot_boxes(video_path, video_stride, tracking_folder, output_path):
    # Create a dictionary to map indices to colors
    color_map = {}

    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise IOError("Cannot open video file")

    # Get video properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = int(cap.get(cv2.CAP_PROP_FPS))

    # Define the codec and create a VideoWriter object to write the video
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    video_name = video_path.split('/')[-1][:-4]

    frame_count = 1
    curr_frame = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if curr_frame % video_stride == 0:
            # Construct the filename for the tracking results
            tracking_file = os.path.join(tracking_folder, f"{video_name}_{frame_count}.txt")
            if os.path.exists(tracking_file):
                with open(tracking_file, 'r') as file:
                    for line in file:
                        parts = line.strip().split()
                        class_id, x_center, y_center, w, h, index = list(map(float, parts[:5])) + [int(parts[5])]

                        # Scale coordinates
                        x1 = int((x_center - w * 0.5) * width)
                        x2 = int((x_center + w * 0.5) * width)
                        y1 = int((y_center + h * 0.5) * height)
                        y2 = int((y_center - h * 0.5) * height)

                        # Draw the rectangle on the frame
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255) if index  == -1 else (0, 255, 0), 2)
                        cv2.putText(frame, 'Salesman' if index == -1 else f'customer {index}', (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255) if index  == -1 else (0, 255, 0), 2)
            frame_count += 1
            # Write the frame into the file 'output_video.mp4'
            out.write(frame)
        curr_frame += 1

    # Release everything if job is finished
    cap.release()
    out.release()
    cv2.destroyAllWindows()