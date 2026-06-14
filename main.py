"""
MediaToolSuite - Android 版
由 Tkinter 移植为 KivyMD Android 原生应用 (不含视频功能)
"""
import os
import sys
import random

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import platform

from kivymd.app import MDApp
from kivymd.theming import ThemeManager
from kivymd.uix.navigationdrawer import MDNavigationDrawer
from kivymd.uix.screen import MDScreen

# ─── 导入所有模块 Screen ───
from modules.home_screen import HomeScreen
from modules.rename_tool import RenameScreen
from modules.image_resize_tool import ImageResizeScreen
from modules.image_stitch_tool import ImageStitchScreen
from modules.radar_chart_tool import RadarChartScreen
from modules.random_tools import RandomToolsScreen


class MediaToolSuiteApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = "MediaToolSuite"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.theme_style = "Light"
        self.theme_cls.material_style = "M3"

    def build(self):
        Builder.load_file("main.kv")
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home"))
        sm.add_widget(RenameScreen(name="rename"))
        sm.add_widget(ImageResizeScreen(name="image-resize"))
        sm.add_widget(ImageStitchScreen(name="image-stitch"))
        sm.add_widget(RadarChartScreen(name="radar"))
        sm.add_widget(RandomToolsScreen(name="random"))
        return sm

    def switch_screen(self, screen_name):
        """切换到指定工具"""
        self.root.current = screen_name

    def go_home(self):
        """返回首页"""
        self.root.current = "home"

    def on_start(self):
        """启动后绑定 Android 返回键"""
        if platform == "android":
            from kivy.base import EventLoop
            EventLoop.window.bind(on_keyboard=self._on_key)

    def _on_key(self, window, key, *args):
        if key == 27:  # Android Back
            if self.root.current != "home":
                self.root.current = "home"
                return True
        return False


if __name__ == "__main__":
    MediaToolSuiteApp().run()
