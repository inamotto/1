import cv2
import numpy as np

def analyze_grains(image, blur_ksize=5, thresh_val=128,
                   min_grain_size=10, max_grain_size=1000, morph_iter=1, mm_per_pixel=None):
    """
    粒度分析：返回结果字典和注释图像。
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if blur_ksize % 2 == 0:
        blur_ksize += 1
    blurred = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)
    # 二值化
    _, binary = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY)
    # 多次形态学开运算
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3,3))
    morphed = binary.copy()
    for i in range(morph_iter):
        morphed = cv2.morphologyEx(morphed, cv2.MORPH_OPEN, kernel)
    # 轮廓检测
    contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    grains = []
    annotated = image.copy()
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < min_grain_size or area > max_grain_size:
            continue
        eq_diam_px = np.sqrt(4 * area / np.pi)
        area_real = None
        diam_real = None
        phi = None
        if mm_per_pixel:
            area_real = area * (mm_per_pixel**2)
            diam_real = eq_diam_px * mm_per_pixel
            if diam_real > 0:
                phi = -np.log2(diam_real)  # 粒度学定义:contentReference[oaicite:12]{index=12}
        grains.append({
            'area_px': float(area),
            'equivalent_diameter_px': float(eq_diam_px),
            'area_mm2': float(area_real) if area_real else None,
            'equivalent_diameter_mm': float(diam_real) if diam_real else None,
            'phi': float(phi) if phi else None
        })
        # 注释图像：绘制颗粒轮廓和圆
        cv2.drawContours(annotated, [cnt], -1, (0, 255, 0), 1)
        x0, y0 = cnt[0][0]
        cv2.circle(annotated, (int(x0), int(y0)), int(eq_diam_px/2), (0, 255, 0), 1)
    result = {
        'num_grains': len(grains),
        'grains': grains
    }
    return result, annotated