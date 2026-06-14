"""
随机工具集 - KivyMD 版
轮盘 / 骰子 / 随机数 / 抽签 / 抛硬币 / 随机颜色
"""
import os
import math
import random
from datetime import datetime

from kivy.clock import Clock
from kivy.graphics import Color as GColor, Ellipse, Line, Rectangle, PushMatrix, PopMatrix, Rotate
from kivy.graphics.texture import Texture
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.image import Image as KivyImage
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.slider import Slider

from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.tab import MDTabs, MDTabsBase
from kivymd.uix.textfield import MDTextField
from kivymd.uix.toolbar import MDTopAppBar


class TabContent(BoxLayout, MDTabsBase):
    """MDTab 包装器"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


from modules.base_tool import BaseToolScreen


class RandomToolsScreen(BaseToolScreen):
    screen_title = "🎲 随机工具"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.build_ui, 0)

    def build_ui(self, dt=None):
        self.clear_widgets()
        main = BoxLayout(orientation="vertical")

        toolbar = MDTopAppBar(title=self.screen_title, elevation=2,
                               left_action_items=[["arrow-left", lambda x: self._go_home()]],
                               md_bg_color=self.theme_cls.primary_color)
        main.add_widget(toolbar)

        tabs = MDTabs(background_color=self.theme_cls.primary_color)
        tabs.bind(on_switch_tabs=self._on_tab_switch)

        for tab_cls, title, icon in [
            (RouletteContent, "轮盘", "🎡"),
            (DiceContent, "骰子", "🎲"),
            (NumberContent, "随机数", "🔢"),
            (DrawContent, "抽签", "🎯"),
            (CoinContent, "抛硬币", "🪙"),
            (ColorContent, "随机颜色", "🎨"),
        ]:
            tab = TabContent(title=f"{icon} {title}")
            widget = tab_cls()
            tab.add_widget(widget)
            tabs.add_widget(tab)

        main.add_widget(tabs)
        self.add_widget(main)

    def _go_home(self):
        app = self._get_app()
        if app: app.go_home()

    def _get_app(self):
        from kivy.app import App
        return App.get_running_app()

    def _on_tab_switch(self, *args):
        pass


# ════════════════════════════════════════════════════════════
# 🎡 轮盘
# ════════════════════════════════════════════════════════════

class RouletteContent(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(8)
        self.padding = dp(12)
        self.options = ["选项 1", "选项 2", "选项 3", "选项 4", "选项 5", "选项 6"]
        self.colors = ["#e74c3c", "#3498db", "#2ecc71", "#f39c12", "#9b59b6", "#1abc9c",
                       "#e67e22", "#00bcd4", "#e91e63", "#4caf50", "#ff5722", "#795548"]
        self.spinning = False
        self.angle = 0
        Clock.schedule_once(self._build_ui, 0)

    def _build_ui(self, dt=None):
        self.clear_widgets()

        hbox = BoxLayout(orientation="horizontal", spacing=dp(8))

        # ─── 左侧: 选项编辑 ───
        left = BoxLayout(orientation="vertical", size_hint_x=0.35, spacing=dp(4))
        left.add_widget(MDLabel(text="选项:", bold=True, size_hint_y=None, height=dp(24)))

        self.opt_grid = GridLayout(cols=1, size_hint_y=None, spacing=dp(2))
        self.opt_grid.bind(minimum_height=self.opt_grid.setter("height"))
        left_scroll = ScrollView(do_scroll_x=False, size_hint_y=0.6)
        left_scroll.add_widget(self.opt_grid)
        left.add_widget(left_scroll)
        self._rebuild_opt_list()

        input_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(4))
        self.opt_input = MDTextField(text="", hint_text="新选项", mode="fill", size_hint_x=0.7)
        input_row.add_widget(self.opt_input)
        input_row.add_widget(MDIconButton(icon="plus", on_release=lambda x: self._add_option()))
        left.add_widget(input_row)

        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36), spacing=dp(4))
        btn_row.add_widget(MDFlatButton(text="删除选中", on_release=lambda x: self._remove_option()))
        btn_row.add_widget(MDFlatButton(text="重置", on_release=lambda x: self._reset_options()))
        left.add_widget(btn_row)

        # ─── 右侧: 轮盘 + 结果 ───
        right = BoxLayout(orientation="vertical", spacing=dp(8))
        self.canvas_box = BoxLayout(size_hint_y=0.7)
        right.add_widget(self.canvas_box)

        ctrl_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        self.spin_btn = MDRaisedButton(text="🎡 旋转!", on_release=lambda x: self._spin())
        ctrl_row.add_widget(self.spin_btn)
        self.result_label = MDLabel(text="点击旋转试试", font_style="H6",
                                     theme_text_color="Primary")
        ctrl_row.add_widget(self.result_label)
        right.add_widget(ctrl_row)

        hbox.add_widget(left)
        hbox.add_widget(right)
        self.add_widget(hbox)

        Clock.schedule_once(lambda dt: self._draw(), 0.3)

    def _rebuild_opt_list(self):
        self.opt_grid.clear_widgets()
        for i, opt in enumerate(self.options):
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32), spacing=dp(2))
            row.add_widget(MDLabel(text=f"{i+1}. {opt}", font_style="Caption"))
            self.opt_grid.add_widget(row)

    def _add_option(self):
        text = self.opt_input.text.strip()
        if text:
            self.options.append(text)
            self.opt_input.text = ""
            self._rebuild_opt_list()
            self._draw()

    def _remove_option(self):
        if len(self.options) > 2:
            self.options.pop()
            self._rebuild_opt_list()
            self._draw()

    def _reset_options(self):
        self.options = ["选项 1", "选项 2", "选项 3", "选项 4", "选项 5", "选项 6"]
        self._rebuild_opt_list()
        self._draw()

    def _draw(self, *args):
        """在 Canvas 中画轮盘"""
        from kivy.graphics import Color as GColor, Ellipse, Line, Rectangle, PushMatrix, PopMatrix, Rotate
        from kivy.uix.widget import Widget

        n = len(self.options)
        if n == 0:
            return

        # 用 Widget + canvas 画
        w = self.canvas_box.width or dp(300)
        h = self.canvas_box.height or dp(300)
        cx, cy = w / 2, h / 2
        r = min(w, h) / 2 - dp(10)
        if r < dp(20):
            return

        # 移除旧的 canvas 子控件
        self.canvas_box.clear_widgets()
        canvas_widget = Widget(size_hint=(1, 1))
        self.canvas_box.add_widget(canvas_widget)

        # 绘制到 PIL 图像然后显示为 Texture（更可靠的跨平台方式）
        from PIL import Image, ImageDraw
        img_size = int(max(w, h))
        img = Image.new("RGBA", (img_size, img_size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        cx2, cy2 = img_size // 2, img_size // 2
        r2 = img_size // 2 - 10

        arc_angle = 360.0 / n
        for i in range(n):
            start = self.angle + i * arc_angle
            color = self.colors[i % len(self.colors)]
            # Draw arc using PIL
            draw.pieslice([cx2-r2, cy2-r2, cx2+r2, cy2+r2],
                          start=start, end=start+arc_angle,
                          fill=color, outline="white", width=2)

            # 标签
            mid_angle = math.radians(start + arc_angle / 2)
            label_r = r2 * 0.6
            lx = cx2 + label_r * math.cos(mid_angle)
            ly = cy2 + label_r * math.sin(mid_angle)
            text = self.options[i][:5]
            draw.text((lx, ly), text, fill="white", anchor="mm")

        # 中心+指针
        draw.ellipse([cx2-15, cy2-15, cx2+15, cy2+15], fill="white", outline="#ddd")
        draw.polygon([(cx2-8, cy2-r2-5), (cx2+8, cy2-r2-5), (cx2, cy2-r2+15)],
                      fill="#e74c3c")

        # PIL → Kivy Texture
        data = img.tobytes()
        tex = Texture.create(size=img.size, colorfmt="rgba")
        tex.blit_buffer(data, colorfmt="rgba", bufferfmt="ubyte")
        tex.flip_vertical()

        kivy_img = KivyImage(texture=tex, allow_stretch=True, keep_ratio=True,
                              size_hint=(1, 1))
        self.canvas_box.add_widget(kivy_img)

    def _spin(self):
        if self.spinning or len(self.options) < 2:
            return
        self.spinning = True
        self.spin_btn.disabled = True
        self.result_label.text = "旋转中..."

        n = len(self.options)
        target_idx = random.randint(0, n - 1)
        arc = 360.0 / n
        extra = random.randint(5, 10) * 360
        target_angle = 360 - (target_idx * arc + arc / 2) + extra

        self._animate(target_angle, target_idx, 0)

    def _animate(self, target, result_idx, step):
        if step >= 40:
            self.angle = target % 360
            self._draw()
            self.spinning = False
            self.spin_btn.disabled = False
            self.result_label.text = f"🎉 选中: {self.options[result_idx]}"
            return

        progress = step / 40
        eased = 1 - (1 - progress) ** 3
        self.angle = (self.angle + (target - self.angle) * eased) % 360
        self._draw()
        Clock.schedule_once(lambda dt: self._animate(target, result_idx, step + 1), 0.03)


# ════════════════════════════════════════════════════════════
# 🎲 骰子
# ════════════════════════════════════════════════════════════

DICE_FACES = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}


class DiceContent(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(12)
        self.padding = dp(16)
        self.history = []
        Clock.schedule_once(self._build_ui, 0)

    def _build_ui(self, dt=None):
        self.clear_widgets()

        # 骰子显示
        self.dice_box = BoxLayout(orientation="horizontal", size_hint_y=0.4, spacing=dp(8),
                                   padding=dp(10))
        self.dice_labels = []
        self._rebuild_dice(1)
        self.add_widget(self.dice_box)

        # 控制
        ctrl = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        ctrl.add_widget(MDLabel(text="骰子数:", size_hint_x=0.15))
        self.count_input = MDTextField(text="1", mode="fill", size_hint_x=0.1, input_filter="int")
        ctrl.add_widget(self.count_input)
        ctrl.add_widget(MDLabel(text="面数:", size_hint_x=0.1))
        self.sides_input = MDTextField(text="6", mode="fill", size_hint_x=0.1, input_filter="int")
        ctrl.add_widget(self.sides_input)
        ctrl.add_widget(MDLabel(text="修正:", size_hint_x=0.1))
        self.mod_input = MDTextField(text="0", mode="fill", size_hint_x=0.08, input_filter="int")
        ctrl.add_widget(self.mod_input)
        ctrl.add_widget(MDRaisedButton(text="🎲 投掷!", on_release=lambda x: self._roll()))
        self.total_label = MDLabel(text="= ?", font_style="H5", theme_text_color="Primary",
                                    size_hint_x=0.2)
        ctrl.add_widget(self.total_label)
        self.add_widget(ctrl)

        # 历史
        hist_label = MDLabel(text="投掷历史:", bold=True, size_hint_y=None, height=dp(24))
        self.add_widget(hist_label)
        self.hist_text = MDLabel(text="(空)", size_hint_y=0.3, font_style="Caption")
        self.hist_text.bind(texture_size=lambda *a: setattr(self.hist_text, 'height',
                                                             min(self.hist_text.texture_size[1], dp(200))))
        self.add_widget(self.hist_text)

        clear_btn = MDFlatButton(text="清空历史", on_release=lambda x: self._clear_history(),
                                  size_hint_y=None, height=dp(32))
        self.add_widget(clear_btn)

    def _rebuild_dice(self, count):
        self.dice_box.clear_widgets()
        self.dice_labels = []
        for i in range(count):
            lbl = MDLabel(
                text="⚀",
                font_style="H1" if count <= 4 else "H3",
                halign="center",
                size_hint_x=1.0/count if count > 0 else 1,
            )
            self.dice_box.add_widget(lbl)
            self.dice_labels.append(lbl)

    def _roll(self):
        try:
            count = max(1, int(self.count_input.text or "1"))
            sides = max(2, int(self.sides_input.text or "6"))
            mod = int(self.mod_input.text or "0")
        except:
            count, sides, mod = 1, 6, 0

        if len(self.dice_labels) != count:
            self._rebuild_dice(count)

        results = []
        for i in range(count):
            r = random.randint(1, sides)
            results.append(r)

        self._animate_roll(results, sides, mod, 0)

    def _animate_roll(self, results, sides, mod, step):
        if step >= 8:
            for i, r in enumerate(results):
                if sides == 6 and 1 <= r <= 6:
                    self.dice_labels[i].text = DICE_FACES[r]
                else:
                    self.dice_labels[i].text = str(r)

            total = sum(results) + mod
            self.total_label.text = f"= {total}"

            detail = " + ".join(str(r) for r in results)
            if mod != 0:
                detail += f" + ({mod})"
            self._add_history(f"d{sides}×{len(results)}: {detail} = {total}")
            return

        for i in range(len(results)):
            rr = random.randint(1, sides)
            if sides == 6:
                self.dice_labels[i].text = DICE_FACES.get(rr, str(rr))
            else:
                self.dice_labels[i].text = str(rr)

        Clock.schedule_once(lambda dt: self._animate_roll(results, sides, mod, step + 1), 0.06)

    def _add_history(self, text):
        current = self.hist_text.text
        self.hist_text.text = (current + "\n" + text) if current != "(空)" else text

    def _clear_history(self):
        self.hist_text.text = "(空)"


# ════════════════════════════════════════════════════════════
# 🔢 随机数
# ════════════════════════════════════════════════════════════

class NumberContent(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(8)
        self.padding = dp(16)
        Clock.schedule_once(self._build_ui, 0)

    def _build_ui(self, dt=None):
        self.clear_widgets()

        # 参数
        param_box = BoxLayout(orientation="vertical", spacing=dp(8), size_hint_y=None)
        param_box.bind(minimum_height=param_box.setter("height"))

        row1 = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        row1.add_widget(MDLabel(text="最小值:", size_hint_x=0.15))
        self.min_input = MDTextField(text="1", mode="fill", size_hint_x=0.15, input_filter="int")
        row1.add_widget(self.min_input)
        row1.add_widget(MDLabel(text="最大值:", size_hint_x=0.15))
        self.max_input = MDTextField(text="100", mode="fill", size_hint_x=0.15, input_filter="int")
        row1.add_widget(self.max_input)
        param_box.add_widget(row1)

        row2 = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        row2.add_widget(MDLabel(text="数量:", size_hint_x=0.1))
        self.count_input = MDTextField(text="1", mode="fill", size_hint_x=0.1, input_filter="int")
        row2.add_widget(self.count_input)
        row2.add_widget(MDRaisedButton(text="🔢 生成", on_release=lambda x: self._generate()))
        param_box.add_widget(row2)
        self.add_widget(param_box)

        # 结果
        self.add_widget(MDLabel(text="结果:", bold=True, size_hint_y=None, height=dp(24)))
        self.result_text = MDLabel(text="(等待生成)", size_hint_y=0.4, font_style="Caption")
        self.result_text.bind(texture_size=lambda *a: setattr(self.result_text, 'height',
                                                               min(self.result_text.texture_size[1], dp(300))))
        self.add_widget(self.result_text)

        self.stat_label = MDLabel(text="", size_hint_y=None, height=dp(24), font_style="Caption",
                                   theme_text_color="Secondary")
        self.add_widget(self.stat_label)

        copy_btn = MDFlatButton(text="复制结果", on_release=lambda x: self._copy(),
                                 size_hint_y=None, height=dp(36))
        self.add_widget(copy_btn)

    def _generate(self):
        try:
            min_v = int(self.min_input.text or "1")
            max_v = int(self.max_input.text or "100")
            count = int(self.count_input.text or "1")
        except:
            min_v, max_v, count = 1, 100, 1

        if min_v > max_v:
            Snackbar(text="最小值不能大于最大值").open()
            return

        results = [str(random.randint(min_v, max_v)) for _ in range(count)]

        self.result_text.text = ", ".join(results)
        nums = [int(x) for x in results]
        avg = sum(nums) / len(nums)
        self.stat_label.text = f"共 {len(results)} 个 | 总和: {sum(nums)} | 平均: {avg:.1f}"

    def _copy(self):
        text = self.result_text.text
        if text and text != "(等待生成)":
            from kivy.core.window import Window
            Window.clipboard = text
            Snackbar(text="已复制到剪贴板").open()


# ════════════════════════════════════════════════════════════
# 🎯 抽签
# ════════════════════════════════════════════════════════════

class DrawContent(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(8)
        self.padding = dp(12)
        self.items = ["张三", "李四", "王五", "赵六", "钱七"]
        Clock.schedule_once(self._build_ui, 0)

    def _build_ui(self, dt=None):
        self.clear_widgets()

        hbox = BoxLayout(orientation="horizontal", spacing=dp(8))

        # 左侧: 名单
        left = BoxLayout(orientation="vertical", size_hint_x=0.35, spacing=dp(4))
        left.add_widget(MDLabel(text="名单:", bold=True, size_hint_y=None, height=dp(24)))

        self.list_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
        self.list_box.bind(minimum_height=self.list_box.setter("height"))
        scroll = ScrollView(do_scroll_x=False)
        scroll.add_widget(self.list_box)
        left.add_widget(scroll)
        self._refresh_list()

        input_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(4))
        self.item_input = MDTextField(text="", hint_text="添加", mode="fill", size_hint_x=0.7)
        input_row.add_widget(self.item_input)
        input_row.add_widget(MDIconButton(icon="plus", on_release=lambda x: self._add_item()))
        left.add_widget(input_row)

        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36), spacing=dp(4))
        btn_row.add_widget(MDFlatButton(text="删除", on_release=lambda x: self._remove_item()))
        btn_row.add_widget(MDFlatButton(text="清空", on_release=lambda x: self._clear_items()))
        left.add_widget(btn_row)
        hbox.add_widget(left)

        # 右侧: 抽签
        right = BoxLayout(orientation="vertical", spacing=dp(8))
        self.result_label = MDLabel(text="🎯", font_style="H1", halign="center", size_hint_y=0.3)
        right.add_widget(self.result_label)
        self.name_label = MDLabel(text="准备就绪", font_style="H4", halign="center",
                                   theme_text_color="Secondary", size_hint_y=0.15)
        right.add_widget(self.name_label)

        draw_ctrl = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        draw_ctrl.add_widget(MDLabel(text="人数:", size_hint_x=0.15))
        self.draw_count_input = MDTextField(text="1", mode="fill", size_hint_x=0.1, input_filter="int")
        draw_ctrl.add_widget(self.draw_count_input)
        draw_ctrl.add_widget(MDRaisedButton(text="🎯 抽签!", on_release=lambda x: self._draw()))
        hbox.add_widget(right)

        self.add_widget(hbox)

        # 历史
        self.add_widget(MDLabel(text="抽签记录:", bold=True, size_hint_y=None, height=dp(24)))
        self.hist_text = MDLabel(text="(空)", size_hint_y=0.2, font_style="Caption")
        self.hist_text.bind(texture_size=lambda *a: setattr(self.hist_text, 'height',
                                                             min(self.hist_text.texture_size[1], dp(150))))
        self.add_widget(self.hist_text)

        clear_hist = MDFlatButton(text="清空记录", on_release=lambda x: self._clear_history(),
                                   size_hint_y=None, height=dp(32))
        self.add_widget(clear_hist)

    def _refresh_list(self):
        self.list_box.clear_widgets()
        for item in self.items:
            lbl = MDLabel(text=f"• {item}", font_style="Caption", size_hint_y=None, height=dp(24))
            self.list_box.add_widget(lbl)

    def _add_item(self):
        text = self.item_input.text.strip()
        if text:
            self.items.append(text)
            self.item_input.text = ""
            self._refresh_list()

    def _remove_item(self):
        if self.items:
            self.items.pop()
            self._refresh_list()

    def _clear_items(self):
        self.items.clear()
        self._refresh_list()

    def _draw(self):
        if not self.items:
            Snackbar(text="名单为空，请先添加").open()
            return

        try:
            count = min(int(self.draw_count_input.text or "1"), len(self.items))
        except:
            count = 1

        picks = random.sample(self.items, count)
        self._animate_draw(picks, 0)

    def _animate_draw(self, picks, step):
        if step >= 10:
            names = ", ".join(picks)
            self.name_label.text = names
            self.name_label.theme_text_color = "Primary"
            self.result_label.text = "🎉"

            current = self.hist_text.text
            entry = f"• {names}"
            self.hist_text.text = (current + "\n" + entry) if current != "(空)" else entry
            return

        self.name_label.text = random.choice(self.items)
        self.name_label.theme_text_color = "Hint"
        self.result_label.text = "🎯"
        Clock.schedule_once(lambda dt: self._animate_draw(picks, step + 1), 0.08)

    def _clear_history(self):
        self.hist_text.text = "(空)"
        self.name_label.text = "准备就绪"
        self.name_label.theme_text_color = "Secondary"
        self.result_label.text = "🎯"


# ════════════════════════════════════════════════════════════
# 🪙 抛硬币
# ════════════════════════════════════════════════════════════

class CoinContent(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(12)
        self.padding = dp(16)
        self.stats = {"正面": 0, "反面": 0, "总次数": 0}
        Clock.schedule_once(self._build_ui, 0)

    def _build_ui(self, dt=None):
        self.clear_widgets()

        self.coin_label = MDLabel(text="🪙", font_style="H1", halign="center", size_hint_y=0.3)
        self.add_widget(self.coin_label)

        self.result_label = MDLabel(text="点击抛硬币！", font_style="H5", halign="center",
                                     size_hint_y=0.1)
        self.add_widget(self.result_label)

        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        btn_row.add_widget(MDRaisedButton(text="🪙 抛一次", on_release=lambda x: self._flip_once()))
        btn_row.add_widget(MDRaisedButton(text="抛 10 次", on_release=lambda x: self._flip_multi(10)))
        btn_row.add_widget(MDRaisedButton(text="抛 100 次", on_release=lambda x: self._flip_multi(100)))
        self.add_widget(btn_row)

        # 统计
        self.add_widget(MDLabel(text="统计:", bold=True, size_hint_y=None, height=dp(24)))
        self.stats_label = MDLabel(text="正面: 0 (0%) | 反面: 0 (0%) | 总次数: 0",
                                    size_hint_y=None, height=dp(36), font_style="H6")
        self.add_widget(self.stats_label)

        self.add_widget(MDFlatButton(text="重置统计", on_release=lambda x: self._reset_stats(),
                                      size_hint_y=None, height=dp(36)))

    def _flip_once(self):
        self._animate_flip(0)

    def _flip_multi(self, n):
        heads = sum(1 for _ in range(n) if random.choice([True, False]))
        tails = n - heads

        self.stats["正面"] += heads
        self.stats["反面"] += tails
        self.stats["总次数"] += n

        result = "正面" if heads > tails else "反面" if tails > heads else "平局"
        self.result_label.text = f"抛 {n} 次: 正面 {heads}, 反面 {tails} → {result}"
        self._update_stats()

    def _animate_flip(self, step):
        if step >= 12:
            result = random.choice(["正面", "反面"])
            self.stats[result] += 1
            self.stats["总次数"] += 1
            self.result_label.text = f"🎉 {result}！"
            self._update_stats()
            return
        self.coin_label.text = random.choice(["🪙", "💫"])
        Clock.schedule_once(lambda dt: self._animate_flip(step + 1), 0.05)

    def _update_stats(self):
        total = self.stats["总次数"]
        hp = (self.stats["正面"] / total * 100) if total else 0
        tp = (self.stats["反面"] / total * 100) if total else 0
        self.stats_label.text = f"正面: {self.stats['正面']} ({hp:.1f}%) | 反面: {self.stats['反面']} ({tp:.1f}%) | 总次数: {total}"

    def _reset_stats(self):
        self.stats = {"正面": 0, "反面": 0, "总次数": 0}
        self._update_stats()
        self.result_label.text = "已重置"


# ════════════════════════════════════════════════════════════
# 🎨 随机颜色
# ════════════════════════════════════════════════════════════

class ColorContent(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(8)
        self.padding = dp(16)
        Clock.schedule_once(self._build_ui, 0)

    def _build_ui(self, dt=None):
        self.clear_widgets()

        # 颜色预览区域 (用 BoxLayout + 背景色实现)
        self.color_preview = BoxLayout(orientation="vertical", size_hint_y=0.25,
                                        canvas_before=None)
        self.add_widget(self.color_preview)

        # 颜色信息
        info = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(8))
        self.hex_label = MDLabel(text="#3498DB", font_style="H5", size_hint_x=0.3,
                                  halign="center")
        info.add_widget(self.hex_label)
        self.rgb_label = MDLabel(text="RGB(52,152,219)", font_style="Caption", size_hint_x=0.35,
                                  halign="center")
        info.add_widget(self.rgb_label)
        self.add_widget(info)

        # 按钮
        btn_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(4))
        btn_row.add_widget(MDRaisedButton(text="🎲 随机", on_release=lambda x: self._random("all")))
        btn_row.add_widget(MDFlatButton(text="亮色", on_release=lambda x: self._random("bright")))
        btn_row.add_widget(MDFlatButton(text="暗色", on_release=lambda x: self._random("dark")))
        btn_row.add_widget(MDFlatButton(text="暖色", on_release=lambda x: self._random("warm")))
        btn_row.add_widget(MDFlatButton(text="冷色", on_release=lambda x: self._random("cool")))
        self.add_widget(btn_row)

        # 配色方案
        self.add_widget(MDLabel(text="配色方案:", bold=True, size_hint_y=None, height=dp(24)))
        scheme_ctrl = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40), spacing=dp(8))
        scheme_ctrl.add_widget(MDLabel(text="数量:", size_hint_x=0.1))
        self.scheme_count_input = MDTextField(text="5", mode="fill", size_hint_x=0.1, input_filter="int")
        scheme_ctrl.add_widget(self.scheme_count_input)
        scheme_ctrl.add_widget(MDRaisedButton(text="🎨 生成", on_release=lambda x: self._generate_scheme()))
        self.add_widget(scheme_ctrl)

        # 配色展示 (用 GridLayout 动态生成色块)
        self.scheme_grid = GridLayout(cols=5, spacing=dp(2), size_hint_y=0.3)
        self.add_widget(self.scheme_grid)

        self._random("all")

    def _random(self, mode="all"):
        if mode == "all":
            r, g, b = random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
        elif mode == "bright":
            r, g, b = random.randint(128, 255), random.randint(128, 255), random.randint(128, 255)
        elif mode == "dark":
            r, g, b = random.randint(0, 128), random.randint(0, 128), random.randint(0, 128)
        elif mode == "warm":
            r, g = random.randint(150, 255), random.randint(50, 200)
            b = random.randint(0, 100)
        elif mode == "cool":
            r, b = random.randint(0, 100), random.randint(150, 255)
            g = random.randint(100, 230)

        hex_c = f"#{r:02x}{g:02x}{b:02x}".upper()
        self.hex_label.text = hex_c
        self.rgb_label.text = f"RGB({r},{g},{b})"

        # 设置预览背景色
        self.color_preview.canvas.before.clear()
        with self.color_preview.canvas.before:
            GColor(r/255, g/255, b/255, 1)
            Rectangle(pos=self.color_preview.pos, size=self.color_preview.size)
        self.color_preview.bind(pos=lambda *a: self._update_preview_bg(r, g, b))

    def _update_preview_bg(self, r, g, b, *args):
        self.color_preview.canvas.before.clear()
        with self.color_preview.canvas.before:
            GColor(r/255, g/255, b/255, 1)
            Rectangle(pos=self.color_preview.pos, size=self.color_preview.size)

    def _generate_scheme(self):
        try:
            n = int(self.scheme_count_input.text or "5")
        except:
            n = 5

        self.scheme_grid.cols = min(n, 5)
        self.scheme_grid.clear_widgets()

        for i in range(n):
            r = random.randint(0, 255)
            g = random.randint(0, 255)
            b = random.randint(0, 255)
            box = BoxLayout(orientation="vertical")
            box.canvas.before.clear()
            with box.canvas.before:
                GColor(r/255, g/255, b/255, 1)
                Rectangle(pos=box.pos, size=box.size)
            hex_c = f"#{r:02x}{g:02x}{b:02x}".upper()

            lbl = MDLabel(text=hex_c, font_style="Caption", halign="center",
                           size_hint_y=0.2)
            box.add_widget(lbl)
            self.scheme_grid.add_widget(box)
