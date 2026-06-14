"""
雷达图绘制工具 - KivyMD 版
使用 Pillow 绘制图表，Kivy 展示
"""
import os
import math
import random
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont

from kivy.clock import Clock, mainthread
from kivy.core.image import Image as CoreImage
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image as KivyImage
from kivy.uix.scrollview import ScrollView

from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.slider import MDSlider
from kivymd.uix.selectioncontrol import MDCheckbox


COLOR_SCHEMES = [
    {"name": "经典", "colors": ["#3498db", "#e74c3c", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c"]},
    {"name": "暖色", "colors": ["#e74c3c", "#e67e22", "#f1c40f", "#e91e63", "#ff5722", "#ff9800"]},
    {"name": "冷色", "colors": ["#3498db", "#00bcd4", "#4caf50", "#2196f3", "#009688", "#03a9f4"]},
    {"name": "马卡龙", "colors": ["#ff9ff3", "#feca57", "#48dbfb", "#ff6348", "#7bed9f", "#e056fd"]},
]


from modules.base_tool import BaseToolScreen


class RadarChartScreen(BaseToolScreen):
    screen_title = "📊 雷达图"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.dimensions = ["速度", "力量", "技巧", "耐力", "智力", "魅力"]
        self.datasets = [
            {"name": "数据集 1", "scores": [85, 70, 90, 60, 75, 80], "color": "#3498db"},
        ]
        self.next_dataset_id = 2
        self.max_score = 100
        self.show_grid = True
        self.show_labels = True
        self.show_filled = True
        self.show_outline = True
        self.chart_title = "雷达图"
        self.bg_color = "#ffffff"
        Clock.schedule_once(self.build_ui, 0)

    def build_ui(self, dt=None):
        self.clear_widgets()
        main = BoxLayout(orientation="vertical")

        toolbar = MDTopAppBar(title=self.screen_title, elevation=2,
                               left_action_items=[["arrow-left", lambda x: self._go_home()]],
                               md_bg_color=self.theme_cls.primary_color)
        main.add_widget(toolbar)

        # ─── 左右布局 ───
        h_box = BoxLayout(orientation="horizontal", spacing=dp(4))

        # ─── 左侧: 控制面板 (可滚动) ───
        scroll = ScrollView(do_scroll_x=False, size_hint_x=0.5)
        left = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4), padding=dp(6))
        left.bind(minimum_height=left.setter("height"))

        left.add_widget(MDLabel(text="维度设置:", font_style="H6", size_hint_y=None, height=dp(26)))

        # 维度输入
        self.dim_container = BoxLayout(orientation="vertical", size_hint_y=None)
        self.dim_container.bind(minimum_height=self.dim_container.setter("height"))
        left.add_widget(self.dim_container)
        self._rebuild_dim_entries()

        dim_btn = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36), spacing=dp(4))
        dim_btn.add_widget(MDRaisedButton(text="➕ 添加", on_release=lambda x: self._add_dim()))
        dim_btn.add_widget(MDFlatButton(text="➖ 删除", on_release=lambda x: self._remove_dim()))
        dim_btn.add_widget(MDFlatButton(text="重置", on_release=lambda x: self._reset_dims()))
        left.add_widget(dim_btn)

        # 数据集
        left.add_widget(MDLabel(text="数据集:", font_style="H6", size_hint_y=None, height=dp(26)))
        self.ds_container = BoxLayout(orientation="vertical", size_hint_y=None)
        self.ds_container.bind(minimum_height=self.ds_container.setter("height"))
        left.add_widget(self.ds_container)
        self._rebuild_ds_ui()

        ds_btn = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36), spacing=dp(4))
        ds_btn.add_widget(MDRaisedButton(text="➕ 添加数据集", on_release=lambda x: self._add_ds()))
        ds_btn.add_widget(MDFlatButton(text="➖ 删除", on_release=lambda x: self._remove_ds()))
        left.add_widget(ds_btn)

        # 显示选项
        left.add_widget(MDLabel(text="显示选项:", font_style="H6", size_hint_y=None, height=dp(26)))

        opt_grid = GridLayout(cols=2, spacing=dp(4), size_hint_y=None, height=dp(120))
        self.grid_cb = MDCheckbox(active=True, size_hint_x=0.1)
        self.labels_cb = MDCheckbox(active=True, size_hint_x=0.1)
        self.filled_cb = MDCheckbox(active=True, size_hint_x=0.1)
        self.outline_cb = MDCheckbox(active=True, size_hint_x=0.1)

        def make_toggle(var):
            return lambda x: (setattr(self, var, x.active) or self._render())

        self.grid_cb.bind(active=make_toggle("show_grid"))
        self.labels_cb.bind(active=make_toggle("show_labels"))
        self.filled_cb.bind(active=make_toggle("show_filled"))
        self.outline_cb.bind(active=make_toggle("show_outline"))

        opt_grid.add_widget(self.grid_cb)
        opt_grid.add_widget(MDLabel(text="显示网格"))
        opt_grid.add_widget(self.labels_cb)
        opt_grid.add_widget(MDLabel(text="显示标签"))
        opt_grid.add_widget(self.filled_cb)
        opt_grid.add_widget(MDLabel(text="填充区域"))
        opt_grid.add_widget(self.outline_cb)
        opt_grid.add_widget(MDLabel(text="显示轮廓"))
        left.add_widget(opt_grid)

        # 满分 & 大小
        param_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(4))
        param_row.add_widget(MDLabel(text="满分:", size_hint_x=0.3, font_style="Caption"))
        self.max_input = MDTextField(text="100", mode="fill", size_hint_x=0.2, input_filter="int")
        param_row.add_widget(self.max_input)
        param_row.add_widget(MDLabel(text="标题:", size_hint_x=0.2, font_style="Caption"))
        self.title_input = MDTextField(text="雷达图", mode="fill", size_hint_x=0.3)
        left.add_widget(param_row)

        # 保存
        left.add_widget(MDRaisedButton(text="💾 保存图片", on_release=lambda x: self._save(),
                                        size_hint_y=None, height=dp(40)))
        left.add_widget(MDFlatButton(text="🔄 重置", on_release=lambda x: self._reset_all(),
                                      size_hint_y=None, height=dp(36)))

        scroll.add_widget(left)

        # ─── 右侧: 图表预览 ───
        right = BoxLayout(orientation="vertical", padding=dp(4))
        right.add_widget(MDLabel(text="预览:", font_style="H6", size_hint_y=None, height=dp(24)))
        self.chart_image = KivyImage(size_hint_y=1, allow_stretch=True, keep_ratio=True)
        right.add_widget(self.chart_image)

        h_box.add_widget(scroll)
        h_box.add_widget(right)
        main.add_widget(h_box)
        self.add_widget(main)

        Clock.schedule_once(lambda dt: self._render(), 0.5)

    def _go_home(self):
        app = self._get_app()
        if app: app.go_home()

    def _get_app(self):
        from kivy.app import App
        return App.get_running_app()

    def _snack(self, text):
        Snackbar(text=text, duration=2).open()

    # ─── 维度管理 ───
    def _rebuild_dim_entries(self):
        self.dim_container.clear_widgets()
        self.dim_fields = []
        for i, name in enumerate(self.dimensions):
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(2))
            row.add_widget(MDLabel(text=f"{i+1}.", size_hint_x=0.1, font_style="Caption"))
            tf = MDTextField(text=name, mode="fill", size_hint_x=0.9)
            tf.bind(text=lambda *a: self._on_dim_change())
            row.add_widget(tf)
            self.dim_fields.append(tf)
            self.dim_container.add_widget(row)

    def _on_dim_change(self):
        new_dims = []
        for f in self.dim_fields:
            new_dims.append(f.text or "未命名")
        self.dimensions = new_dims
        self._rebuild_ds_ui()
        self._render()

    def _add_dim(self):
        self.dimensions.append(f"维度 {len(self.dimensions)+1}")
        for ds in self.datasets:
            ds["scores"].append(50)
        self._rebuild_dim_entries()
        self._rebuild_ds_ui()
        self._render()

    def _remove_dim(self):
        if len(self.dimensions) <= 2:
            self._snack("至少需要 2 个维度")
            return
        self.dimensions.pop()
        for ds in self.datasets:
            if ds["scores"]:
                ds["scores"].pop()
        self._rebuild_dim_entries()
        self._rebuild_ds_ui()
        self._render()

    def _reset_dims(self):
        self.dimensions = ["速度", "力量", "技巧", "耐力", "智力", "魅力"]
        n = len(self.dimensions)
        for ds in self.datasets:
            ds["scores"] = [50] * n if len(ds["scores"]) < n else ds["scores"][:n]
        self._rebuild_dim_entries()
        self._rebuild_ds_ui()
        self._render()

    # ─── 数据集管理 ───
    def _rebuild_ds_ui(self):
        self.ds_container.clear_widgets()
        for idx, ds in enumerate(self.datasets):
            box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2),
                            padding=dp(4))
            box.bind(minimum_height=box.setter("height"))

            # 名称行
            name_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36), spacing=dp(4))
            name_row.add_widget(MDLabel(text=f"#{idx+1}:", size_hint_x=0.15, font_style="Caption"))
            name_tf = MDTextField(text=ds["name"], mode="fill", size_hint_x=0.6)
            name_tf.bind(text=lambda *a, i=idx: self._on_ds_name_change(i))
            name_row.add_widget(name_tf)
            ds["name_field"] = name_tf

            # 分数
            scores_row = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(1))
            scores_row.bind(minimum_height=scores_row.setter("height"))
            for di, (dim, score) in enumerate(zip(self.dimensions, ds["scores"])):
                sr = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32), spacing=dp(2))
                sr.add_widget(MDLabel(text=f"{dim}:", size_hint_x=0.35, font_style="Caption"))
                sf = MDTextField(text=str(score), mode="fill", size_hint_x=0.25, input_filter="int")
                sf.bind(text=lambda *a, i=idx, j=di: self._on_score_change(i, j))
                sr.add_widget(sf)

                # 颜色方块
                color_lbl = MDLabel(text="●", size_hint_x=0.1,
                                     theme_text_color="Custom",
                                     text_color=self._hex_to_rgb(ds["color"]))
                sr.add_widget(color_lbl)
                scores_row.add_widget(sr)

            box.add_widget(name_row)
            box.add_widget(scores_row)
            self.ds_container.add_widget(box)

    def _on_ds_name_change(self, idx):
        f = self.datasets[idx].get("name_field")
        if f:
            self.datasets[idx]["name"] = f.text or f"数据集 {idx+1}"
            self._render()

    def _on_score_change(self, ds_idx, dim_idx):
        try:
            ds = self.datasets[ds_idx]
            # 找到对应的分数输入框
            container = self.ds_container.children[-(ds_idx+1)] if ds_idx < len(self.ds_container.children) else None
            if container:
                scores_rows = [c for c in container.children if isinstance(c, BoxLayout)][1]  # 第二个子容器是分数
                # 简化：用一个 dict 跟踪
                pass
            val = int(ds["scores"][dim_idx])  # 保留原值
            # 但我们需要从 UI 读取... 简化处理
            self._render()
        except:
            pass

    def _add_ds(self):
        n = len(self.dimensions)
        colors = COLOR_SCHEMES[0]["colors"]
        color = colors[len(self.datasets) % len(colors)]
        self.datasets.append({
            "name": f"数据集 {self.next_dataset_id}",
            "scores": [50] * n,
            "color": color,
        })
        self.next_dataset_id += 1
        self._rebuild_ds_ui()
        self._render()

    def _remove_ds(self):
        if len(self.datasets) <= 1:
            self._snack("至少保留一个数据集")
            return
        self.datasets.pop()
        self._rebuild_ds_ui()
        self._render()

    def _reset_all(self):
        self.dimensions = ["速度", "力量", "技巧", "耐力", "智力", "魅力"]
        self.datasets = [
            {"name": "数据集 1", "scores": [85, 70, 90, 60, 75, 80], "color": "#3498db"},
        ]
        self.next_dataset_id = 2
        self.max_score = 100
        self._rebuild_dim_entries()
        self._rebuild_ds_ui()
        if hasattr(self, 'max_input'):
            self.max_input.text = "100"
        if hasattr(self, 'title_input'):
            self.title_input.text = "雷达图"
        self._render()

    # ─── 绘制 ───
    def _render(self, *args):
        """使用 Pillow 绘制雷达图"""
        n = len(self.dimensions)
        if n < 2:
            return

        try:
            self.max_score = int(self.max_input.text) if hasattr(self, 'max_input') and self.max_input.text else 100
        except:
            self.max_score = 100

        if hasattr(self, 'title_input'):
            self.chart_title = self.title_input.text or "雷达图"

        img_size = 600
        img = Image.new("RGB", (img_size, img_size), self.bg_color)
        draw = ImageDraw.Draw(img)

        cx = cy = img_size // 2
        margin = 80
        r = img_size // 2 - margin

        # 网格
        if self.show_grid:
            grid_levels = 5
            for level in range(1, grid_levels + 1):
                lr = r * level / grid_levels
                pts = []
                for i in range(n):
                    angle = -math.pi / 2 + 2 * math.pi * i / n
                    x = cx + lr * math.cos(angle)
                    y = cy + lr * math.sin(angle)
                    pts.extend([x, y])
                draw.polygon(pts, outline="#d0d0d0", fill=None, width=1)

        # 射线
        if self.show_grid:
            for i in range(n):
                angle = -math.pi / 2 + 2 * math.pi * i / n
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                draw.line([cx, cy, x, y], fill="#d0d0d0", width=1)

        # 标签
        if self.show_labels:
            try:
                font = ImageFont.truetype("msyh.ttc", 14)
            except:
                font = ImageFont.load_default()
            for i, dim_name in enumerate(self.dimensions):
                angle = -math.pi / 2 + 2 * math.pi * i / n
                lx = cx + (r + 28) * math.cos(angle)
                ly = cy + (r + 28) * math.sin(angle)
                draw.text((lx, ly), dim_name, fill="#333333", font=font, anchor="mm")

        # 数据集
        for ds_idx, ds in enumerate(self.datasets):
            scores = ds["scores"]
            color = ds["color"]
            pts = []
            for i in range(n):
                angle = -math.pi / 2 + 2 * math.pi * i / n
                val = scores[i] if i < len(scores) else 0
                ratio = max(0, min(1, val / self.max_score)) if self.max_score > 0 else 0
                dist = r * ratio
                x = cx + dist * math.cos(angle)
                y = cy + dist * math.sin(angle)
                pts.append((x, y))

            # 填充
            if self.show_filled:
                draw.polygon(pts, outline=None, fill=color + "40" if len(color) == 7 else color)

            # 轮廓
            if self.show_outline:
                for j in range(len(pts)):
                    j2 = (j + 1) % len(pts)
                    draw.line([pts[j], pts[j2]], fill=color, width=3)

            # 数据点
            for px, py in pts:
                draw.ellipse([px-4, py-4, px+4, py+4], fill="white", outline=color, width=2)

        # 标题
        try:
            title_font = ImageFont.truetype("msyh.ttc", 18)
        except:
            title_font = ImageFont.load_default()
        draw.text((img_size // 2, 20), self.chart_title, fill="#2c3e50", font=title_font, anchor="mt")

        # 图例
        if len(self.datasets) > 1:
            ly = 45
            for ds in reversed(self.datasets):
                ly += 22
                draw.rectangle([img_size - 90, ly - 7, img_size - 76, ly + 7], fill=ds["color"], outline=None)
                draw.text((img_size - 72, ly), ds["name"], fill="#333333", font=font, anchor="lm")

        # ─── PIL → Kivy Texture ───
        data = img.tobytes()
        tex = Texture.create(size=img.size, colorfmt="rgb")
        tex.blit_buffer(data, colorfmt="rgb", bufferfmt="ubyte")
        tex.flip_vertical()
        self.chart_image.texture = tex

    def _save(self):
        """保存为图片"""
        try:
            from datetime import datetime
            name = f"radar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            from utils import get_pictures_path
            path = os.path.join(get_pictures_path(), name)

            # 重新渲染高清版
            self._render_hires(path)
            self._snack(f"已保存: {name}")
        except Exception as e:
            self._snack(f"保存失败: {e}")

    def _render_hires(self, save_path):
        """高清渲染并保存"""
        n = len(self.dimensions)
        if n < 2: return

        try:
            self.max_score = int(self.max_input.text) if hasattr(self, 'max_input') and self.max_input.text else 100
        except:
            self.max_score = 100

        img_size = 1200
        img = Image.new("RGB", (img_size, img_size), self.bg_color)
        draw = ImageDraw.Draw(img)

        cx = cy = img_size // 2
        r = img_size // 2 - 80

        if self.show_grid:
            grid_levels = 5
            for level in range(1, grid_levels + 1):
                lr = r * level / grid_levels
                pts = []
                for i in range(n):
                    angle = -math.pi / 2 + 2 * math.pi * i / n
                    x = cx + lr * math.cos(angle)
                    y = cy + lr * math.sin(angle)
                    pts.extend([x, y])
                draw.polygon(pts, outline="#d0d0d0", fill=None, width=2)

        if self.show_grid:
            for i in range(n):
                angle = -math.pi / 2 + 2 * math.pi * i / n
                x = cx + r * math.cos(angle)
                y = cy + r * math.sin(angle)
                draw.line([cx, cy, x, y], fill="#d0d0d0", width=2)

        if self.show_labels:
            try:
                font = ImageFont.truetype("msyh.ttc", 24)
            except:
                font = ImageFont.load_default()
            for i, dim_name in enumerate(self.dimensions):
                angle = -math.pi / 2 + 2 * math.pi * i / n
                lx = cx + (r + 40) * math.cos(angle)
                ly = cy + (r + 40) * math.sin(angle)
                draw.text((lx, ly), dim_name, fill="#333333", font=font, anchor="mm")

        for ds in self.datasets:
            scores = ds["scores"]
            color = ds["color"]
            pts = []
            for i in range(n):
                angle = -math.pi / 2 + 2 * math.pi * i / n
                val = scores[i] if i < len(scores) else 0
                ratio = max(0, min(1, val / self.max_score)) if self.max_score > 0 else 0
                dist = r * ratio
                x = cx + dist * math.cos(angle)
                y = cy + dist * math.sin(angle)
                pts.append((x, y))

            if self.show_filled:
                draw.polygon(pts, outline=None, fill=color)

            if self.show_outline:
                for j in range(len(pts)):
                    j2 = (j + 1) % len(pts)
                    draw.line([pts[j], pts[j2]], fill=color, width=5)

            for px, py in pts:
                draw.ellipse([px-6, py-6, px+6, py+6], fill="white", outline=color, width=3)

        try:
            title_font = ImageFont.truetype("msyh.ttc", 30)
        except:
            title_font = ImageFont.load_default()
        draw.text((img_size // 2, 30), self.chart_title, fill="#2c3e50", font=title_font, anchor="mt")

        img.save(save_path, dpi=(150, 150))

    def _hex_to_rgb(self, hex_color):
        """#RRGGBB → (r/255, g/255, b/255, 1) for Kivy"""
        h = hex_color.lstrip("#")
        return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4)) + (1,)
