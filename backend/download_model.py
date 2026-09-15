"""Download the RoadRead road-damage checkpoint for offline/local inference."""
from pathlib import Path
import requests

ROOT=Path(__file__).resolve().parent
MODEL_DIR=ROOT/'models'/'road_damage'
MODEL_PATH=MODEL_DIR/'yolov8s_rdd2022.pt'
URL='https://huggingface.co/SreekarAditya/yolo-rdd2022-benchmark/resolve/main/yolo-rdd2022-benchmark/yolov8s_seed0_best.pt?download=true'
MODEL_DIR.mkdir(parents=True, exist_ok=True)
if MODEL_PATH.exists() and MODEL_PATH.stat().st_size >= 10_000_000:
    print(f'Already present: {MODEL_PATH}')
else:
    print('Downloading ~22.5 MB RDD2022 YOLOv8s checkpoint...')
    tmp=MODEL_PATH.with_suffix('.download')
    with requests.get(URL,stream=True,timeout=(20,300)) as r:
        r.raise_for_status()
        with open(tmp,'wb') as f:
            for chunk in r.iter_content(chunk_size=1024*1024):
                if chunk: f.write(chunk)
    tmp.replace(MODEL_PATH)
    print(f'Downloaded: {MODEL_PATH}')
