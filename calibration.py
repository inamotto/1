def calibrate_by_dpi(dpi):
    """
    根据DPI计算每像素对应的毫米数。
    """
    mm_per_pixel = 25.4 / dpi  # 1英寸=25.4毫米:contentReference[oaicite:1]{index=1}
    return mm_per_pixel

def calibrate_manual(pixel_count, real_length_mm):
    """
    手动标定：pixel_count像素对应real_length_mm毫米。
    """
    mm_per_pixel = real_length_mm / pixel_count
    return mm_per_pixel

def pixel_to_length(px, mm_per_pixel):
    """
    将像素长度转换为毫米。
    """
    return px * mm_per_pixel

def pixel_to_area(px_area, mm_per_pixel):
    """
    将像素面积转换为平方毫米。
    """
    return px_area * (mm_per_pixel**2)