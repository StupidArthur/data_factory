"""
数据可视化工具（PyQt6）

支持数据生成前的预览和已生成数据的展示。
支持时间窗口拖拽和缩放功能。
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Dict, List
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QFileDialog, QLabel,
                             QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox,
                             QCheckBox, QScrollArea)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor
import pyqtgraph as pg
from utils.logger import get_logger


class DataViewer(QMainWindow):
    """
    数据查看器主窗口
    
    支持：
    - 加载和显示CSV数据文件
    - 显示DataFrame数据
    - 时间窗口拖拽
    - 缩放显示
    - 多曲线显示
    """
    
    def __init__(self):
        """初始化数据查看器"""
        super().__init__()
        self.logger = get_logger()
        self.data: Optional[pd.DataFrame] = None
        self.visible_start_idx = 0
        self.visible_points = 1000  # 默认显示1000个点
        self.y_min = None  # Y轴最小值
        self.y_max = None  # Y轴最大值
        self.column_checkboxes: Dict[str, QCheckBox] = {}  # 列复选框字典
        
        self.init_ui()
    
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('数据工厂 - 数据查看器')
        self.setGeometry(100, 100, 1400, 800)
        
        # 中央部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 主布局
        main_layout = QHBoxLayout(central_widget)
        
        # 左侧控制面板
        control_panel = self.create_control_panel()
        main_layout.addWidget(control_panel, 1)
        
        # 右侧图表区域
        chart_widget = self.create_chart_widget()
        main_layout.addWidget(chart_widget, 4)
        
        # 状态栏
        self.statusBar().showMessage('就绪')
    
    def create_control_panel(self) -> QWidget:
        """创建控制面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # 文件操作组
        file_group = QGroupBox('文件操作')
        file_layout = QVBoxLayout()
        
        btn_load = QPushButton('加载CSV文件')
        btn_load.clicked.connect(self.load_csv_file)
        file_layout.addWidget(btn_load)
        
        btn_load_df = QPushButton('加载DataFrame')
        btn_load_df.clicked.connect(self.load_dataframe)
        file_layout.addWidget(btn_load_df)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 显示控制组
        display_group = QGroupBox('显示控制')
        display_layout = QVBoxLayout()
        
        # 时间窗口控制
        display_layout.addWidget(QLabel('起始索引:'))
        self.start_idx_spin = QSpinBox()
        self.start_idx_spin.setMinimum(0)
        self.start_idx_spin.setMaximum(999999)
        self.start_idx_spin.valueChanged.connect(self.on_start_idx_changed)
        display_layout.addWidget(self.start_idx_spin)
        
        display_layout.addWidget(QLabel('显示点数:'))
        self.points_spin = QSpinBox()
        self.points_spin.setMinimum(10)
        self.points_spin.setMaximum(100000)
        self.points_spin.setValue(1000)
        self.points_spin.valueChanged.connect(self.on_points_changed)
        display_layout.addWidget(self.points_spin)
        
        # 列选择（复选框）
        display_layout.addWidget(QLabel('显示列:'))
        
        # 创建滚动区域用于容纳多个复选框
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMaximumHeight(200)  # 限制最大高度
        
        # 创建复选框容器
        checkbox_container = QWidget()
        self.checkbox_layout = QVBoxLayout(checkbox_container)
        self.checkbox_layout.setContentsMargins(5, 5, 5, 5)
        
        scroll_area.setWidget(checkbox_container)
        display_layout.addWidget(scroll_area)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        # 缩放控制组
        zoom_group = QGroupBox('缩放控制')
        zoom_layout = QVBoxLayout()
        
        btn_zoom_in = QPushButton('放大 (x2)')
        btn_zoom_in.clicked.connect(self.zoom_in)
        zoom_layout.addWidget(btn_zoom_in)
        
        btn_zoom_out = QPushButton('缩小 (x0.5)')
        btn_zoom_out.clicked.connect(self.zoom_out)
        zoom_layout.addWidget(btn_zoom_out)
        
        btn_reset = QPushButton('重置视图')
        btn_reset.clicked.connect(self.reset_view)
        zoom_layout.addWidget(btn_reset)
        
        zoom_group.setLayout(zoom_layout)
        layout.addWidget(zoom_group)
        
        layout.addStretch()
        
        return panel
    
    def create_chart_widget(self) -> QWidget:
        """创建图表部件"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 创建图表
        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setLabel('left', '数值')
        self.plot_widget.setLabel('bottom', '时间索引')
        self.plot_widget.showGrid(x=True, y=True)
        self.plot_widget.setMouseEnabled(x=True, y=False)  # Y轴禁用鼠标交互，只允许X轴缩放和拖拽
        
        # 禁用Y轴自动范围调整，我们将手动设置
        self.plot_widget.enableAutoRange(axis='x')  # 只允许X轴自动范围
        self.plot_widget.enableAutoRange(axis='y', enable=False)  # 禁用Y轴自动范围
        
        layout.addWidget(self.plot_widget)
        
        return widget
    
    def load_csv_file(self):
        """加载CSV文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, '选择CSV文件', '', 'CSV Files (*.csv);;All Files (*)'
        )
        
        if file_path:
            try:
                # 先读取前两行，判断是否有描述行
                with open(file_path, 'r', encoding='utf-8') as f:
                    first_line = f.readline().strip()
                    second_line = f.readline().strip()
                
                # 判断第二行是否是描述行（通常描述行包含中文或"未知工况"等关键词）
                has_description_row = False
                if second_line:
                    # 检查第二行是否包含常见的中文描述关键词
                    description_keywords = ['时间戳', '未知工况', '描述', '说明']
                    if any(keyword in second_line for keyword in description_keywords):
                        has_description_row = True
                    # 或者检查第二行是否看起来不像数据（包含非数字字符较多）
                    elif not any(char.isdigit() for char in second_line.split(',')[0] if second_line.split(',')[0]):
                        has_description_row = True
                
                # 根据是否有描述行决定跳过行数
                skiprows = 1 if has_description_row else 0  # 跳过标题行，如果有描述行则再跳过一行
                
                # 读取CSV文件
                df = pd.read_csv(file_path, skiprows=skiprows)
                
                # 如果跳过了描述行，需要手动设置列名（从第一行读取）
                if has_description_row:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        header_line = f.readline().strip()
                        column_names = [col.strip() for col in header_line.split(',')]
                        df.columns = column_names
                
                # 检查是否有timeStamp列，如果没有，尝试解析第一列
                if 'timeStamp' not in df.columns:
                    if len(df.columns) > 0:
                        # 假设第一列是时间戳
                        first_col = df.columns[0]
                        if 'time' in first_col.lower():
                            df = df.rename(columns={first_col: 'timeStamp'})
                
                # 确保数值列的数据类型正确
                for col in df.columns:
                    if col != 'timeStamp':
                        # 尝试转换为数值类型
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                self.set_data(df)
                self.statusBar().showMessage(f'已加载文件: {Path(file_path).name} ({len(df)} 行)')
            except Exception as e:
                self.logger.error(f"加载CSV文件失败: {e}")
                import traceback
                self.logger.error(traceback.format_exc())
                self.statusBar().showMessage(f'加载失败: {str(e)}')
    
    def load_dataframe(self):
        """加载DataFrame（用于预览生成的数据）"""
        # 这个方法应该由外部调用，传入DataFrame
        self.statusBar().showMessage('请使用set_data方法设置DataFrame')
    
    def set_data(self, df: pd.DataFrame):
        """
        设置要显示的数据
        
        Args:
            df: DataFrame数据
        """
        self.data = df.copy()
        
        # 清除旧的复选框
        for checkbox in self.column_checkboxes.values():
            self.checkbox_layout.removeWidget(checkbox)
            checkbox.deleteLater()
        self.column_checkboxes.clear()
        
        # 获取数值列
        numeric_columns = self.data.select_dtypes(include=[np.number]).columns.tolist()
        # 排除timeStamp列（如果存在）
        if 'timeStamp' in numeric_columns:
            numeric_columns.remove('timeStamp')
        
        # 创建复选框
        for col in numeric_columns:
            checkbox = QCheckBox(col)
            checkbox.setChecked(False)  # 默认不选中
            checkbox.stateChanged.connect(self.on_column_checkbox_changed)
            self.column_checkboxes[col] = checkbox
            self.checkbox_layout.addWidget(checkbox)
        
        # 如果没有列，添加一个占位标签
        if len(numeric_columns) == 0:
            label = QLabel('无数值列')
            self.checkbox_layout.addWidget(label)
        
        # 计算所有数值列的最大最小值（用于Y轴范围）
        if len(numeric_columns) > 0:
            all_numeric_data = self.data[numeric_columns].values.flatten()
            all_numeric_data = all_numeric_data[~np.isnan(all_numeric_data)]  # 排除NaN
            if len(all_numeric_data) > 0:
                self.y_min = float(np.min(all_numeric_data))
                self.y_max = float(np.max(all_numeric_data))
                # 添加一些边距（5%）
                y_range = self.y_max - self.y_min
                if y_range > 0:
                    self.y_min -= y_range * 0.05
                    self.y_max += y_range * 0.05
                else:
                    # 如果数据范围很小，添加固定边距
                    self.y_min -= 1.0
                    self.y_max += 1.0
        
        # 更新索引范围
        if len(self.data) > 0:
            self.start_idx_spin.setMaximum(len(self.data) - 1)
            self.points_spin.setMaximum(len(self.data))
        
        # 重置视图
        self.reset_view()
        
        # 更新显示
        self.update_plot()
    
    def on_start_idx_changed(self, value: int):
        """起始索引改变时的回调"""
        self.visible_start_idx = value
        self.update_plot()
    
    def on_points_changed(self, value: int):
        """显示点数改变时的回调"""
        self.visible_points = value
        self.update_plot()
    
    def on_column_checkbox_changed(self):
        """列复选框状态改变时的回调"""
        self.update_plot()
    
    def update_plot(self):
        """更新图表显示"""
        if self.data is None or len(self.data) == 0:
            return
        
        # 清除现有曲线
        self.plot_widget.clear()
        
        # 获取选中的列
        selected_columns = [col for col, checkbox in self.column_checkboxes.items() 
                           if checkbox.isChecked()]
        
        if not selected_columns:
            # 如果没有选中的列，清空图表
            self.statusBar().showMessage('请选择要显示的列')
            return
        
        # 计算显示范围
        end_idx = min(self.visible_start_idx + self.visible_points, len(self.data))
        visible_data = self.data.iloc[self.visible_start_idx:end_idx]
        
        # 获取X轴数据
        x_data = np.arange(self.visible_start_idx, end_idx)
        
        # 定义颜色列表（支持多条曲线）
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray', 
                 'olive', 'cyan', 'magenta', 'yellow', 'navy', 'teal', 'coral', 'lime']
        
        # 绘制所有选中的列
        for idx, col in enumerate(selected_columns):
            y_data = visible_data[col].values
            color = colors[idx % len(colors)]  # 循环使用颜色
            pen = pg.mkPen(color=color, width=2)
            self.plot_widget.plot(x_data, y_data, pen=pen, name=col)
        
        # 设置Y轴范围为数据的最大最小值（固定Y轴范围）
        if self.y_min is not None and self.y_max is not None:
            self.plot_widget.setYRange(self.y_min, self.y_max, padding=0)
        
        # 更新状态栏
        columns_str = ', '.join(selected_columns)
        self.statusBar().showMessage(
            f'显示: {self.visible_start_idx}-{end_idx-1} ({len(visible_data)}点) | 列: {columns_str}'
        )
    
    def zoom_in(self):
        """放大视图"""
        self.visible_points = max(10, int(self.visible_points / 2))
        self.points_spin.setValue(self.visible_points)
    
    def zoom_out(self):
        """缩小视图"""
        if self.data is not None:
            max_points = len(self.data) - self.visible_start_idx
            self.visible_points = min(max_points, int(self.visible_points * 2))
            self.points_spin.setValue(self.visible_points)
    
    def reset_view(self):
        """重置视图"""
        if self.data is not None:
            self.visible_start_idx = 0
            self.visible_points = min(1000, len(self.data))
            self.start_idx_spin.setValue(0)
            self.points_spin.setValue(self.visible_points)
            # 重置Y轴范围（如果已设置）
            if self.y_min is not None and self.y_max is not None:
                self.plot_widget.setYRange(self.y_min, self.y_max, padding=0)
            self.update_plot()


def show_data_viewer(data: Optional[pd.DataFrame] = None):
    """
    显示数据查看器
    
    Args:
        data: 要显示的DataFrame（可选）
    
    Returns:
        数据查看器实例
    """
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    viewer = DataViewer()
    if data is not None:
        viewer.set_data(data)
    viewer.show()
    
    return viewer


if __name__ == '__main__':
    # 配置参数
    csv_file_path = None  # CSV文件路径（None表示不加载文件，手动选择）
    
    # 创建应用
    app = QApplication(sys.argv)
    viewer = DataViewer()
    
    # 如果指定了CSV文件路径，自动加载
    if csv_file_path:
        import pandas as pd
        try:
            df = pd.read_csv(csv_file_path, skiprows=0)
            if 'timeStamp' not in df.columns and len(df.columns) > 0:
                first_col = df.columns[0]
                if 'time' in first_col.lower():
                    df = df.rename(columns={first_col: 'timeStamp'})
            viewer.set_data(df)
        except Exception as e:
            print(f"加载CSV文件失败: {e}")
    
    # 显示窗口
    viewer.show()
    sys.exit(app.exec())

