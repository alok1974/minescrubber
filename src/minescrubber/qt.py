import os


from PySide2 import QtWidgets, QtCore, QtGui


from . import conf


__all__ = ['BaseDialog', QtCore, QtGui, QtWidgets]


class BaseDialog(QtWidgets.QDialog):
    def __init__(self, stylesheet='dark_01', parent=None):
        super().__init__(parent=parent)
        stylesheet = self._get_stylesheet(stylesheet)
        self.setStyleSheet(stylesheet)

    def _get_stylesheet(self, stylesheet_name):
        stylesheet = None
        stylesheet_file_path = os.path.join(
            conf.RESOURCE_DIR,
            f'{stylesheet_name}.css',
        )
        with open(stylesheet_file_path, 'r') as f:
            stylesheet = f.read()

        return stylesheet
