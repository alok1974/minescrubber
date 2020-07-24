import enum
import io
import functools


from PIL import ImageDraw, Image


from .qt import BaseDialog, QtCore, QtWidgets, QtGui


class DIRECTION(enum.Enum):
    LEFT = -1
    RIGHT = 1
    TOP = -1
    BOTTOM = 1


@enum.unique
class AXIS(enum.Enum):
    X = 0
    Y = 1
    XY = 2


class SingleAnimController(QtCore.QObject):
    UPDATE_SIGNAL = QtCore.Signal()
    DONE_SIGNAL = QtCore.Signal(QtCore.QObject)
    DEFAULT_TIME = 1  # In seconds
    DEFAULT_FPS = 6

    def __init__(self, board_image=None, parent=None):
        super().__init__(parent=parent)
        self._is_running = False
        self._board_image = board_image
        self._time = 0
        self._step = 0
        self._fps = 0
        self._nb_frames = 0
        self._frames_played = 0
        self._draw_context = ImageDraw.Draw(self._board_image.image)
        self._animate_func_to_use = None
        self._animate_func_args = None
        self._animate_func_kwargs = None
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self._update)
        self.name = None

    @property
    def is_running(self):
        return self._is_running

    @property
    def qt_image(self):
        return self._board_image.qt_image

    def _run(self, time=None):
        time = time or self.DEFAULT_TIME
        fps = self.DEFAULT_FPS
        self._time = time * 1000
        self._fps = fps
        self._step = self._time / self._fps
        self._nb_frames = int(self._time / self._step)
        self._timer.setInterval(self._step)
        self._timer.start()

    def _update(self):
        if self._frames_played == self._nb_frames:
            self._timer.stop()
            self._time = 0
            self._fps = 0
            self._nb_frames = 0
            self._is_running = False
            self.DONE_SIGNAL.emit(self)
            return

        self._frames_played += 1
        self._time -= self._step
        self._animate_func_to_use()
        self.UPDATE_SIGNAL.emit()

    def animate_rectangle(self, x, y, x_size, y_size, axis=AXIS.XY,
                          x_dir=DIRECTION.RIGHT,
                          y_dir=DIRECTION.BOTTOM, fill=None, time=None):

        animate_func_args = (x, y, x_size, y_size)
        animate_func_kwargs = {
            'axis': axis,
            'x_dir': x_dir,
            'y_dir': y_dir,
            'fill': fill,
        }

        self._animate_func_to_use = functools.partial(
            self._rectangle,
            *animate_func_args,
            **animate_func_kwargs,
        )

        self._run(
            time=time,
        )

    def _rectangle(self, x, y, x_size, y_size, axis=AXIS.XY,
                   x_dir=DIRECTION.RIGHT,
                   y_dir=DIRECTION.BOTTOM, fill=None):

        _x_incr = (
            int(x_size * self._frames_played / self._nb_frames)
            * x_dir.value
        )
        _y_incr = (
            int(y_size * self._frames_played / self._nb_frames)
            * y_dir.value
        )

        x_incr = x_size
        y_incr = y_size
        if axis == AXIS.X:
            x_incr = _x_incr
        elif axis == AXIS.Y:
            y_incr = _y_incr
        elif axis == AXIS.XY:
            x_incr = _x_incr
            y_incr = _y_incr

        self._draw_context.rectangle(
            [
                (x, y),
                (x + x_incr, y + y_incr),
            ],
            fill=fill,
        )


class AnimController(QtCore.QObject):
    UPDATE_SIGNAL = QtCore.Signal()
    DONE_SIGNAL = QtCore.Signal()

    def __init__(self, board_image, parent=None):
        super().__init__(parent=parent)
        self._board_image = board_image
        self._single_controllers = []

    @property
    def qt_image(self):
        return self._board_image.qt_image

    def reveal_cells(self, cells):
        coords = self._get_cell_coordinates(cells)
        for coord in coords:
            x, y = coord
            sac = SingleAnimController(board_image=self._board_image)
            self._single_controllers.append(sac)
            sac.animate_rectangle(
                x=x + self._board_image.cell_image_size - 1,
                y=y + self._board_image.cell_image_size - 1,
                x_size=self._board_image.cell_image_size - 1,
                y_size=self._board_image.cell_image_size - 1,
                x_dir=DIRECTION.LEFT,
                y_dir=DIRECTION.TOP,
                axis=AXIS.XY,
                fill=(255, 0, 0),
                time=0.05,
            )
            sac.UPDATE_SIGNAL.connect(self._update)
            sac.DONE_SIGNAL.connect(self._done)

    def _update(self):
        self.UPDATE_SIGNAL.emit()

    def _done(self, controller_obj):
        self._single_controllers.remove(controller_obj)
        if not self._single_controllers:
            self.DONE_SIGNAL.emit()

    def _get_cell_coordinates(self, cells):
        return list(
            map(
                self._board_image.slot_to_pixel,
                [cell.slot for cell in cells],
            )
        )


class AnimView(BaseDialog):
    def __init__(self, board_image, parent=None):
        super().__init__(parent=parent)
        self._board_image = board_image
        self._ac = AnimController(board_image=self._board_image)
        self._orig_image_data = io.BytesIO()
        self._board_image.image.save(self._orig_image_data, 'PNG')
        self._setup_ui()
        self._connect_signals()
        self._start_time = None

    def _setup_ui(self):
        title = 'Anim View'
        self.setWindowTitle(title)
        self.setFixedSize(
            max(304, self._ac.qt_image.width() + 40),
            self._ac.qt_image.height() + 120,
        )

        self._main_layout = QtWidgets.QVBoxLayout(self)

        self._pixmap = QtGui.QPixmap.fromImage(self._ac.qt_image)
        self._image_label = QtWidgets.QLabel()
        self._image_label.setPixmap(self._pixmap)

        self._button_layout = QtWidgets.QHBoxLayout()

        self._animate_btn = QtWidgets.QPushButton("Run Anim")
        self._animate_btn.setFixedHeight(60)

        self._clear_btn = QtWidgets.QPushButton("Reset")
        self._clear_btn.setFixedHeight(60)

        self._button_layout.addWidget(self._animate_btn)
        self._button_layout.addWidget(self._clear_btn)

        self._main_layout.addWidget(self._image_label)
        self._main_layout.addLayout(self._button_layout)

        self._clear_btn.setFocus()
        self._image_label.setFocus()

    def _connect_signals(self):
        self._ac.UPDATE_SIGNAL.connect(self._update)
        self._ac.DONE_SIGNAL.connect(self._done)
        self._animate_btn.clicked.connect(self._run_anim)
        self._clear_btn.clicked.connect(self._reset_image)

    def _run_anim(self):
        import time
        import random
        all_cells = [cell for cell in self._board_image.board.cells]
        random.shuffle(all_cells)
        cells = all_cells[:int(len(all_cells) / 2)]
        self._start_time = time.time()
        self._ac.reveal_cells(cells)

    def _reset_image(self):
        self._board_image.image = Image.open(self._orig_image_data)
        self._update()

    def _update(self):
        self._pixmap = QtGui.QPixmap.fromImage(self._ac.qt_image)
        self._image_label.setPixmap(self._pixmap)

    def _done(self):
        pass
