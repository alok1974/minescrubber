import os
import random


from . import imager, conf, animator
from .qt import BaseDialog, QtWidgets, QtCore, QtGui


class MainWidget(BaseDialog):
    CELL_SELECTED_SIGNAL = QtCore.Signal(tuple)
    CELL_FLAGGED_SIGNAL = QtCore.Signal(tuple)
    NEW_GAME_SIGNAL = QtCore.Signal(tuple)

    def __init__(self, parent=None):
        super().__init__(parent=parent)

    def init_board(self, board):
        self._board = board
        self._last_swept = self._board.last_swept
        self._board_image = imager.BoardImage(self._board)
        self._ac = animator.AnimController(board_image=self._board_image)
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

        self._marked_mines_lcd = QtWidgets.QLCDNumber()
        self._marked_mines_lcd.display('000')
        self._marked_mines_lcd.setDigitCount(3)
        self._marked_mines_lcd.setSegmentStyle(QtWidgets.QLCDNumber.Flat)
        self._marked_mines_lcd.setStyleSheet(
            "color: red;"
            "background-color: rgb(50, 50, 50);"
            "border: none;"
        )

        self._timer_lcd = QtWidgets.QLCDNumber()
        self._timer_lcd.display('000')
        self._timer_lcd.setDigitCount(3)
        self._timer_lcd.setSegmentStyle(QtWidgets.QLCDNumber.Flat)
        self._timer_lcd.setStyleSheet(
            "color: red;"
            "background-color: rgb(50, 50, 50);"
            "border: none;"
        )

        self._top_layout.addWidget(self._marked_mines_lcd, 1)
        self._top_layout.addWidget(self._restart_image_label)
        self._top_layout.addWidget(self._timer_lcd, 1)

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
        self._ac.UPDATE_SIGNAL.connect(self._update_image_label)
        self._ac.DONE_SIGNAL.connect(self._anim_done)

    def _on_timer_timeout(self):
        self._time += 1
        self._timer_lcd.display(str(self._time).zfill(3))

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

        min_cells, max_cells = self._board.MIN_CELLS, self._board.MAX_CELLS
        invalid_width = not(min_cells <= width <= max_cells)
        invalid_height = not(min_cells <= height <= max_cells)
        if invalid_width or invalid_height:
            error_msg = (
                f'Fields should be between '
                f'{min_cells} and {max_cells}!')
            msg_box = QtWidgets.QErrorMessage(parent=self)
            msg_box.showMessage(error_msg)
            return

        self._marked_mines_lcd.display(str(nb_mines).zfill(3))
        self._restart_image_label.setPixmap(
            QtGui.QPixmap(
                os.path.join(conf.RESOURCE_DIR, 'happy_48.png')
            )
        )
        self._restart_image_label.setFocus()
        self._timer.start(1000)
        self._time = 0
        self._timer_lcd.display(str(self._time).zfill(3))
        self._last_swept = []

        self.NEW_GAME_SIGNAL.emit(args)

    def _on_image_clicked(self, event):
        selected_cell = self._board_image.pixel_to_slot(event.x(), event.y())
        if selected_cell is None:
            return

        button = event.button()
        if button == QtCore.Qt.MouseButton.RightButton:
            signal = self.CELL_FLAGGED_SIGNAL
        else:
            signal = self.CELL_SELECTED_SIGNAL

        signal.emit(selected_cell)

    def refresh(self, board, init_image=True):
        self._board = board

        if init_image:
            self._board_image.init_image(self._board)

        self._image_label.setMinimumWidth(self._board_image.qt_image.width())
        self._image_label.setMinimumHeight(self._board_image.qt_image.height())
        self.setFixedSize(
            max(304, self._board_image.qt_image.width() + 40),
            self._board_image.qt_image.height() + 140
        )

        remaining_mines = max(
            0,
            self._board.nb_mines - self._board.nb_flagged,
        )
        self._marked_mines_lcd.display(str(remaining_mines).zfill(3))

        if self._last_swept != self._board.last_swept:
            self._last_swept = self._board.last_swept
            last_swept_cells = []
            for slot in self._last_swept:
                last_swept_cells.append(self._board.get_cell(slot))

            self._ac.method = random.choice(list(animator.METHOD))
            self._ac.reveal_cells(
                cells=last_swept_cells,
                fill=self._board_image.UNCOVERED_COLOR,
                fill_from=self._board_image.COVERED_COLOR,
            )
        else:
            self._update_image_label()

    def _update_image_label(self):
        self._pixmap = QtGui.QPixmap.fromImage(self._board_image.qt_image)
        self._image_label.setPixmap(self._pixmap)

    def _anim_done(self):
        self._board_image.init_image(self._board)
        self._update_image_label()

    def game_over(self, board):
        self.refresh(board=board)
        self._timer.stop()
        self._restart_image_label.setPixmap(
            QtGui.QPixmap(
                os.path.join(conf.RESOURCE_DIR, 'sad_48.png')
            )
        )

    def game_solved(self, board):
        self.refresh(board=board)
        self._timer.stop()
        self._restart_image_label.setPixmap(
            QtGui.QPixmap(
                os.path.join(conf.RESOURCE_DIR, 'shine_48.png')
            )
        )
