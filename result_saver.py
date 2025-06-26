import os
import json
import cv2
from datetime import datetime

def save_results(data, analysis_type, annotated_image=None):
    """
    保存JSON结果（可选保存注释图像）到对应目录，文件名使用时间戳。
    analysis_type: 'fracture', 'pore', 或 'grain'
    """
    type_dir_map = {
        'fracture': '裂缝',
        'pore': '孔洞',
        'grain': '粒度'
    }
    if analysis_type not in type_dir_map:
        raise ValueError("Unknown analysis type")
    subfolder = type_dir_map[analysis_type]
    base_dir = os.path.join('results', subfolder)
    os.makedirs(base_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    json_path = os.path.join(base_dir, f'{timestamp}.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    # 可选保存注释图
    if annotated_image is not None:
        image_path = os.path.join(base_dir, f'{timestamp}.png')
        cv2.imwrite(image_path, annotated_image)
    return json_path