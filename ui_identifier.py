# -*- coding: utf-8 -*-
"""
UI页面识别工具 v1
功能：截图→OCR识别→显示文字→标记页面类型→保存数据集
"""
import sys, os, time, json, cv2, numpy as np
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import easyocr

# ===== 截图模式选择 =====
# 模式1: adb_screenshot — 通过adb截取手机画面
# 模式2: screen_grab — 截取电脑屏幕指定区域
USE_MODE = 'adb_screenshot'  # adb_screenshot: adb截图 | screen_grab: 电脑截图

ADB = r'D:\MuMuPlayer\nx_main\adb.exe'
PHONE = '1aabaaeb'
DATA_FILE = os.path.join(os.path.dirname(__file__), 'ui_dataset.json')
SAVE_DIR = os.path.join(os.path.dirname(__file__), 'ui_screenshots')
LATEST_SCREENSHOT_FLAG = os.path.join(os.path.dirname(__file__), 'latest_ui_screenshot.txt')

class UIIdentWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('UI识别工具 v1')
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.resize(700, 750)

        # 数据集
        self.dataset = {}
        self.page_types = ['大厅', '选图', '匹配中', '游戏内', '结算', '加载/公告', '退出确认', '未知']
        self.current_label = '未知'
        self.load_dataset()

        # UI
        central = QWidget()
        self.setCentralWidget(central)
        vbox = QVBoxLayout(central)

        # 截图显示
        self.img_label = QLabel('点截取或按F5')
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setMinimumHeight(300)
        self.img_label.setStyleSheet('background: #1a1a1a; color: #666; border: 1px solid #333;')
        vbox.addWidget(self.img_label)

        # OCR结果
        self.text_out = QTextEdit()
        self.text_out.setReadOnly(True)
        self.text_out.setMaximumHeight(120)
        self.text_out.setStyleSheet('background: #111; color: #0f0; font: 10pt Consolas;')
        vbox.addWidget(self.text_out)

        # 页面分类按钮
        btn_layout = QHBoxLayout()
        for pt in self.page_types:
            btn = QPushButton(pt)
            btn.setStyleSheet('padding: 4px 8px;')
            btn.clicked.connect(lambda checked, t=pt: self.set_label(t))
            btn_layout.addWidget(btn)
        vbox.addLayout(btn_layout)

        # 截图区域选择
        area_layout = QHBoxLayout()
        area_layout.addWidget(QLabel('截图区域:'))
        self.area_btn = QPushButton('🖱 框选区域')
        self.area_btn.clicked.connect(self.select_area)
        self.area_btn.setStyleSheet('padding: 4px;')
        area_layout.addWidget(self.area_btn)
        self.area_label = QLabel('全屏')
        self.area_label.setStyleSheet('color: #888;')
        area_layout.addWidget(self.area_label)
        area_layout.addStretch()
        vbox.addLayout(area_layout)

        # 操作按钮
        op_layout = QHBoxLayout()

        self.cap_btn = QPushButton('📷 截图 (F5)')
        self.cap_btn.clicked.connect(self.capture)
        self.cap_btn.setStyleSheet('padding: 6px; font-size: 12pt;')
        op_layout.addWidget(self.cap_btn)

        self.save_btn = QPushButton('💾 保存标记')
        self.save_btn.clicked.connect(self.save_label)
        op_layout.addWidget(self.save_btn)

        self.copy_btn = QPushButton('📋 复制文字')
        self.copy_btn.clicked.connect(self.copy_text)
        self.copy_btn.setStyleSheet('padding: 6px;')
        op_layout.addWidget(self.copy_btn)

        self.auto_btn = QPushButton('▶ 连续识别')
        self.auto_btn.setCheckable(True)
        self.auto_btn.clicked.connect(self.toggle_auto)
        self.auto_btn.setStyleSheet('padding: 6px;')
        op_layout.addWidget(self.auto_btn)

        vbox.addLayout(op_layout)

        # 统计
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage('就绪 | 数据集: {} 条'.format(len(self.dataset)))

        # 快捷键
        self.shortcut_cap = QShortcut(QKeySequence('F5'), self)
        self.shortcut_cap.activated.connect(self.capture)
        self.shortcut_save = QShortcut(QKeySequence('Ctrl+S'), self)
        self.shortcut_save.activated.connect(self.save_label)

        # 截图区域
        self.crop_rect = None  # (x, y, w, h)

        # 定时器
        self.timer = QTimer()
        self.timer.timeout.connect(self.capture)
        self.auto_mode = False

        # OCR
        self.reader = None
        self.last_img = None

    def load_dataset(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                self.dataset = json.load(f)

    def save_dataset(self):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.dataset, f, ensure_ascii=False, indent=2)

    def set_label(self, label):
        self.current_label = label
        self.status_bar.showMessage(f'当前标记: {label} | 数据集: {len(self.dataset)} 条')

    def capture(self):
        self.status_bar.showMessage('截图...')
        QApplication.processEvents()

        try:
            if USE_MODE == 'screen_grab':
                from PIL import ImageGrab
                if self.crop_rect:
                    x, y, w, h = self.crop_rect
                    pil_img = ImageGrab.grab(bbox=(x, y, x+w, y+h))
                else:
                    pil_img = ImageGrab.grab()
                img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
            else:
                import subprocess
                r = subprocess.run([ADB, '-s', PHONE, 'exec-out', 'screencap', '-p'],
                                capture_output=True, timeout=15)
                img = cv2.imdecode(np.frombuffer(r.stdout, np.uint8), cv2.IMREAD_COLOR)
                if img is None:
                    self.text_out.setText('截图失败：图片为空')
                    self.status_bar.showMessage('截图失败')
                    return
                if img.shape[0] > img.shape[1]:
                    img = cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE)
            self.last_img = img
        except Exception as e:
            self.text_out.setText(f'截图异常: {e}')
            self.status_bar.showMessage(f'截图失败: {e}')
            return

        # 显示缩略图
        h, w = img.shape[:2]
        max_h, max_w = 500, 600
        scale = min(max_w/w, max_h/h, 1.0)
        disp = cv2.resize(img, (int(w*scale), int(h*scale)))
        h2, w2 = disp.shape[:2]
        qimg = QImage(disp.data, w2, h2, disp.strides[0], QImage.Format_RGB888).rgbSwapped()
        pix = QPixmap.fromImage(qimg)
        self.img_label.setPixmap(pix)
        self.img_label.setFixedSize(w2, h2)

        # 自动保存截图并通知（用英文文件名避免编码问题）
        os.makedirs(SAVE_DIR, exist_ok=True)
        ts = time.strftime('%Y%m%d_%H%M%S')
        fname = f'screenshot_{ts}.png'
        save_path = os.path.join(SAVE_DIR, fname)
        success = cv2.imwrite(save_path, self.last_img)
        with open(LATEST_SCREENSHOT_FLAG, 'w', encoding='utf-8') as f:
            f.write(save_path)
        if success:
            self.status_bar.showMessage(f'已自动保存: {fname}')
        else:
            self.status_bar.showMessage(f'保存失败！检查路径权限')

        # OCR识别（后台线程加载，不阻塞截图保存）
        self.status_bar.showMessage('OCR识别...')
        QApplication.processEvents()
        if self.reader is not None:
            try:
                self._run_ocr(img)
            except Exception as e:
                self.text_out.setText(f'OCR异常: {e}')
        else:
            self.text_out.setText('OCR加载中，稍后自动识别...')
            # 后台加载OCR
            def load_ocr():
                try:
                    self.reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
                    self._run_ocr(self.last_img)
                except Exception as e:
                    self.text_out.setText(f'OCR加载失败: {e}')
            QTimer.singleShot(100, load_ocr)

    def _run_ocr(self, img):
        results = self.reader.readtext(img, paragraph=False)
        lines = []
        for bbox, text, conf in results:
            if conf > 0.3:
                cx = int((bbox[0][0] + bbox[2][0]) / 2)
                cy = int((bbox[0][1] + bbox[2][1]) / 2)
                lines.append(f'{text} ({cx},{cy}) [{conf:.2f}]')

        brightness = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).mean()
        h, w = img.shape[:2]
        header = f'分辨率: {w}x{h} | 亮度: {brightness:.0f}\n'
        header += f'标记: {self.current_label} | 文字: {len(lines)} 个\n'
        header += '-'*40

        self.text_out.setText(header + '\n' + '\n'.join(lines))
        self.status_bar.showMessage(f'识别完成 | {len(lines)} 文字 | 标记: {self.current_label}')

        # 自动匹配已知页面
        best_page, best_score = self.match_page(lines)
        if best_score > 0:
            self.current_label = best_page
            self.status_bar.showMessage(f'自动匹配: {best_page} ({best_score:.2f})')

    def match_page(self, lines):
        """根据识别文字匹配页面类型"""
        all_text = ' '.join([l.split(' (')[0] for l in lines])
        scores = {}
        for label, samples in self.dataset.items():
            keywords = samples.get('keywords', [])
            score = sum(1 for kw in keywords if kw in all_text)
            if score > 0:
                scores[label] = score / len(keywords) if keywords else 0

        page_rules = {
            '大厅': ['藏品', '市场', '商城', '出发', '仓库'],
            '选图': ['零号大坝', '长弓溪谷', '航天基地', '战略板'],
            '匹配中': ['取消行动'],
            '结算': ['致命一击', '下一步', '战报', '淘汰回放'],
            '退出确认': ['确定退出', '取消', '确认'],
            '游戏内': []  # 很难纯文字判断
        }
        for label, keywords in page_rules.items():
            score = sum(1 for kw in keywords if kw in all_text)
            if score > 0:
                if label not in scores or score > scores[label]:
                    scores[label] = score

        if scores:
            best = max(scores, key=scores.get)
            return best, scores[best]
        return '', 0

    def save_label(self):
        if self.last_img is None:
            self.status_bar.showMessage('没截图可保存')
            return

        os.makedirs(SAVE_DIR, exist_ok=True)

        # OCR文字作为关键词
        current_texts = self.text_out.toPlainText()
        keywords = []
        for line in current_texts.split('\n'):
            if ' (' in line:
                text = line.split(' (')[0]
                if text and len(text) > 1:
                    keywords.append(text)

        ts = time.strftime('%Y%m%d_%H%M%S')
        fname = f'{ts}_{self.current_label}.png'
        cv2.imwrite(os.path.join(SAVE_DIR, fname), self.last_img)

        if self.current_label not in self.dataset:
            self.dataset[self.current_label] = {'count': 0, 'keywords': [], 'files': []}
        self.dataset[self.current_label]['count'] += 1
        # 合并关键词
        existing_kw = set(self.dataset[self.current_label]['keywords'])
        existing_kw.update(keywords)
        self.dataset[self.current_label]['keywords'] = list(existing_kw)
        self.dataset[self.current_label]['files'].append(fname)
        self.save_dataset()

        # 通知外部：最新截图已保存
        full_path = os.path.join(SAVE_DIR, fname)
        with open(LATEST_SCREENSHOT_FLAG, 'w', encoding='utf-8') as f:
            f.write(full_path)

        self.status_bar.showMessage(f'已保存: {fname} | 总数据集: {sum(d["count"] for d in self.dataset.values())} 条')

    def copy_text(self):
        text = self.text_out.toPlainText()
        cb = QApplication.clipboard()
        cb.setText(text)
        self.status_bar.showMessage('已复制到剪贴板')

    def toggle_auto(self):
        self.auto_mode = self.auto_btn.isChecked()
        if self.auto_mode:
            self.auto_btn.setText('⏹ 停止')
            self.timer.start(5000)  # 5秒一次
            self.status_bar.showMessage('连续识别中 (每5秒)...')
        else:
            self.auto_btn.setText('▶ 连续识别')
            self.timer.stop()
            self.status_bar.showMessage('停止连续识别')

    def select_area(self):
        """隐藏窗口，框选截图区域"""
        self.hide()
        time.sleep(0.3)

        # 用PIL截全屏
        from PIL import ImageGrab
        full = ImageGrab.grab()
        sw, sh = full.size

        # 用一个全屏半透明窗口让用户框选
        self.overlay = QDialog()
        self.overlay.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.overlay.setAttribute(Qt.WA_TranslucentBackground)
        self.overlay.setGeometry(0, 0, sw, sh)

        class OverlayWidget(QWidget):
            def __init__(self, parent):
                super().__init__(parent)
                self.start = None
                self.end = None
                self.drawing = False

            def paintEvent(self, e):
                p = QPainter(self)
                # 半透明灰色遮罩
                p.fillRect(self.rect(), QColor(0, 0, 0, 120))
                if self.start and self.end:
                    x = min(self.start.x(), self.end.x())
                    y = min(self.start.y(), self.end.y())
                    w = abs(self.end.x() - self.start.x())
                    h = abs(self.end.y() - self.start.y())
                    # 透明矩形(显示截图)
                    p.setCompositionMode(QPainter.CompositionMode_Clear)
                    p.fillRect(x, y, w, h, Qt.transparent)
                    p.setCompositionMode(QPainter.CompositionMode_SourceOver)
                    # 边框
                    p.setPen(QPen(QColor(0, 255, 0), 3))
                    p.drawRect(x, y, w, h)
                    p.setPen(QColor(255, 255, 255))
                    p.drawText(x+5, y-10, f'{w}x{h}')
                    p.setPen(Qt.NoPen)

            def mousePressEvent(self, e):
                self.start = e.pos()
                self.end = e.pos()
                self.drawing = True
                self.update()

            def mouseMoveEvent(self, e):
                if self.drawing:
                    self.end = e.pos()
                    self.update()

            def mouseReleaseEvent(self, e):
                self.drawing = False
                self.end = e.pos()
                x = min(self.start.x(), self.end.x())
                y = min(self.start.y(), self.end.y())
                w = abs(self.end.x() - self.start.x())
                h = abs(self.end.y() - self.start.y())
                if w > 10 and h > 10:
                    self.parent().crop_rect = (x, y, w, h)
                self.parent().overlay.accept()

        overlay_widget = OverlayWidget(self.overlay)
        self.overlay.setLayout(QVBoxLayout())
        self.overlay.layout().addWidget(overlay_widget)
        self.overlay.exec_()
        self.overlay = None

        if self.crop_rect:
            x, y, w, h = self.crop_rect
            self.area_label.setText(f'{w}x{h} @ ({x},{y})')
            self.status_bar.showMessage(f'截图区域: ({x},{y}) {w}x{h}')
        else:
            self.area_label.setText('全屏')

        self.show()
        self.raise_()
        self.activateWindow()

def main():
    import subprocess
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    win = UIIdentWindow()
    win.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
