"""
批量文件重命名工具 - KivyMD 版
"""
import os
import re
from pathlib import Path
from datetime import datetime

from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform as kivy_platform

from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.slider import MDSlider
from kivymd.uix.textfield import MDTextField
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.toolbar import MDTopAppBar


from modules.base_tool import BaseToolScreen


class RenameScreen(BaseToolScreen):
    screen_title = "📄 批量重命名"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.files = []            # [(abs_path, name), ...]
        self.current_preview = []  # [(old_name, new_name, old_path), ...]
        self.renamed = []          # [(old_state, count), ...]
        self.redo_stack = []
        self.history_limit = 50
        self.folder_path = ""
        Clock.schedule_once(self.build_ui, 0)

    def build_ui(self, dt=None):
        self.clear_widgets()
        main = BoxLayout(orientation="vertical")

        # ─── 顶栏 ───
        toolbar = MDTopAppBar(
            title=self.screen_title,
            elevation=2,
            left_action_items=[["arrow-left", lambda x: self._go_home()]],
            md_bg_color=self.theme_cls.primary_color,
        )
        main.add_widget(toolbar)

        # ─── 参数区域 (可滚动) ───
        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(8), padding=dp(12))
        content.bind(minimum_height=content.setter("height"))

        # --- 文件夹选择 ---
        self.folder_field = MDTextField(
            hint_text="选择目标文件夹",
            mode="fill",
            size_hint_y=None,
            height=dp(56),
            readonly=True,
        )
        self.folder_field.bind(on_focus=lambda *a: self._pick_folder())
        content.add_widget(self.folder_field)

        # --- 筛选 ---
        filter_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(8))
        self.filter_btn_all = MDRaisedButton(text="所有文件", size_hint_x=0.4, on_release=lambda x: self._set_filter(True))
        self.filter_btn_ext = MDRaisedButton(text="按扩展名", size_hint_x=0.4, on_release=lambda x: self._set_filter(False))
        self.filter_all = True
        self.ext_filter = ""
        filter_box.add_widget(self.filter_btn_all)
        filter_box.add_widget(self.filter_btn_ext)
        content.add_widget(filter_box)

        # --- 命名规则选择 ---
        rules_label = MDLabel(text="命名规则:", font_style="H6", size_hint_y=None, height=dp(30))
        content.add_widget(rules_label)

        rule_grid = GridLayout(cols=2, spacing=dp(6), size_hint_y=None, height=dp(120))
        self.rule_var = "sequence"
        rules = [
            ("sequence", "🔢 序号"),
            ("prefix", "➕ 前缀"),
            ("suffix", "➕ 后缀"),
            ("replace", "✏️ 替换"),
            ("case", "🔤 大小写"),
            ("date", "📅 日期"),
        ]
        self.rule_btns = {}
        for val, lbl in rules:
            btn = MDRaisedButton(text=lbl, size_hint_x=0.5, on_release=lambda x, v=val: self._set_rule(v))
            rule_grid.add_widget(btn)
            self.rule_btns[val] = btn
        content.add_widget(rule_grid)

        # --- 参数卡片 (动态内容) ---
        self.params_box = BoxLayout(orientation="vertical", size_hint_y=None)
        self.params_box.bind(minimum_height=self.params_box.setter("height"))
        content.add_widget(self.params_box)
        self._build_sequence_params()

        # --- 操作按钮 ---
        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48), spacing=dp(8))
        btn_row.add_widget(MDRaisedButton(text="📂 加载文件", on_release=lambda x: self._load_files()))
        btn_row.add_widget(MDRaisedButton(text="👁 预览", on_release=lambda x: self._preview()))
        btn_row.add_widget(MDRaisedButton(text="✅ 执行", md_bg_color="#27ae60", on_release=lambda x: self._execute()))
        btn_row.add_widget(MDFlatButton(text="↩ 撤销", on_release=lambda x: self._undo()))
        btn_row.add_widget(MDFlatButton(text="↪ 重做", on_release=lambda x: self._redo()))
        content.add_widget(btn_row)

        # --- 文件列表 ---
        list_label = MDLabel(text="文件列表:", font_style="H6", size_hint_y=None, height=dp(30))
        content.add_widget(list_label)

        self.file_list_label = MDLabel(text="就绪", font_style="Caption", size_hint_y=None, height=dp(20),
                                        theme_text_color="Secondary")
        content.add_widget(self.file_list_label)

        scroll.add_widget(content)
        main.add_widget(scroll)

        # --- 使用简单的表格显示 (MDDataTable 可能太重，改用 ScrollView + 行) ---
        self.table_scroll = ScrollView(do_scroll_x=False, size_hint_y=0.4)
        self.table_content = BoxLayout(orientation="vertical", size_hint_y=None)
        self.table_content.bind(minimum_height=self.table_content.setter("height"))
        self.table_scroll.add_widget(self.table_content)
        main.add_widget(self.table_scroll)

        self.add_widget(main)

    # ─── 辅助 ───
    def _go_home(self):
        app = self._get_app()
        if app:
            app.go_home()

    def _get_app(self):
        from kivy.app import App
        return App.get_running_app()

    def _snack(self, text):
        Snackbar(text=text, duration=2).open()

    # ─── 规则切换 ───
    def _set_rule(self, rule):
        self.rule_var = rule
        for v, btn in self.rule_btns.items():
            btn.md_bg_color = self.theme_cls.primary_color if v == rule else (0.5, 0.5, 0.5, 0.3)
        self.params_box.clear_widgets()
        build_fns = {
            "sequence": self._build_sequence_params,
            "prefix": self._build_prefix_params,
            "suffix": self._build_suffix_params,
            "replace": self._build_replace_params,
            "case": self._build_case_params,
            "date": self._build_date_params,
        }
        fn = build_fns.get(rule)
        if fn:
            fn()

    def _build_sequence_params(self):
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4),
                         padding=dp(8), height=dp(100))
        box.md_bg_color = (0.95, 0.95, 0.95, 1) if not self.theme_cls.theme_style == "Dark" else (0.2, 0.2, 0.2, 1)

        row1 = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(8))
        self.base_var = "file"
        self.base_input = MDTextField(text="file", hint_text="基础名", size_hint_x=0.4, mode="fill")
        row1.add_widget(self.base_input)

        self.start_var = 1
        self.start_input = MDTextField(text="1", hint_text="起始", size_hint_x=0.2, mode="fill", input_filter="int")
        row1.add_widget(self.start_input)

        self.digits_var = 3
        self.digits_input = MDTextField(text="3", hint_text="位数", size_hint_x=0.2, mode="fill", input_filter="int")
        row1.add_widget(self.digits_input)

        box.add_widget(row1)
        self.params_box.add_widget(box)

    def _build_prefix_params(self):
        box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56), spacing=dp(8), padding=dp(8))
        self.prefix_var = "new_"
        box.add_widget(MDTextField(text="new_", hint_text="前缀内容", mode="fill"))
        self.params_box.add_widget(box)

    def _build_suffix_params(self):
        box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56), spacing=dp(8), padding=dp(8))
        self.suffix_var = "_new"
        box.add_widget(MDTextField(text="_new", hint_text="后缀内容", mode="fill"))
        self.params_box.add_widget(box)

    def _build_replace_params(self):
        box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(56), spacing=dp(8), padding=dp(8))
        self.old_text_var = "old"
        self.new_text_var = "new"
        box.add_widget(MDTextField(text="old", hint_text="查找", mode="fill", size_hint_x=0.4))
        box.add_widget(MDTextField(text="new", hint_text="替换为", mode="fill", size_hint_x=0.4))
        self.params_box.add_widget(box)

    def _build_case_params(self):
        box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48), spacing=dp(8), padding=dp(8))
        self.case_var = "lower"
        for val, lbl in [("lower", "小写"), ("upper", "大写"), ("title", "首字母大写")]:
            btn = MDRaisedButton(text=lbl, on_release=lambda x, v=val: self._set_case(v))
            box.add_widget(btn)
        self.params_box.add_widget(box)

    def _set_case(self, val):
        self.case_var = val

    def _build_date_params(self):
        box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(4), padding=dp(8), height=dp(80))
        self.date_format_var = "%Y%m%d_%H%M%S"
        self.date_base_var = ""
        row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(8))
        row.add_widget(MDTextField(text="%Y%m%d_%H%M%S", hint_text="日期格式", mode="fill", size_hint_x=0.5))
        row.add_widget(MDTextField(text="", hint_text="基础名(可选)", mode="fill", size_hint_x=0.4))
        box.add_widget(row)
        self.params_box.add_widget(box)

    def _set_filter(self, all_files):
        self.filter_all = all_files
        if all_files:
            self.filter_btn_all.md_bg_color = self.theme_cls.primary_color
            self.filter_btn_ext.md_bg_color = (0.5, 0.5, 0.5, 0.3)
        else:
            self.filter_btn_ext.md_bg_color = self.theme_cls.primary_color
            self.filter_btn_all.md_bg_color = (0.5, 0.5, 0.5, 0.3)

    # ─── 文件夹 ───
    def _pick_folder(self):
        """Android 上使用文件选择器"""
        self.show_file_chooser("选择文件夹", callback=self._on_folder_selected, dir_select=True)

    def _on_folder_selected(self, path):
        self.folder_path = path
        self.folder_field.text = path
        self._load_files()

    # ─── 文件操作 ───
    def _load_files(self):
        if not self.folder_path or not os.path.isdir(self.folder_path):
            self._snack("请先选择有效的文件夹")
            return

        self.files = []
        for entry in os.scandir(self.folder_path):
            if entry.is_file():
                self.files.append((entry.path, entry.name))

        self.files.sort(key=lambda x: x[1])

        if not self.filter_all and self.ext_filter:
            exts = [e.strip().lower() for e in self.ext_filter.split(",")]
            self.files = [f for f in self.files if Path(f[1]).suffix.lower() in exts]

        self.current_preview = []
        self._refresh_table()
        self.file_list_label.text = f"已加载 {len(self.files)} 个文件"

    def _refresh_table(self, preview=False):
        self.table_content.clear_widgets()
        source = self.current_preview if preview else [(n, "", p) for p, n in self.files]

        # 表头
        header = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32), spacing=dp(4))
        for text, w in [("#", 0.08), ("原始名称", 0.40), ("新名称", 0.40), ("大小", 0.12)]:
            lbl = MDLabel(text=text, bold=True, font_style="Caption", size_hint_x=w, halign="center")
            header.add_widget(lbl)
        self.table_content.add_widget(header)

        for i, (old_name, new_name, path) in enumerate(source):
            try:
                size = os.path.getsize(path)
                size_str = f"{size // 1024}KB" if size < 1024**2 else f"{size // 1024**2}MB"
            except Exception:
                size_str = ""
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28), spacing=dp(4))
            row.add_widget(MDLabel(text=str(i+1), size_hint_x=0.08, halign="center", font_style="Caption"))
            row.add_widget(MDLabel(text=old_name, size_hint_x=0.40, font_style="Caption"))
            display_new = new_name if preview and new_name != old_name else ""
            row.add_widget(MDLabel(text=display_new, size_hint_x=0.40, font_style="Caption",
                                    theme_text_color="Primary" if display_new else "Hint"))
            row.add_widget(MDLabel(text=size_str, size_hint_x=0.12, halign="center", font_style="Caption"))
            self.table_content.add_widget(row)

    # ─── 命名逻辑 ───
    def _generate_new_name(self, old_name, index):
        name_part, ext_part = os.path.splitext(old_name)
        rule = self.rule_var

        if rule == "sequence":
            base = self.base_input.text if hasattr(self, 'base_input') else "file"
            start = int(self.start_input.text) if hasattr(self, 'start_input') and self.start_input.text.isdigit() else 1
            digits = int(self.digits_input.text) if hasattr(self, 'digits_input') and self.digits_input.text.isdigit() else 3
            num = str(start + index).zfill(digits)
            return f"{base}{num}{ext_part}"

        elif rule == "prefix":
            prefix = self.prefix_var if hasattr(self, 'prefix_var') else "new_"
            return prefix + old_name

        elif rule == "suffix":
            suffix = self.suffix_var if hasattr(self, 'suffix_var') else "_new"
            return name_part + suffix + ext_part

        elif rule == "replace":
            old_t = self.old_text_var if hasattr(self, 'old_text_var') else "old"
            new_t = self.new_text_var if hasattr(self, 'new_text_var') else "new"
            return old_name.replace(old_t, new_t)

        elif rule == "case":
            val = self.case_var if hasattr(self, 'case_var') else "lower"
            if val == "lower":
                return old_name.lower()
            elif val == "upper":
                return old_name.upper()
            elif val == "title":
                return name_part.title() + ext_part.lower()

        elif rule == "date":
            date_str = datetime.now().strftime(self.date_format_var if hasattr(self, 'date_format_var') else "%Y%m%d_%H%M%S")
            base = self.date_base_var if hasattr(self, 'date_base_var') else ""
            if base:
                return f"{base}_{date_str}{ext_part}"
            return f"{date_str}_{name_part}{ext_part}"

        return old_name

    # ─── 预览和执行 ───
    def _preview(self, *args):
        if not self.files:
            self._snack("没有文件可预览")
            return
        self.current_preview = []
        for i, (path, name) in enumerate(self.files):
            new_name = self._generate_new_name(name, i)
            self.current_preview.append((name, new_name, path))
        self._refresh_table(preview=True)
        self.file_list_label.text = f"预览完成 — {len(self.files)} 个文件"

    def _execute(self, *args):
        if not self.files:
            self._snack("没有文件需要重命名")
            return
        if len(self.current_preview) != len(self.files):
            self._preview()

        # 备份
        old_state = [(p, n) for n, _, p in self.current_preview]

        renamed_count = 0
        failed_count = 0
        for old_name, new_name, old_path in self.current_preview:
            if old_name == new_name:
                continue
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            if os.path.exists(new_path) and new_path != old_path:
                base, ext = os.path.splitext(new_name)
                counter = 1
                while os.path.exists(new_path):
                    new_name = f"{base}_{counter}{ext}"
                    new_path = os.path.join(os.path.dirname(old_path), new_name)
                    counter += 1
            try:
                os.rename(old_path, new_path)
                renamed_count += 1
                for j, (p, n) in enumerate(self.files):
                    if p == old_path:
                        self.files[j] = (new_path, new_name)
                        break
            except Exception as e:
                failed_count += 1

        self.renamed.append((old_state, renamed_count))
        if len(self.renamed) > self.history_limit:
            self.renamed.pop(0)
        self.redo_stack.clear()

        self.current_preview = []
        self._refresh_table()
        msg = f"成功重命名 {renamed_count} 个文件"
        if failed_count:
            msg += f"，{failed_count} 个失败"
        self.file_list_label.text = msg
        self._snack(msg)

    # ─── 撤销/重做 ───
    def _undo(self, *args):
        if not self.renamed:
            self._snack("没有可撤销的操作")
            return
        old_state, count = self.renamed.pop()
        reversed_state = []
        for orig_path, orig_name in old_state:
            for path, name in self.files:
                if os.path.basename(path) != orig_name:
                    try:
                        target = os.path.join(os.path.dirname(path), orig_name)
                        os.rename(path, target)
                        reversed_state.append((path, os.path.basename(path)))
                        break
                    except Exception:
                        pass
        self.redo_stack.append((reversed_state, count))
        self._load_files()
        self._snack(f"已撤销: 还原 {count} 个文件")

    def _redo(self, *args):
        if not self.redo_stack:
            self._snack("没有可重做的操作")
            return
        self._snack("请重新执行重命名操作")
