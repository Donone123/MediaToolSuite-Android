"""
首页 - 工具卡片网格
"""
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView

from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.toolbar import MDTopAppBar


# 工具配置
# (name, icon, title, subtitle)
TOOLS = [
    ("rename", "📄", "批量重命名", "序号、替换、大小写转换"),
    ("image-resize", "🖼", "图片批处理", "批量缩放、格式转换"),
    ("image-stitch", "🧩", "图片拼接", "多图拼接合成"),
    ("radar", "📊", "雷达图", "多维度数据可视化"),
    ("random", "🎲", "随机工具", "轮盘/骰子/抽签/颜色"),
]


class HomeScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(self.build_ui, 0)

    def build_ui(self, dt=None):
        self.clear_widgets()

        # ─── 顶栏 ───
        toolbar = MDTopAppBar(
            title="MediaToolSuite",
            elevation=2,
            title_align="left",
            md_bg_color=self.theme_cls.primary_color,
        )

        # ─── 欢迎文字 ───
        welcome = MDLabel(
            text="🎉 多媒体工具集\n集成 5 款工具，一站式处理图片和文件",
            font_style="H5",
            halign="center",
            size_hint_y=None,
            height=dp(110),
            theme_text_color="Secondary",
        )

        # ─── 卡片网格 ───
        grid = GridLayout(
            cols=2,
            spacing=dp(12),
            size_hint_y=None,
            padding=[dp(12), dp(8)],
        )
        grid.bind(minimum_height=grid.setter("height"))

        for name, icon, title, sub in TOOLS:
            card = self._make_card(name, icon, title, sub)
            grid.add_widget(card)

        # ─── 滚动容器 ───
        scroll = ScrollView(do_scroll_x=False)
        content = BoxLayout(orientation="vertical", size_hint_y=None)
        content.bind(minimum_height=content.setter("height"))
        content.add_widget(welcome)
        content.add_widget(grid)

        # 版本信息
        version = MDLabel(
            text="v1.0.0 | 点击卡片启动工具",
            font_style="Caption",
            halign="center",
            size_hint_y=None,
            height=dp(40),
            theme_text_color="Hint",
        )
        content.add_widget(version)

        scroll.add_widget(content)

        # ─── 组装 ───
        main_layout = BoxLayout(orientation="vertical")
        main_layout.add_widget(toolbar)
        main_layout.add_widget(scroll)
        self.add_widget(main_layout)

    def _make_card(self, screen_name, icon, title, subtitle):
        card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height=dp(130),
            padding=dp(12),
            spacing=dp(4),
            ripple_behavior=True,
            radius=[dp(12)],
        )

        icon_label = MDLabel(
            text=icon,
            font_style="H3",
            halign="center",
            size_hint_y=None,
            height=dp(50),
        )
        title_label = MDLabel(
            text=title,
            font_style="H6",
            halign="center",
            size_hint_y=None,
            height=dp(26),
            bold=True,
        )
        sub_label = MDLabel(
            text=subtitle,
            font_style="Caption",
            halign="center",
            size_hint_y=None,
            height=dp(20),
            theme_text_color="Secondary",
        )

        card.add_widget(icon_label)
        card.add_widget(title_label)
        card.add_widget(sub_label)

        # 点击跳转
        card.bind(on_release=lambda *a: self._open_tool(screen_name))
        return card

    def _open_tool(self, name):
        app = self._get_app()
        if app:
            app.switch_screen(name)

    def _get_app(self):
        from kivy.app import App
        return App.get_running_app()
