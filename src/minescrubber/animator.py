import enum
import io
import functools


from PIL import ImageDraw, Image


from .qt import BaseDialog, QtCore, QtWidgets, QtGui
from .imager import COLOR


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


@enum.unique
class METHOD(enum.Enum):
    ANIMATE_RECTANGLE = 0
    FADE = 1
    FLIP = 2


class SingleAnimController(QtCore.QObject):
    UPDATE_SIGNAL = QtCore.Signal()
    DONE_SIGNAL = QtCore.Signal(QtCore.QObject)
    DEFAULT_TIME = 1  # In seconds

    def __init__(self, board_image=None, parent=None):
        super().__init__(parent=parent)
        self._is_running = False
        self._board_image = board_image
        self._time = 0
        self._step = 0
        self._fps = 6
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
    def fps(self):
        return self._fps

    @fps.setter
    def fps(self, val):
        self._fps = val

    @property
    def qt_image(self):
        return self._board_image.qt_image

    def animate_rectangle(self, x, y, x_size, y_size, fill=None, time=None):
        import random
        axis = random.choice(list(AXIS))
        x_dir = random.choice(list(DIRECTION))
        y_dir = random.choice(list(DIRECTION))

        if axis == AXIS.XY:
            if x_dir == DIRECTION.LEFT:
                x += x_size
            if y_dir == DIRECTION.TOP:
                y += y_size
        elif axis == AXIS.X:
            if x_dir == DIRECTION.LEFT:
                x += x_size
        elif axis == AXIS.Y:
            if y_dir == DIRECTION.TOP:
                y += y_size

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

    def fade(self, x, y, x_size, y_size, fill_to, fill_from, time=None):
        animate_func_args = (x, y, x_size, y_size, fill_to, fill_from)
        animate_func_kwargs = {}
        self._animate_func_to_use = functools.partial(
            self._fade,
            *animate_func_args,
            **animate_func_kwargs,
        )

        self._run(
            time=time,
        )

    def flip(self, x, y, x_size, y_size, fill_to, fill_from, time=None):
        animate_func_args = (x, y, x_size, y_size, fill_to, fill_from)
        animate_func_kwargs = {}
        self._animate_func_to_use = functools.partial(
            self._flip,
            *animate_func_args,
            **animate_func_kwargs,
        )

        self._run(
            time=time,
        )

    def _run(self, time=None):
        time = time or self.DEFAULT_TIME
        self._time = time * 1000
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

    def _rectangle(
            self, x, y, x_size, y_size, axis=AXIS.XY,
            x_dir=DIRECTION.RIGHT, y_dir=DIRECTION.BOTTOM, fill=None
    ):
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

    def _fade(self, x, y, x_size, y_size, fill_to, fill_from):
        fill_from = self._fix_alpha(fill_from)

        alpha = int(255 * self._frames_played / self._nb_frames)
        r, g, b = fill_to
        fill_to = (r, g, b, alpha)

        result = self._alpha_blend(fill_from, fill_to)

        self._draw_context.rectangle(
            [
                (x, y),
                (x + x_size, y + y_size),
            ],
            fill=result,
        )

    def _fix_alpha(self, color, normalized=False):
        alpha = 1 if normalized else 255
        if len(color) == 3:
            return (*color, alpha)
        return color

    def _alpha_blend(self, src, dst):
        src = self._normalize_color(src)
        r_src, g_src, b_src, a_src = src

        dst = self._normalize_color(dst)
        r_dst, g_dst, b_dst, a_dst = dst

        a_mix = a_src + a_dst - (a_src * a_dst)

        r_mix = self._blend(r_src, a_src, r_dst, a_dst, a_mix)
        g_mix = self._blend(g_src, a_src, g_dst, a_dst, a_mix)
        b_mix = self._blend(b_src, a_src, b_dst, a_dst, a_mix)
        result = r_mix, g_mix, b_mix, a_mix

        return self._denormalize_color(result)

    def _blend(self, c_src, a_src, c_dst, a_dst, a_mix):
        if a_mix == 0:
            return 0
        return ((c_dst * a_dst) + (c_src * a_src * (1 - a_dst))) / a_mix

    def _normalize_color(self, color):
        color = self._fix_alpha(color)
        return tuple(map(lambda x: x / 255, color))

    def _denormalize_color(self, color):
        color = self._fix_alpha(color, normalized=True)
        return tuple(map(lambda x: int(x * 255), color))

    def _flip(self, x, y, x_size, y_size, fill_to, fill_from):
        orig_incr = self._frames_played / self._nb_frames
        mid_color = COLOR.extra_dark_gray

        incr = None
        if orig_incr <= 0.5:
            incr = self._rescale(
                val=orig_incr,
                min_in=0.0,
                max_in=0.5,
                min_out=0.0,
                max_out=1.0,
            )

            src = self._fix_alpha(fill_from)
            alpha = int(255 * incr)
            r, g, b = mid_color
            dst = (r, g, b, alpha)
            fill = self._alpha_blend(src, dst)

            r1_start = (x, y)
            r1_end = (x + int(x_size * incr / 2), y + y_size)
            r2_start = (x + x_size - int(x_size * incr / 2) + 1, y)
            r2_end = (x + x_size, y + y_size)
        else:
            incr = self._rescale(
                val=orig_incr,
                min_in=0.5,
                max_in=1.0,
                min_out=0.0,
                max_out=1.0,
            )

            src = self._fix_alpha(mid_color)
            alpha = int(255 * incr)
            r, g, b = fill_to
            dst = (r, g, b, alpha)
            fill = self._alpha_blend(src, dst)
            r1_start = (
                x + int(x_size / 2) - int(x_size * incr / 2),
                y,
            )

            r1_end = (
                x + int(x_size / 2),
                y + y_size,
            )

            r2_start = (
                x + int(x_size / 2) + 1,
                y,
            )

            r2_end = (
                x + int(x_size / 2) + 1 + int(x_size * incr / 2),
                y + y_size,
            )

        # First rect
        self._draw_context.rectangle(
            [r1_start, r1_end],
            fill=fill,
        )

        # Second rect
        self._draw_context.rectangle(
            [r2_start, r2_end],
            fill=fill,
        )

    def _rescale(self, val, min_in, max_in, min_out, max_out):
        if min_in == max_in:
            return 0
        return min_out + (
            (val - min_in) * (max_out - min_out) / (max_in - min_in)
        )


class AnimController(QtCore.QObject):
    UPDATE_SIGNAL = QtCore.Signal()
    DONE_SIGNAL = QtCore.Signal()
    DEFAULT_ANIM_SETTINGS = {
        METHOD.ANIMATE_RECTANGLE: {
            'time': 0.1,
            'fps': 6,
        },
        METHOD.FLIP: {
            'time': 0.5,
            'fps': 20,
        },
        METHOD.FADE: {
            'time': 0.1,
            'fps': 6,
        },
    }

    def __init__(self, board_image, method=METHOD.FADE, parent=None):
        super().__init__(parent=parent)
        self._board_image = board_image
        self._single_controllers = []
        self._method = method
        self._fps = 6

    @property
    def method(self):
        return self._method

    @method.setter
    def method(self, method):
        self._method = method

    @property
    def fps(self):
        return self._fps

    @fps.setter
    def fps(self, val):
        self._fps = val

    @property
    def qt_image(self):
        return self._board_image.qt_image

    def reveal_cells(
            self, cells, fill,
            fill_from=None, time=None, fps=None
    ):
        coords = self._get_cell_coordinates(cells)
        for coord in coords:
            x, y = coord
            sac = SingleAnimController(board_image=self._board_image)
            self._single_controllers.append(sac)
            if self.method == METHOD.ANIMATE_RECTANGLE:
                self._animate_rectangle(sac, x, y, fill, time, fps)
            elif self.method == METHOD.FADE:
                self._fade(sac, x, y, fill, fill_from, time, fps)
            elif self.method == METHOD.FLIP:
                self._flip(sac, x, y, fill, fill_from, time, fps)
            else:
                error_msg = f'The method {self.method} is not implemented'
                raise RuntimeError(error_msg)

            sac.UPDATE_SIGNAL.connect(self._update)
            sac.DONE_SIGNAL.connect(self._done)

    def _animate_rectangle(self, sac, x, y, fill, time, fps):
        time = time or self.DEFAULT_ANIM_SETTINGS[METHOD.ANIMATE_RECTANGLE]['time']
        sac.fps = fps or self.DEFAULT_ANIM_SETTINGS[METHOD.ANIMATE_RECTANGLE]['fps']
        sac.animate_rectangle(
            x=x,
            y=y,
            x_size=self._board_image.cell_image_size - 1,
            y_size=self._board_image.cell_image_size - 1,
            fill=fill,
            time=time,
        )

    def _fade(self, sac, x, y, fill_to, fill_from, time, fps):
        time = time or self.DEFAULT_ANIM_SETTINGS[METHOD.FADE]['time']
        sac.fps = fps or self.DEFAULT_ANIM_SETTINGS[METHOD.FADE]['fps']
        sac.fade(
            x=x,
            y=y,
            x_size=self._board_image.cell_image_size - 1,
            y_size=self._board_image.cell_image_size - 1,
            fill_to=fill_to,
            fill_from=fill_from,
            time=time,
        )

    def _flip(self, sac, x, y, fill_to, fill_from, time, fps):
        time = time or self.DEFAULT_ANIM_SETTINGS[METHOD.FLIP]['time']
        sac.fps = fps or self.DEFAULT_ANIM_SETTINGS[METHOD.FLIP]['fps']
        sac.flip(
            x=x,
            y=y,
            x_size=self._board_image.cell_image_size - 1,
            y_size=self._board_image.cell_image_size - 1,
            fill_to=fill_to,
            fill_from=fill_from,
            time=time,
        )

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


# This widget is used only for testing the animation
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
        self._shuffled_cells = self._get_shuffled_cells()

    def _setup_ui(self):
        title = 'Anim View'
        self.setWindowTitle(title)
        self.setFixedSize(
            max(304, self._ac.qt_image.width() + 40),
            self._ac.qt_image.height() + 180,
        )

        self._main_layout = QtWidgets.QVBoxLayout(self)

        self._pixmap = QtGui.QPixmap.fromImage(self._ac.qt_image)
        self._image_label = QtWidgets.QLabel()
        self._image_label.setPixmap(self._pixmap)

        self._button_layout = QtWidgets.QVBoxLayout()
        self._top_button_layout = QtWidgets.QHBoxLayout()

        self._animate_btn = QtWidgets.QPushButton("Animate")
        self._animate_btn.setFixedHeight(60)

        self._fade_btn = QtWidgets.QPushButton("Fade")
        self._fade_btn.setFixedHeight(60)

        self._flip_btn = QtWidgets.QPushButton("Flip")
        self._flip_btn.setFixedHeight(60)

        self._clear_btn = QtWidgets.QPushButton("Reset")
        self._clear_btn.setFixedHeight(60)

        self._top_button_layout.addWidget(self._animate_btn)
        self._top_button_layout.addWidget(self._fade_btn)
        self._top_button_layout.addWidget(self._flip_btn)

        self._button_layout.addLayout(self._top_button_layout)
        self._button_layout.addWidget(self._clear_btn)

        self._main_layout.addWidget(self._image_label)
        self._main_layout.addLayout(self._button_layout)

        self._clear_btn.setFocus()
        self._image_label.setFocus()

    def _connect_signals(self):
        self._ac.UPDATE_SIGNAL.connect(self._update)
        self._ac.DONE_SIGNAL.connect(self._done)
        self._animate_btn.clicked.connect(self._run_animate_rect)
        self._fade_btn.clicked.connect(self._run_fade)
        self._flip_btn.clicked.connect(self._run_flip)
        self._clear_btn.clicked.connect(self._reset_image)

    def _get_shuffled_cells(self):
        import random
        all_cells = [cell for cell in self._board_image.board.cells]
        random.shuffle(all_cells)
        return all_cells

    def _get_random_cells(self):
        import random
        if len(self._shuffled_cells) == 0:
            return []

        if len(self._shuffled_cells) > 3:
            nb_cells = random.randint(1, int(len(self._shuffled_cells) / 2))
        else:
            nb_cells = len(self._shuffled_cells)

        cells = []
        for _ in range(nb_cells):
            cell = self._shuffled_cells.pop()
            cells.append(cell)

        return cells

    def _run_animate_rect(self):
        import time
        self._ac.method = METHOD.ANIMATE_RECTANGLE
        self._start_time = time.time()
        cells = self._get_random_cells()
        self._ac.reveal_cells(cells=cells, fill=COLOR.light_gray)

    def _run_fade(self):
        import time
        self._ac.method = METHOD.FADE
        self._start_time = time.time()
        cells = self._get_random_cells()
        self._ac.reveal_cells(
            cells=cells,
            fill=COLOR.light_gray,
            fill_from=COLOR.teal,
        )

    def _run_flip(self):
        import time
        self._ac.method = METHOD.FLIP
        self._start_time = time.time()
        cells = self._get_random_cells()
        self._ac.reveal_cells(
            cells=cells,
            fill=COLOR.light_gray,
            fill_from=COLOR.teal,
        )

    def _reset_image(self):
        self._shuffled_cells = self._get_shuffled_cells()
        self._board_image.image = Image.open(self._orig_image_data)
        self._update()

    def _update(self):
        self._pixmap = QtGui.QPixmap.fromImage(self._ac.qt_image)
        self._image_label.setPixmap(self._pixmap)

    def _done(self):
        pass
