import sys
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import Qt, QRect, QTimer
from PyQt5.QtGui import QPainter, QPen, QColor, QBrush

class RegionSelector(QWidget):
    """全屏点击选区工具：鼠标点击位置为中心，自动框选 200x200"""
    
    def __init__(self):
        super().__init__()
        # 设置全屏、半透明、置顶
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setWindowState(Qt.WindowFullScreen)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        # 鼠标点击位置
        self.click_pos = None
        
        # 选中的区域 (x, y, width, height)，None表示未选中
        self.selected_region = None
        
        # 选框大小（固定200x200）
        self.box_size = 100

        self.is_cancelled = False
        #键盘监听
        self.setFocusPolicy(Qt.StrongFocus)

    def mousePressEvent(self, event):
        """点击鼠标：记录点击位置，计算200x200区域"""
        if event.button() == Qt.LeftButton:
            # 记录点击位置
            self.click_pos = event.pos()
            
            # 计算以点击位置为中心的 200x200 区域
            x = self.click_pos.x() - self.box_size // 2
            y = self.click_pos.y() - self.box_size // 2
            w = self.box_size
            h = self.box_size
            
            # 边界保护：防止超出屏幕
            screen_width = QApplication.primaryScreen().geometry().width()
            screen_height = QApplication.primaryScreen().geometry().height()
            
            if x < 0:
                x = 0
            if y < 0:
                y = 0
            if x + w > screen_width:
                x = screen_width - w
            if y + h > screen_height:
                y = screen_height - h
            
            self.selected_region = (x, y, w, h)
            
            # 重绘显示绿色框
            self.update()
            
            # 延迟关闭，让用户看到选中的区域
            QTimer.singleShot(500, self.close)
            
    def paintEvent(self, event):
        """绘制灰色遮罩和绿色选框"""
        painter = QPainter(self)
        
        # 1. 半透明灰色遮罩
        painter.fillRect(self.rect(), QColor(0, 0, 0, 150))
        
        # 2. 如果有点击位置，画绿色选框
        if self.click_pos is not None:
            x = self.click_pos.x() - self.box_size // 2
            y = self.click_pos.y() - self.box_size // 2
            
            # 边界保护
            screen_width = QApplication.primaryScreen().geometry().width()
            screen_height = QApplication.primaryScreen().geometry().height()
            if x < 0:
                x = 0
            if y < 0:
                y = 0
            if x + self.box_size > screen_width:
                x = screen_width - self.box_size
            if y + self.box_size > screen_height:
                y = screen_height - self.box_size
            
            rect = QRect(x, y, self.box_size, self.box_size)
            
            # 清除矩形区域的遮罩（露出底下的屏幕）
            painter.setCompositionMode(QPainter.CompositionMode_Clear)
            painter.fillRect(rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            
            # 画绿色边框
            pen = QPen(QColor(0, 255, 0), 3)
            painter.setPen(pen)
            painter.drawRect(rect)