import time
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import QTime,QTimer,Qt
from fishing_ui import Ui_Form  # 导入你刚转换的 UI 类
import pyautogui
import numpy as np
from region_selector import RegionSelector
import cv2
import ctypes

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004

def hardware_click():
    """硬件级鼠标左键点击（游戏里也能用）"""
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.02)
    ctypes.windll.user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # 加载 UI
        self.ui = Ui_Form()
        self.ui.setupUi(self)


        # 浮标区域（默认值，后面会被用户选择覆盖）
        self.region = None
        self.isfishing = False
        self.prev_frame = None

        # ===== 检测参数 =====
        self.movement_threshold = 30
        self.sensitivity = 10

        # 连接"选择区域"按钮
        self.ui.ChooseRegion.clicked.connect(self.select_region)
        self.ui.FishingButtom.clicked.connect(self.start_fishing)
        # 初始禁用"开始钓鱼"
        self.ui.FishingButtom.setEnabled(False)

        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        self.preview_timer.start(100)  # 每100ms刷新一次
    
        self.setFocusPolicy(Qt.StrongFocus)

    def keyPressEvent(self, event):
        """按 N 取消已选择的区域"""
        if event.key() == Qt.Key_N:
            if self.region is not None:
                self.region = None
                self.ui.FishingButtom.setEnabled(False)
                self.ui.Region.setText("已取消选择")
                self.ui.ChooseRegion.setEnabled(True)  # 重新启用"选择区域"按钮
                self.isfishing = False
                print("已取消选择区域")
            else:
                print("当前没有已选择的区域")
    def start_fishing(self):
        """点击"开始钓鱼"：开始检测浮标"""
        if not self.isfishing:
            self.isfishing = True
            self.ui.ChooseRegion.setEnabled(False)
            self.prev_frame = None
            print("开始钓鱼！")

    def select_region(self):
        """点击"选择区域"按钮：打开全屏选区工具"""
        
        # 创建选区窗口
        self.selector = RegionSelector()
        self.selector.showFullScreen()
        
        # 等待选区窗口关闭，然后获取结果
        # 用一个定时器不断检查选区窗口是否已关闭
        self.check_timer = QTimer()
        self.check_timer.timeout.connect(self.check_selector_closed)
        self.check_timer.start(200)  # 每200ms检查一次
    def check_selector_closed(self):
        """检查选区窗口是否已关闭"""
        if not hasattr(self, 'selector'):
            return
        
        # 如果选区窗口已关闭
        if not self.selector.isVisible():
            self.check_timer.stop()
            
            # 获取选中的区域
            region = self.selector.selected_region

            is_cancelled = hasattr(self.selector, 'is_cancelled') and self.selector.is_cancelled

            self.selector = None
            
            # 恢复主窗口
            self.showNormal()
            self.raise_()

            if is_cancelled:
                self.region = None
                self.ui.FishingButtom.setEnabled(False)
                self.ui.Region.setText("已取消选择")
                print("已取消选择")
                return

            if region is not None:
                self.region = region
                print(f"已选择区域: {region}")
                self.ui.FishingButtom.setEnabled(True)
                self.ui.ChooseRegion.setEnabled(False)
                # 截取该区域的图片显示到预览框
                self.update_preview()
            else:
                print("未选择有效区域")
    def update_preview(self):
        """截取选定区域并显示到预览框"""
        if self.region is None:
            return
        
        x, y, w, h = self.region
        screenshot = pyautogui.screenshot(region=(x, y, w, h))
        
        # 转换为 QPixmap
        img_np = np.array(screenshot)
        height, width, channel = img_np.shape
        bytes_per_line = 3 * width
        qimage = QImage(img_np.data, width, height, bytes_per_line, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimage)
        
        # 缩放到预览框大小
        scaled = pixmap.scaled(400, 400, aspectRatioMode=1)
        self.ui.Region.setPixmap(scaled)


        # ---- 2. 如果正在钓鱼，做检测 ----
        if not self.isfishing:
            return

        # 转灰度图
        gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)

        # 第一帧只记录
        if self.prev_frame is None:
            self.prev_frame = gray
            return

        # 计算变化
        diff = cv2.absdiff(self.prev_frame, gray)
        _, thresh = cv2.threshold(diff, self.movement_threshold, 255, cv2.THRESH_BINARY)

        total_pixels = w * h
        changed_pixels = np.sum(thresh > 0)
        change_ratio = (changed_pixels / total_pixels) * 100

        self.prev_frame = gray

        # 判断上钩
        if change_ratio > self.sensitivity:
            print(f"上钩！变化率: {change_ratio:.1f}% ")
            self.prev_frame = None  # 重置，防止连续触发
                    # ---- 4. 执行点击收竿 + 抛竿 ----
            print(" 点击收竿...")
            hardware_click()  # 第一次点击（收竿）
            time.sleep(0.7)    # 等待收竿动画
            print(" 点击抛竿...")
            hardware_click()  # 第二次点击（抛竿）

            # ---- 5. 重置上一帧，延迟1秒再继续检测 ----
            self.prev_frame = None
            print(" 等待1秒后继续检测...")
            time.sleep(1)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())