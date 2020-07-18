import os
from PySide2 import QtWidgets, QtGui, QtCore


from . import imager, conf


class MainWidget(QtWidgets.QDialog):
    CELL_SELECTED_SIGNAL = QtCore.Signal(tuple)
    NEW_GAME_SIGNAL = QtCore.Signal(tuple)

    def __init__(self, board, parent=None):
        super().__init__(parent=parent)
        self._board = board
        self._board_image = imager.BoardImage(self._board)
        self._setup_ui()
        self._timer = QtCore.QTimer()
        self._timer.start(1000)
        self._time = 0
        self._connect_signals()

    def _setup_ui(self):
        title = 'Minescrubber'
        self.setWindowTitle(title)
        self.setFixedSize(
            max(304, self._board_image.qt_image.width() + 40),
            self._board_image.qt_image.height() + 140
        )

        stylesheet = _get_stylesheet('dark_01')
        self.setStyleSheet(stylesheet)

        self._main_layout = QtWidgets.QVBoxLayout(self)

        # Add top layout
        self._top_layout = self._create_top_layout()
        self._main_layout.addLayout(self._top_layout)

        # Add image layout
        self._image_layout_outer = self._create_image_layout()
        self._main_layout.addLayout(self._image_layout_outer)

        # Add bottom layout
        self._bottom_layout = self._create_bottom_layout()
        self._main_layout.addLayout(self._bottom_layout)

        # Move focus away from the line edits
        self._restart_image_label.setFocus()

    def _create_top_layout(self):
        self._top_layout = QtWidgets.QHBoxLayout()

        # Create Image Label to act as a button
        self._restart_image_label = QtWidgets.QLabel()
        self._restart_image_label.setPixmap(
            QtGui.QPixmap(
                os.path.join(conf.RESOURCE_DIR, 'happy_48.png')
            )
        )

        self._marked_mines_label = QtWidgets.QLabel()
        self._marked_mines_label.setText(
            str(self._board.nb_mines).zfill(3)
        )
        font = self._marked_mines_label.font()
        font.setPointSize(30)
        self._marked_mines_label.setFont(font)
        self._marked_mines_label.setAlignment(QtCore.Qt.AlignCenter)
        self._marked_mines_label.setStyleSheet(
            "color: red;"
            "background-color: rgb(50, 50, 50);"
            "selection-color: rgb(50, 50, 50);"
            "selection-background-color: red;"
        )

        self._timer_label = QtWidgets.QLabel()
        self._timer_label.setText('000')
        font = self._timer_label.font()
        font.setPointSize(30)
        self._timer_label.setFont(font)
        self._timer_label.setAlignment(QtCore.Qt.AlignCenter)
        self._timer_label.setStyleSheet(
            "color: red;"
            "background-color: rgb(50, 50, 50);"
            "selection-color: rgb(50, 50, 50);"
            "selection-background-color: red;"
        )

        self._top_layout.addWidget(self._marked_mines_label, 1)
        self._top_layout.addWidget(self._restart_image_label)
        self._top_layout.addWidget(self._timer_label, 1)

        return self._top_layout

    def _create_image_layout(self):
        self._image_layout_inner = QtWidgets.QHBoxLayout()

        # Create Pixmap
        self._pixmap = QtGui.QPixmap.fromImage(self._board_image.qt_image)

        # Create Label and add the pixmap
        self._image_label = QtWidgets.QLabel()
        self._image_label.setPixmap(self._pixmap)
        self._image_label.setMinimumWidth(self._board_image.qt_image.width())
        self._image_label.setMinimumHeight(self._board_image.qt_image.height())
        self._image_label.setCursor(
            QtGui.QCursor(QtCore.Qt.PointingHandCursor)
        )

        # Create an innner layout to prohibit horizontal stretching of the
        # image label
        self._image_layout_inner.addWidget(self._image_label)

        # Adding a spacer to the right of the label to make sure that the
        # image label does not stretch otherwise we cannot get the right
        # mouse position to pick the pixel
        self._image_layout_inner.addStretch(1)

        # Create an outer layout to prohibit the vertical stretching
        # of the image label
        self._image_layout_outer = QtWidgets.QVBoxLayout()
        self._image_layout_outer.addLayout(self._image_layout_inner)

        # Adding a spacer to the bottom of the label to make sure that the
        # image label does not stretch otherwise we cannot get the right
        # mouse position to pick the pixel
        self._image_layout_outer.addStretch(1)
        return self._image_layout_outer

    def _create_bottom_layout(self):
        self._bottom_layout = QtWidgets.QHBoxLayout()

        self._fields_label = QtWidgets.QLabel("Fields")
        font = self._fields_label.font()
        font.setPointSize(18)
        self._fields_label.setFont(font)

        self._field_x_line_edit = QtWidgets.QLineEdit("9")
        self._field_x_line_edit.setFixedHeight(32)
        self._field_x_line_edit.setFixedWidth(32)
        self._field_x_line_edit.setAlignment(QtCore.Qt.AlignCenter)
        font = self._field_x_line_edit.font()
        font.setPointSize(18)
        self._field_x_line_edit.setFont(font)

        self._x_label = QtWidgets.QLabel("X")
        self._field_y_line_edit = QtWidgets.QLineEdit("9")
        self._field_y_line_edit.setFixedHeight(32)
        self._field_y_line_edit.setFixedWidth(32)
        self._field_y_line_edit.setAlignment(QtCore.Qt.AlignCenter)
        font = self._field_y_line_edit.font()
        font.setPointSize(18)
        self._field_y_line_edit.setFont(font)

        self._mines_label = QtWidgets.QLabel("Mines")
        font = self._mines_label.font()
        font.setPointSize(18)
        self._mines_label.setFont(font)

        self._fields_label.setFont(font)
        self._mines_line_edit = QtWidgets.QLineEdit("10")
        self._mines_line_edit.setFixedHeight(32)
        self._mines_line_edit.setFixedWidth(32)
        self._mines_line_edit.setAlignment(QtCore.Qt.AlignCenter)
        font = self._mines_line_edit.font()
        font.setPointSize(18)
        self._mines_line_edit.setFont(font)

        self._bottom_layout.addWidget(self._fields_label)
        self._bottom_layout.addWidget(self._field_x_line_edit)
        self._bottom_layout.addWidget(self._x_label)
        self._bottom_layout.addWidget(self._field_y_line_edit)
        self._bottom_layout.addStretch(1)
        self._bottom_layout.addWidget(self._mines_label)
        self._bottom_layout.addWidget(self._mines_line_edit)

        return self._bottom_layout

    def _connect_signals(self):
        self._restart_image_label.mousePressEvent = self._restart
        self._image_label.mousePressEvent = self._on_image_clicked
        self._timer.timeout.connect(self._on_timer_timeout)

    def _on_timer_timeout(self):
        self._time += 1
        self._timer_label.setText(str(self._time).zfill(3))

    def _restart(self, event=None):
        try:
            width = int(self._field_x_line_edit.text())
            height = int(self._field_y_line_edit.text())
            nb_mines = int(self._mines_line_edit.text())
            args = (width, height, nb_mines)
        except ValueError:
            error_msg = 'Fields, Mines can only be valid numbers!'
            msg_box = QtWidgets.QErrorMessage(parent=self)
            msg_box.showMessage(error_msg)
            return

        if not(5 <= width <= 16) or not(5 <= height <= 16):
            error_msg = 'Fields should be between 5 and 16!'
            msg_box = QtWidgets.QErrorMessage(parent=self)
            msg_box.showMessage(error_msg)
            return

        self.NEW_GAME_SIGNAL.emit(args)
        self._marked_mines_label.setText(
            str(nb_mines).zfill(3)
        )
        self._restart_image_label.setPixmap(
            QtGui.QPixmap(
                os.path.join(conf.RESOURCE_DIR, 'happy_48.png')
            )
        )
        self._restart_image_label.setFocus()
        self._timer.start(1000)
        self._time = 0
        self._timer_label.setText(str(self._time).zfill(3))

    def _on_image_clicked(self, event):
        selected_cell = self._board_image.pixel_to_slot(event.x(), event.y())
        if selected_cell is None:
            return

        self.CELL_SELECTED_SIGNAL.emit(selected_cell)

    def refresh(self, board):
        self._board = board
        self._board_image.init_image(self._board)
        self.setFixedSize(
            max(304, self._board_image.qt_image.width() + 40),
            self._board_image.qt_image.height() + 140
        )
        self._pixmap = QtGui.QPixmap.fromImage(self._board_image.qt_image)
        self._image_label.setPixmap(self._pixmap)
        self._image_label.setMinimumWidth(self._board_image.qt_image.width())
        self._image_label.setMinimumHeight(self._board_image.qt_image.height())

    def game_over(self, board):
        self.refresh(board=board)
        self._timer.stop()
        self._restart_image_label.setPixmap(
            QtGui.QPixmap(
                os.path.join(conf.RESOURCE_DIR, 'sad_48.png')
            )
        )


def _get_stylesheet(stylesheet_name='dark_01'):
    stylesheet = None
    stylesheet_file_path = os.path.join(
        conf.RESOURCE_DIR,
        f'{stylesheet_name}.css',
    )
    with open(stylesheet_file_path, 'r') as f:
        stylesheet = f.read()

    return stylesheet
