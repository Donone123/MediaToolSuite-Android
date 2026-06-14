"""
多图拼接工具 - KivyMD 版
通过滑杆调节每张图的显示区域，合并为一张图
"""
import os
from PIL import Image

from kivy.clock import Clock
from kivy.core.image import Image as CoreImage
from kivy.graphics import Color, Rectangle
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image as KivyImage
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider

from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.slider import MDSlider
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.toolbar import MDTopAppBar


from modules.base_tool import BaseToolScreen


class ImageStitchScreen(BaseToolScreen):
    screen_title = "🧩 图片拼接"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.images = []       # PIL Image 列表
        self.paths = []
        self.slider_values = []  # [0-100]
        self.preview_texture = None
        self.dir_var = "horizontal"  # 方向
        Clock.schedule_once(self.build_ui, 0)

    def build_ui(self, dt=None):
        self.clear_widgets()
        main = BoxLayout(orientation="vertical")

        toolbar = MDTopAppBar(title=self.screen_title, elevation=2,
                               left_action_items=[["arrow-left", lambda x: self._go_home()]],
                               md_bg_color=self.theme_cls.primary_color)
        main.add_widget(toolbar)

        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=dp(12))
        content.bind(minimum_height=content.setter("height"))

        # ─── 按钮行 ───
        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        btn_row.add_widget(MDRaisedButton(text="📂 打开图片", on_release=lambda x: self._open_images()))
        self.save_btn = MDRaisedButton(text="💾 保存结果", disabled=True, on_release=lambda x: self._save_result())
        btn_row.add_widget(self.save_btn)
        content.add_widget(btn_row)

        # ─── 方向选择 ───
        dir_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        dir_row.add_widget(MDLabel(text="拼接方向:", size_hint_x=0.3))
        self.h_btn = MDRaisedButton(text="水平  ↔", size_hint_x=0.3, on_release=lambda x: self._set_dir("horizontal"))
        self.v_btn = MDRaisedButton(text="垂直  ↕", size_hint_x=0.3, md_bg_color=(0.5,0.5,0.5,0.3),
                                     on_release=lambda x: self._set_dir("vertical"))
        dir_row.add_widget(self.h_btn)
        dir_row.add_widget(self.v_btn)
        content.add_widget(dir_row)

        # ─── 滑杆区域 ───
        slider_label = MDLabel(text="分割点调节:", font_style="H6", size_hint_y=None, height=dp(26))
        content.add_widget(slider_label)
        self.slider_container = BoxLayout(orientation="vertical", size_hint_y=None)
        self.slider_container.bind(minimum_height=self.slider_container.setter("height"))
        content.add_widget(self.slider_container)

        # ─── 预览 ───
        preview_label = MDLabel(text="预览:", font_style="H6", size_hint_y=None, height=dp(26))
        content.add_widget(preview_label)
        self.preview_image = KivyImage(size_hint_y=None, height=dp(300), allow_stretch=True, keep_ratio=True)
        content.add_widget(self.preview_image)

        # ─── 状态 ───
        self.status_label = MDLabel(text="请打开多张同规格图片", font_style="Caption", size_hint_y=None, height=dp(24),
                                     theme_text_color="Secondary")
        content.add_widget(self.status_label)

        scroll.add_widget(content)
        main.add_widget(scroll)
        self.add_widget(main)

    def _go_home(self):
        app = self._get_app()
        if app: app.go_home()

    def _get_app(self):
        from kivy.app import App
        return App.get_running_app()

    def _snack(self, text):
        Snackbar(text=text, duration=2).open()

    def _set_dir(self, d):
        self.dir_var = d
        self.h_btn.md_bg_color = self.theme_cls.primary_color if d == "horizontal" else (0.5,0.5,0.5,0.3)
        self.v_btn.md_bg_color = self.theme_cls.primary_color if d == "vertical" else (0.5,0.5,0.5,0.3)
        self._update_preview()

    def _open_images(self):
        self.show_file_chooser("选择图片", callback=self._on_file_selected, dir_select=False)

    def _on_file_selected(self, path):
        from kivy.uix.filechooser import FileChooserListView
        from kivy.uix.modalview import ModalView
        from kivy.uix.boxlayout import BoxLayout as Bx

        content = Bx(orientation="vertical", spacing=5, padding=5)
        fc = FileChooserListView(path=os.path.dirname(path) if os.path.isfile(path) else path,
                                  filters=[lambda folder, fn: fn.lower().endswith(
                                      ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'))])
        fc.selection = [path] if os.path.isfile(path) else []

        btn_bar = Bx(size_hint_y=0.1, spacing=10)
        confirm = MDRaisedButton(text="确定", size_hint_x=0.3)
        cancel = MDFlatButton(text="取消", size_hint_x=0.3)
        btn_bar.add_widget(cancel)
        btn_bar.add_widget(confirm)

        content.add_widget(fc)
        content.add_widget(btn_bar)

        modal = ModalView(size_hint=(0.9, 0.9))
        modal.add_widget(content)

        def on_confirm(*a):
            sel = fc.selection
            if len(sel) >= 2:
                self._load_images(list(sel))
            else:
                self._snack("请至少选择 2 张图片")
            modal.dismiss()
        confirm.bind(on_release=on_confirm)
        cancel.bind(on_release=lambda x: modal.dismiss())
        modal.open()

    def _load_images(self, paths):
        self.paths = paths
        self.images = []
        for p in self.paths:
            try:
                img = Image.open(p)
                self.images.append(img)
            except Exception as e:
                self._snack(f"无法加载 {os.path.basename(p)}: {e}")
                return

        # 检查规格
        ref_size = self.images[0].size
        for img in self.images[1:]:
            if img.size != ref_size:
                self._snack("图片规格不一致，请使用同尺寸图片")
                return

        # 重建滑杆
        self.slider_container.clear_widgets()
        self.slider_values = []
        n = len(self.images)
        for i in range(n - 1):
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48), spacing=dp(8))
            row.add_widget(MDLabel(text=f"分割点 {i+1}:", size_hint_x=0.3, font_style="Caption"))
            sv = Slider(min=5, max=95, value=50, size_hint_x=0.5)
            sv.bind(value=lambda inst, val, idx=i: self._on_slider(idx, val))
            row.add_widget(sv)
            self.slider_values.append(50)
            lbl = MDLabel(text="50%", size_hint_x=0.2, font_style="Caption")
            sv.bind(value=lambda inst, val, lbl=lbl: setattr(lbl, 'text', f"{int(val)}%"))
            row.add_widget(lbl)
            self.slider_container.add_widget(row)

        self.save_btn.disabled = False
        self.status_label.text = f"已加载 {n} 张图片 ({ref_size[0]}×{ref_size[1]})"
        self._update_preview()

    def _on_slider(self, idx, val):
        if idx < len(self.slider_values):
            self.slider_values[idx] = int(val)
            self._update_preview()

    def _stitch(self):
        """拼接图片，返回 PIL Image"""
        if len(self.images) < 2:
            return None

        is_h = self.dir_var == "horizontal"
        ref_w, ref_h = self.images[0].size

        splits = []
        for v in self.slider_values:
            pct = v / 100.0
            splits.append(int(ref_w * pct) if is_h else int(ref_h * pct))

        splits = [0] + splits + [ref_w if is_h else ref_h]

        result = Image.new("RGB", (ref_w, ref_h), "white")
        for i in range(len(splits) - 1):
            img_idx = min(i, len(self.images) - 1)
            x1, x2 = splits[i], splits[i + 1]
            if x2 > x1:
                region = self.images[img_idx].crop(
                    (x1, 0, x2, ref_h) if is_h else (0, x1, ref_w, x2)
                )
                result.paste(region, (x1, 0) if is_h else (0, x1))

        return result

    def _update_preview(self):
        if len(self.images) < 2:
            return
        try:
            result = self._stitch()
            if result is None:
                return
            # 缩放到预览大小
            pw, ph = result.size
            max_h = 300
            if ph > max_h:
                ratio = max_h / ph
                pw, ph = int(pw * ratio), max_h
            preview = result.resize((pw, ph), Image.Resampling.LANCZOS)

            # PIL → Kivy Texture
            data = preview.tobytes()
            tex = Texture.create(size=preview.size, colorfmt="rgb")
            tex.blit_buffer(data, colorfmt="rgb", bufferfmt="ubyte")
            tex.flip_vertical()
            self.preview_image.texture = tex
            self.preview_image.size_hint_y = None
            self.preview_image.height = dp(ph) if ph < 600 else dp(500)

        except Exception as e:
            self.status_label.text = f"预览失败: {e}"

    def _save_result(self):
        if len(self.images) < 2:
            return
        result = self._stitch()
        if result is None:
            return

        # 用默认文件名保存到 Pictures 目录
        from datetime import datetime
        default_name = f"stitch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
        from utils import get_pictures_path
        save_path = os.path.join(get_pictures_path(), default_name)

        try:
            result.save(save_path, quality=95)
            self.status_label.text = f"已保存: {default_name}"
            self._snack(f"拼接结果已保存到: {save_path}")
        except Exception as e:
            self._snack(f"保存失败: {e}")
