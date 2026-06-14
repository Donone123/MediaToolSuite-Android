"""
所有工具屏幕的基类 - 提供统一的顶栏和可滚动内容区
"""
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserIconView, FileChooserListView
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform as kivy_platform

from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.snackbar import Snackbar


class BaseToolScreen(MDScreen):
    """工具基类: 共享方法 (文件选择器、对话框等)"""

    def show_snackbar(self, text, duration=2):
        Snackbar(text=text, duration=duration).open()

    def show_dialog(self, title, text, buttons=None):
        if buttons is None:
            buttons = [MDFlatButton(text="确定", on_release=lambda x: dlg.dismiss())]
        dlg = MDDialog(title=title, text=text, buttons=buttons)
        dlg.open()
        return dlg

    def show_confirm(self, title, text, on_confirm, on_cancel=None):
        dlg = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDFlatButton(text="取消", on_release=lambda x: self._dlg_cancel(dlg, on_cancel)),
                MDRaisedButton(text="确定", on_release=lambda x: self._dlg_confirm(dlg, on_confirm)),
            ],
        )
        dlg.open()
        return dlg

    def _dlg_confirm(self, dlg, cb):
        dlg.dismiss()
        if cb: cb()

    def _dlg_cancel(self, dlg, cb):
        dlg.dismiss()
        if cb: cb()

    def show_file_chooser(self, title="选择文件", callback=None, dir_select=True,
                          filters=None):
        """通用文件/文件夹选择器 (ModalView + FileChooser)"""
        content = BoxLayout(orientation="vertical", spacing=dp(8), padding=dp(8))

        # 标题
        content.add_widget(MDLabel(text=title, font_style="H6", size_hint_y=None, height=dp(36)))

        # 文件选择器
        default_path = "/storage/emulated/0" if kivy_platform == "android" else "/"
        if dir_select:
            fc = FileChooserIconView(path=default_path, dirselect=True)
        else:
            if filters:
                fc = FileChooserListView(path=default_path, filters=filters)
            else:
                fc = FileChooserListView(path=default_path)

        content.add_widget(fc)

        # 按钮行
        btn_bar = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48), spacing=dp(12))
        confirm_btn = MDRaisedButton(text="确定", size_hint_x=0.3)
        cancel_btn = MDFlatButton(text="取消", size_hint_x=0.3)

        btn_bar.add_widget(cancel_btn)
        btn_bar.add_widget(confirm_btn)
        content.add_widget(btn_bar)

        modal = ModalView(size_hint=(0.92, 0.92), auto_dismiss=True)
        modal.add_widget(content)

        def on_confirm(*args):
            sel = fc.selection
            if sel:
                if callback:
                    callback(str(sel[0]))
                modal.dismiss()
            else:
                self.show_snackbar("请先选择一个路径")
        confirm_btn.bind(on_release=on_confirm)
        cancel_btn.bind(on_release=lambda x: modal.dismiss())
        modal.open()

    def go_home(self):
        app = self._get_app()
        if app:
            app.go_home()

    def _get_app(self):
        from kivy.app import App
        return App.get_running_app()
