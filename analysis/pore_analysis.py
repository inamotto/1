import cv2
import numpy as np

def analyze_pores(image, blur_ksize=5, thresh_val=128,
                  min_pore_area=10, fill_thresh=100, mm_per_pixel=None):
    """
    孔洞分析：返回结果字典和注释图像。
    """
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    if blur_ksize % 2 == 0:
        blur_ksize += 1
    blurred = cv2.GaussianBlur(gray, (blur_ksize, blur_ksize), 0)
    # 二值化（假设孔洞为暗区）
    _, binary = cv2.threshold(blurred, thresh_val, 255, cv2.THRESH_BINARY_INV)
    # 开运算去噪
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    opened = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)
    # 闭运算填充孔洞
    filled = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel, iterations=1)
    # 轮廓检测:contentReference[oaicite:8]{index=8}
    contours, _ = cv2.findContours(filled, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    pores = []
    annotated = image.copy()
    for cnt in contours:
        area = cv2.contourArea(cnt)
        # 根据面积过滤
        if area < min_pore_area or area > fill_thresh:
            continue
        eq_diam_px = np.sqrt(4 * area / np.pi)  # 等效直径（像素）
        # 计算质心
        M = cv2.moments(cnt)
        if M["m00"] != 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
        else:
            cx, cy = 0, 0
        # 真是面积和直径
        area_real = None
        diam_real = None
        if mm_per_pixel:
            area_real = area * (mm_per_pixel**2)
            diam_real = eq_diam_px * mm_per_pixel
        pores.append({
            'centroid': [cx, cy],
            'area_px': float(area),
            'equivalent_diameter_px': float(eq_diam_px),
            'area_mm2': float(area_real) if area_real else None,
            'equivalent_diameter_mm': float(diam_real) if diam_real else None
        })
        # 注释图像：绘制轮廓和圆
        cv2.drawContours(annotated, [cnt], -1, (255, 0, 0), 1)
        cv2.circle(annotated, (cx, cy), int(eq_diam_px/2), (255, 0, 0), 1)
    result = {
        'num_pores': len(pores),
        'pores': pores
    }
    return result, annotated