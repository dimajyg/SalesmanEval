import os
import schedule
import time
import shutil
from datetime import datetime

from utility.yandex_disk_connector import download_new_videos, ensure_shops_on_ydisk
from utility.video_compressor import batch_compress_videos
from utility.google_sheets_connector import get_salesman_data, ensure_shop_columns, store_metrics
from yolo.tracking.track import run
from metrics_evaluation.metrics import calculate_all_metrics


last_invoke_time = None

def pipeline():
    global last_invoke_time

    new_files = download_new_videos(last_check_time=last_invoke_time)

    g_sheets_table = 'Продавцы в магазинах'

    ensure_shops_on_ydisk()
    ensure_shop_columns(g_sheets_table)

    compressed_files = batch_compress_videos(new_files)

    salesmen = get_salesman_data(g_sheets_table)
    

    all_metrics = []
    for vid in compressed_files:
        shop_name = os.path.basename(os.path.dirname(vid))
        video_name = os.path.basename(vid)
        run(source=vid, project="data/results", name=f'{shop_name}/{video_name}', vid_stride=3)

        res_path = f"data/results/{shop_name}/{video_name}"
        
        metrics = calculate_all_metrics(detections_folder=f'{res_path}/labels',
                              video_path=f'{res_path}/salesman_labeled.mp4',
                              video_stride=3)
        
        metrics["date"] = datetime.strptime(video_name[:10], "%Y-%m-%d").date()
        metrics["shop_name"] = shop_name
        try:
            metrics["salesman"] = salesmen[metrics["date"]][metrics["shop_name"]]
        except KeyError:
            metrics["salesman"] = 'Unknown'

        all_metrics.append(metrics)
    
    store_metrics(all_metrics, g_sheets_table)

    try:
        shutil.rmtree("data/results")
    except FileNotFoundError:
        pass
    
    last_invoke_time = datetime.now()

if __name__ == "__main__":
    # Schedule daily at 07:00
    schedule.every().day.at("07:00").do(pipeline)

    while True:
        schedule.run_pending()
        time.sleep(60)
