"""
图片批量调整工具 - KivyMD 版
"""
import os
import threading
from pathlib import Path
from PIL import Image

from kivy.clock import Clock, mainthread
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView

from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.slider import MDSlider
from kivymd.uix.textfield import MDTextField
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.toolbar import MDTopAppBar

from utils import get_image_files, SUPPORTED_IMAGE_FORMATS


from modules.base_tool import BaseToolScreen


class ImageResizeScreen(BaseToolScreen):
    screen_title = "🖼 图片批处理"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.file_list = []
        self._processing = False
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

        # ─── 输入模式 ───
        mode_label = MDLabel(text="输入模式:", font_style="H6", size_hint_y=None, height=dp(30))
        content.add_widget(mode_label)

        mode_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        self.mode_folder = True
        self.folder_btn = MDRaisedButton(text="📁 选择文件夹", on_release=lambda x: self._set_mode(True))
        self.files_btn = MDRaisedButton(text="📄 选择文件", md_bg_color=self.theme_cls.primary_color,
                                         on_release=lambda x: self._set_mode(False))
        mode_row.add_widget(self.folder_btn)
        mode_row.add_widget(self.files_btn)
        content.add_widget(mode_row)

        # ─── 输入路径 ───
        self.in_path_field = MDTextField(hint_text="输入文件夹", mode="fill", size_hint_y=None, height=dp(56), readonly=True)
        self.in_path_field.bind(on_focus=lambda *a: self._pick_input())
        content.add_widget(self.in_path_field)

        # ─── 输出路径 ───
        self.out_path_field = MDTextField(hint_text="输出文件夹", mode="fill", size_hint_y=None, height=dp(56), readonly=True)
        self.out_path_field.bind(on_focus=lambda *a: self._pick_output())
        content.add_widget(self.out_path_field)

        # ─── 调整方式 ───
        method_label = MDLabel(text="调整方式:", font_style="H6", size_hint_y=None, height=dp(30))
        content.add_widget(method_label)

        method_grid = GridLayout(cols=3, spacing=dp(6), size_hint_y=None, height=dp(44))
        self.method_var = "scale"
        self.scale_btn = MDRaisedButton(text="比例缩放", on_release=lambda x: self._set_method("scale"))
        self.res_btn = MDRaisedButton(text="按尺寸", md_bg_color=(0.5,0.5,0.5,0.3), on_release=lambda x: self._set_method("resolution"))
        self.short_btn = MDRaisedButton(text="短边限制", md_bg_color=(0.5,0.5,0.5,0.3), on_release=lambda x: self._set_method("short_edge"))
        method_grid.add_widget(self.scale_btn)
        method_grid.add_widget(self.res_btn)
        method_grid.add_widget(self.short_btn)
        content.add_widget(method_grid)

        # ─── 参数: 比例 ---
        self.scale_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56), spacing=dp(8), padding=dp(8))
        self.scale_box.add_widget(MDLabel(text="缩放比例:", size_hint_x=0.3))
        self.scale_var = 0.5
        self.scale_slider = MDSlider(min=0.05, max=3.0, value=0.5, size_hint_x=0.5)
        self.scale_lbl = MDLabel(text="0.50×", size_hint_x=0.2)
        self.scale_box.add_widget(self.scale_slider)
        self.scale_box.add_widget(self.scale_lbl)
        content.add_widget(self.scale_box)

        # ─── 参数: 尺寸 ---
        self.res_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56), spacing=dp(8), padding=dp(8))
        self.res_box.add_widget(MDLabel(text="宽度:", size_hint_x=0.15))
        self.width_input = MDTextField(text="1920", hint_text="宽", mode="fill", size_hint_x=0.2, input_filter="int")
        self.res_box.add_widget(self.width_input)
        self.res_box.add_widget(MDLabel(text="× 高度:", size_hint_x=0.15))
        self.height_input = MDTextField(text="1080", hint_text="高", mode="fill", size_hint_x=0.2, input_filter="int")
        self.res_box.add_widget(self.height_input)
        self.res_box.add_widget(MDLabel(text="px", size_hint_x=0.1))
        self.res_box.opacity = 0
        self.res_box.disabled = True
        content.add_widget(self.res_box)

        # ─── 参数: 短边 ---
        self.short_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56), spacing=dp(8), padding=dp(8))
        self.short_box.add_widget(MDLabel(text="短边像素:", size_hint_x=0.3))
        self.short_input = MDTextField(text="720", hint_text="短边", mode="fill", size_hint_x=0.3, input_filter="int")
        self.short_box.add_widget(self.short_input)
        self.short_box.opacity = 0
        self.short_box.disabled = True
        content.add_widget(self.short_box)

        # ─── 通用选项 ---
        opt_label = MDLabel(text="选项:", font_style="H6", size_hint_y=None, height=dp(30))
        content.add_widget(opt_label)

        opt_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(12))
        self.keep_aspect = True
        self.keep_btn = MDRaisedButton(text="☑ 保持宽高比", on_release=lambda x: self._toggle_aspect())
        opt_row.add_widget(self.keep_btn)

        opt_row.add_widget(MDLabel(text="质量:", size_hint_x=0.1))
        self.quality_input = MDTextField(text="85", hint_text="质量", mode="fill", size_hint_x=0.15, input_filter="int")
        opt_row.add_widget(self.quality_input)
        content.add_widget(opt_row)

        # 输出格式
        fmt_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        fmt_row.add_widget(MDLabel(text="输出格式:", size_hint_x=0.2))
        self.format_var = "保持原格式"
        for fmt in ["保持原格式", "JPEG", "PNG", "WEBP"]:
            btn = MDFlatButton(text=fmt, on_release=lambda x, f=fmt: self._set_format(f))
            fmt_row.add_widget(btn)
        content.add_widget(fmt_row)

        # ─── 操作 ---
        action_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48), spacing=dp(8))
        self.start_btn = MDRaisedButton(text="开始处理", md_bg_color="#27ae60",
                                        on_release=lambda x: self._start())
        action_row.add_widget(self.start_btn)
        self.progress = MDProgressBar(value=0, size_hint_x=0.6)
        action_row.add_widget(self.progress)
        self.progress_label = MDLabel(text="", size_hint_x=0.2, font_style="Caption")
        action_row.add_widget(self.progress_label)
        content.add_widget(action_row)

        # ─── 日志 ---
        log_label = MDLabel(text="处理日志:", font_style="H6", size_hint_y=None, height=dp(26))
        content.add_widget(log_label)
        self.log_text = MDLabel(text="就绪", size_hint_y=None, font_style="Caption")
        self.log_text.bind(texture_size=lambda *a: setattr(self.log_text, 'height', self.log_text.texture_size[1] + dp(8)))
        content.add_widget(self.log_text)

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

    def _set_mode(self, is_folder):
        self.mode_folder = is_folder
        self.folder_btn.md_bg_color = self.theme_cls.primary_color if is_folder else (0.5,0.5,0.5,0.3)
        self.files_btn.md_bg_color = (0.5,0.5,0.5,0.3) if is_folder else self.theme_cls.primary_color

    def _set_method(self, method):
        self.method_var = method
        for btn, m in [(self.scale_btn, "scale"), (self.res_btn, "resolution"), (self.short_btn, "short_edge")]:
            btn.md_bg_color = self.theme_cls.primary_color if m == method else (0.5,0.5,0.5,0.3)
        self.scale_box.opacity = 1 if method == "scale" else 0
        self.scale_box.disabled = method != "scale"
        self.res_box.opacity = 1 if method == "resolution" else 0
        self.res_box.disabled = method != "resolution"
        self.short_box.opacity = 1 if method == "short_edge" else 0
        self.short_box.disabled = method != "short_edge"

    def _toggle_aspect(self):
        self.keep_aspect = not self.keep_aspect
        self.keep_btn.text = "☑ 保持宽高比" if self.keep_aspect else "☐ 保持宽高比"

    def _set_format(self, fmt):
        self.format_var = fmt

    def _pick_input(self):
        self.show_file_chooser("选择输入文件夹", callback=self._on_input_selected, dir_select=True)

    def _on_input_selected(self, path):
        self.in_path_field.text = path

    def _pick_output(self):
        self.show_file_chooser("选择输出文件夹", callback=self._on_output_selected, dir_select=True)

    def _on_output_selected(self, path):
        self.out_path_field.text = path

    @mainthread
    def _log(self, msg):
        current = self.log_text.text
        self.log_text.text = (current + "\n" + msg) if current != "就绪" else msg

    @mainthread
    def _update_progress(self, value, label=""):
        self.progress.value = value
        if label:
            self.progress_label.text = label

    def _start(self):
        if self._processing:
            return

        out_dir = self.out_path_field.text.strip()
        if not out_dir:
            self._snack("请选择输出文件夹")
            return

        input_files = []
        if self.mode_folder:
            in_path = self.in_path_field.text.strip()
            if not in_path:
                self._snack("请选择输入文件夹")
                return
            input_files = get_image_files(in_path, True)
        else:
            input_files = [Path(f) for f in self.file_list]

        if not input_files:
            self._snack("没有找到支持的图片文件")
            return

        self._processing = True
        self.start_btn.disabled = True
        self.log_text.text = "处理中..."
        self.progress.value = 0

        thread = threading.Thread(target=self._process, args=(input_files, out_dir), daemon=True)
        thread.start()

    def _process(self, input_files, out_dir):
        total = len(input_files)
        method = self.method_var
        keep_aspect = self.keep_aspect
        try:
            quality = int(self.quality_input.text) if self.quality_input.text else 85
        except:
            quality = 85
        out_format = self.format_var

        scale = None
        target_size = None
        short_edge = None

        if method == "scale":
            scale = self.scale_slider.value
        elif method == "resolution":
            try:
                tw = int(self.width_input.text) if self.width_input.text else 1920
                th = int(self.height_input.text) if self.height_input.text else 1080
                target_size = (tw, th)
            except:
                target_size = (1920, 1080)
        elif method == "short_edge":
            try:
                short_edge = int(self.short_input.text) if self.short_input.text else 720
            except:
                short_edge = 720

        success = 0
        failed = 0

        for i, img_file in enumerate(input_files):
            try:
                out_path = Path(out_dir) / img_file.name
                os.makedirs(out_path.parent, exist_ok=True)

                with Image.open(img_file) as img:
                    if img.mode in ("RGBA", "P"):
                        if out_format == "JPEG" or (not out_format or out_format == "保持原格式"):
                            img = img.convert("RGB")

                    w, h = img.size

                    if scale:
                        nw, nh = int(w * scale), int(h * scale)
                    elif target_size:
                        tw, th = target_size
                        if keep_aspect:
                            ratio = min(tw / w, th / h) if tw > 0 and th > 0 else 1
                            nw, nh = int(w * ratio), int(h * ratio)
                        else:
                            nw, nh = tw, th
                    elif short_edge:
                        ratio = short_edge / min(w, h)
                        nw, nh = int(w * ratio), int(h * ratio)
                    else:
                        nw, nh = w, h

                    nw = max(1, nw)
                    nh = max(1, nh)

                    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)

                    save_path = str(out_path)
                    if out_format and out_format != "保持原格式":
                        base, _ = os.path.splitext(save_path)
                        save_path = f"{base}.{out_format.lower()}"

                    fmt = out_format if out_format and out_format != "保持原格式" else None
                    if fmt == "JPEG" or (not fmt and save_path.upper().endswith((".JPG", ".JPEG"))):
                        resized.save(save_path, quality=quality, optimize=True)
                    else:
                        resized.save(save_path)

                    self._log(f"✅ {img_file.name} → ({nw}×{nh})")
                    success += 1
            except Exception as e:
                self._log(f"❌ {img_file.name}: {e}")
                failed += 1

            self._update_progress((i + 1) / total * 100, f"{i+1}/{total}")

        self._log(f"\n处理完成！成功: {success}, 失败: {failed}")
        self._update_progress(100, "完成")
        self._processing = False
        Clock.schedule_once(lambda dt: setattr(self.start_btn, 'disabled', False), 0)
        self._snack(f"处理完成！成功: {success}, 失败: {failed}")
