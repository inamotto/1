import cv2
import numpy as np

def analyze_fractures(image, blur_ksize=5, canny_thresh1=50, canny_thresh2=150,
                     aperture=3, min_line_length=50, max_line_gap=10,
                     morph_kernel=3, filter_type='all', mm_per_pixel=None):
    """
    裂缝分析：返回结果字典和注释图像。
    """
    # 转灰度并高斯模糊
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if blur_ksize % 2 == 0:
        blur_ksize += 1  # 核大小为奇数
    blurred = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)
    # Canny 边缘检测:contentReference[oaicite:4]{index=4}
    edges = cv2.Canny(blurred, canny_thresh1, canny_thresh2, apertureSize=aperture)
    # 形态学闭运算连接断裂边缘
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_kernel, morph_kernel))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    # 霍夫线变换提取线段:contentReference[oaicite:5]{index=5}
    lines = cv2.HoughLinesP(closed, 1, np.pi/180, threshold=50,
                            minLineLength=min_line_length, maxLineGap=max_line_gap)
    fractures = []
    annotated = image.copy()
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            length_px = np.hypot(x2 - x1, y2 - y1)  # 像素长度
            angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))  # 角度
            orientation = 'horizontal' if abs(y2 - y1) < abs(x2 - x1) else 'vertical'
            # 根据指定类型过滤
            if filter_type == 'horizontal' and orientation != 'horizontal':
                continue
            if filter_type == 'vertical' and orientation != 'vertical':
                continue
            # 真实长度（毫米）
            length_real = None
            if mm_per_pixel:
                length_real = length_px * mm_per_pixel
            fractures.append({
                'endpoints': [(int(x1), int(y1)), (int(x2), int(y2))],
                'length_px': float(length_px),
                'length_mm': float(length_real) if length_real else None,
                'angle_deg': float(angle),
                'orientation': orientation
            })
            # 在注释图上绘制裂缝线
            cv2.line(annotated, (x1, y1), (x2, y2), (0, 0, 255), 2)
    result = {
        'num_fractures': len(fractures),
        'fractures': fractures
    }
    return result, annotated