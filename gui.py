import sys
import cv2
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, QPushButton,
                             QVBoxLayout, QHBoxLayout, QFileDialog, QComboBox,
                             QSpinBox, QRadioButton, QMessageBox)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from analysis.fracture_analysis import analyze_fractures
from analysis.pore_analysis import analyze_pores
from analysis.grain_analysis import analyze_grains
from calibration import calibrate_by_dpi, calibrate_manual
from result_saver import save_results


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("岩心图像分析工具")
        self.image = None
        self.mm_per_pixel = None
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        # 左侧控制面板
        self.control_panel = QVBoxLayout()  # 使用 control_panel 来保存控制面板
        load_btn = QPushButton("加载图像")
        load_btn.clicked.connect(self.load_image)
        self.control_panel.addWidget(load_btn)

        self.combo = QComboBox()
        self.combo.addItems(["裂缝", "孔洞", "粒度"])
        self.combo.currentIndexChanged.connect(self.update_parameters)  # 绑定选择变化事件
        self.control_panel.addWidget(QLabel("选择分析模块："))
        self.control_panel.addWidget(self.combo)

        self.update_parameters()  # 初始化时更新参数设置

        # 高斯模糊核 (奇数)
        self.control_panel.addWidget(QLabel("高斯模糊核 (奇数):"))
        self.blur_spin = QSpinBox()
        self.blur_spin.setRange(1, 31)
        self.blur_spin.setValue(5)
        self.control_panel.addWidget(self.blur_spin)

        # 阈值设置
        self.control_panel.addWidget(QLabel("阈值:"))
        self.thresh_spin = QSpinBox()
        self.thresh_spin.setRange(0, 255)
        self.thresh_spin.setValue(128)
        self.control_panel.addWidget(self.thresh_spin)

        # 最小长度/面积
        self.control_panel.addWidget(QLabel("最小长度/面积:"))
        self.min_spin = QSpinBox()
        self.min_spin.setRange(0, 10000)
        self.min_spin.setValue(50)
        self.control_panel.addWidget(self.min_spin)

        # 校准方式选择
        self.control_panel.addWidget(QLabel("校准方式："))
        self.auto_radio = QRadioButton("自动 (DPI)")
        self.manual_radio = QRadioButton("手动")
        self.auto_radio.setChecked(True)
        self.control_panel.addWidget(self.auto_radio)
        self.control_panel.addWidget(self.manual_radio)

        # DPI和手动模式的控制
        self.control_panel.addWidget(QLabel("DPI:"))
        self.dpi_spin = QSpinBox()
        self.dpi_spin.setRange(1, 1000)
        self.dpi_spin.setValue(300)
        self.control_panel.addWidget(self.dpi_spin)

        self.control_panel.addWidget(QLabel("像素数 (手动):"))
        self.pixel_spin = QSpinBox()
        self.pixel_spin.setRange(1, 10000)
        self.pixel_spin.setValue(100)
        self.control_panel.addWidget(self.pixel_spin)

        self.control_panel.addWidget(QLabel("真实长度(mm):"))
        self.real_spin = QSpinBox()
        self.real_spin.setRange(1, 100000)
        self.real_spin.setValue(10)
        self.control_panel.addWidget(self.real_spin)

        # 开始分析按钮
        analyze_btn = QPushButton("开始分析")
        analyze_btn.clicked.connect(self.perform_analysis)
        self.control_panel.addWidget(analyze_btn)

        # 保存结果按钮
        save_btn = QPushButton("保存结果")
        save_btn.clicked.connect(self.save_results)
        self.control_panel.addWidget(save_btn)

        self.control_panel.addStretch()
        main_layout.addLayout(self.control_panel)

        # 右侧图像显示
        self.image_label = QLabel("暂无图像")
        self.image_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(self.image_label)

    def update_parameters(self):
        # 获取当前选择的分析模块
        analysis_type = self.combo.currentText()

        # 清空现有的参数设置
        self.clear_parameters()

        # 根据选择的分析模块更新参数设置
        if analysis_type == "裂缝":
            self.control_panel.addWidget(QLabel("Canny 边缘检测阈值:"))
            self.canny_thresh_spin = QSpinBox()
            self.canny_thresh_spin.setRange(0, 255)
            self.canny_thresh_spin.setValue(50)
            self.control_panel.addWidget(self.canny_thresh_spin)

            self.control_panel.addWidget(QLabel("最小裂缝长度:"))
            self.min_length_spin = QSpinBox()
            self.min_length_spin.setRange(0, 10000)
            self.min_length_spin.setValue(50)
            self.control_panel.addWidget(self.min_length_spin)

        elif analysis_type == "孔洞":
            self.control_panel.addWidget(QLabel("孔洞阈值:"))
            self.pore_thresh_spin = QSpinBox()
            self.pore_thresh_spin.setRange(0, 255)
            self.pore_thresh_spin.setValue(128)
            self.control_panel.addWidget(self.pore_thresh_spin)

            self.control_panel.addWidget(QLabel("最小孔洞面积:"))
            self.min_pore_area_spin = QSpinBox()
            self.min_pore_area_spin.setRange(0, 10000)
            self.min_pore_area_spin.setValue(10)
            self.control_panel.addWidget(self.min_pore_area_spin)

        elif analysis_type == "粒度":
            self.control_panel.addWidget(QLabel("粒度阈值:"))
            self.grain_thresh_spin = QSpinBox()
            self.grain_thresh_spin.setRange(0, 255)
            self.grain_thresh_spin.setValue(128)
            self.control_panel.addWidget(self.grain_thresh_spin)

            self.control_panel.addWidget(QLabel("最小颗粒面积:"))
            self.min_grain_area_spin = QSpinBox()
            self.min_grain_area_spin.setRange(0, 10000)
            self.min_grain_area_spin.setValue(10)
            self.control_panel.addWidget(self.min_grain_area_spin)

    def clear_parameters(self):
        # 清空控制面板中的现有控件
        for i in reversed(range(self.control_panel.count())):
            widget = self.control_panel.itemAt(i).widget()
            if widget and widget != self.combo:
                widget.deleteLater()

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图像文件", "", "Images (*.png *.jpg *.bmp)")
        if file_path:
            self.image = cv2.imread(file_path)
            if self.image is None:
                QMessageBox.critical(self, "错误", "无法加载图像。")
                return
            # 在QLabel中显示原图（缩放到最大400x400）
            h, w = self.image.shape[:2]
            qimg = QImage(self.image.data, w, h, 3 * w, QImage.Format_BGR888)
            self.image_label.setPixmap(QPixmap.fromImage(qimg).scaled(400, 400, Qt.KeepAspectRatio))

    def perform_analysis(self):
        if self.image is None:
            QMessageBox.warning(self, "提示", "请先加载图像。")
            return
        # 选择标定方法
        if self.auto_radio.isChecked():
            dpi = self.dpi_spin.value()
            self.mm_per_pixel = calibrate_by_dpi(dpi)
        else:
            px = self.pixel_spin.value()
            length = self.real_spin.value()
            self.mm_per_pixel = calibrate_manual(px, length)
        # 获取参数
        blur = self.blur_spin.value()
        thresh = self.thresh_spin.value()
        min_val = self.min_spin.value()
        analysis_type = self.combo.currentText()
        # 调用相应分析模块
        if analysis_type == "裂缝":
            res, annotated = analyze_fractures(self.image,
                                               blur_ksize=blur,
                                               canny_thresh1=thresh,
                                               canny_thresh2=thresh,
                                               min_line_length=min_val,
                                               mm_per_pixel=self.mm_per_pixel)
        elif analysis_type == "孔洞":
            res, annotated = analyze_pores(self.image,
                                           blur_ksize=blur,
                                           thresh_val=thresh,
                                           min_pore_area=min_val,
                                           mm_per_pixel=self.mm_per_pixel)
        else:  # 粒度
            res, annotated = analyze_grains(self.image,
                                            blur_ksize=blur,
                                            thresh_val=thresh,
                                            min_grain_size=min_val,
                                            mm_per_pixel=self.mm_per_pixel)
        # 在界面显示注释图像
        h, w = annotated.shape[:2]
        qimg = QImage(annotated.data, w, h, 3 * w, QImage.Format_BGR888)
        self.image_label.setPixmap(QPixmap.fromImage(qimg).scaled(400, 400, Qt.KeepAspectRatio))
        # 保存最近结果，供保存按钮使用
        self.last_result = res
        self.last_annotated = annotated
        self.last_type = analysis_type.lower()

    def save_results(self):
        if hasattr(self, 'last_result'):
            save_results(self.last_result, self.last_type, self.last_annotated)
            QMessageBox.information(self, "保存", "结果已保存。")
        else:
            QMessageBox.warning(self, "提示", "没有可保存的结果。")


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
