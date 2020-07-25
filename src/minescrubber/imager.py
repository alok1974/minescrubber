import enum

from PIL import Image, ImageFont, ImageDraw, ImageQt


from . import conf


@enum.unique
class CELL_STYLE(enum.Enum):
    covered = 0
    uncovered = 1


@enum.unique
class CELL_DRAW_METHOD(enum.Enum):
    flag = 0
    mine = 1
    hint = 2
    solved = 3


class COLOR:
    white = (255, 255, 255)
    black = (0, 0, 0)
    teal = (145, 156, 255)
    light_gray = (200, 200, 200)
    extra_dark_gray = (27, 27, 27)
    blue = (0, 0, 255)
    red = (255, 0, 0)
    dark_red = (200, 0, 0)
    green = (0, 255, 0)
    dark_green = (0, 100, 0)
    dark_gray = (80, 80, 80)
    very_dark_gray = (60, 60, 60)


class BoardImage:
    EDGE_WIDTH_CONTROL = 12  # Lesser produces thicker edges (12 is ideal)
    COVERED_COLOR = COLOR.teal
    UNCOVERED_COLOR = COLOR.light_gray

    def __init__(self, board):
        self.init_image(board=board)

    @property
    def qt_image(self):
        return ImageQt.ImageQt(self._board_image)

    @property
    def board(self):
        return self._board

    @property
    def image(self):
        return self._board_image

    @image.setter
    def image(self, val):
        self._board_image = val

    @property
    def width(self):
        return self._board_image.width

    @property
    def height(self):
        return self._board_image.height

    @property
    def is_solved(self):
        return self._board.mine_slots == sorted(
            self._board.covered_slots +
            self._board.flagged_slots
        )

    def init_image(self, board):
        self._board = board
        self.cell_image_size = min(
            min(48, int(432 / self._board.width)),
            min(48, int(432 / self._board.height))
        )

        self._edge_width = int(self.cell_image_size / self.EDGE_WIDTH_CONTROL)

        self._cell_image_covered = self._create_cell_image(
            cell_state=CELL_STYLE.covered
        )

        self._cell_image_uncovered = self._create_cell_image(
            cell_state=CELL_STYLE.uncovered
        )
        self._board_image = self._create_board_image()
        self.draw()

    def pixel_to_slot(self, x, y):
        quotient_x, remainder_x = divmod(
            x,
            self._edge_width + self.cell_image_size,
        )

        quotient_y, remainder_y = divmod(
            y,
            self._edge_width + self.cell_image_size,
        )
        if remainder_x <= self._edge_width or remainder_y <= self._edge_width:
            return

        return quotient_x, quotient_y

    def slot_to_pixel(self, slot):
        x, y = slot
        return self._get_cell_coordinate(x), self._get_cell_coordinate(y)

    def show(self):
        self._board_image.show()

    def draw(self):
        for y in range(self._board.height):
            for x in range(self._board.width):
                self._draw_cell(x, y)

    def _draw_cell(self, x, y):
        slot = (x, y)
        cell = self._board.data[slot]
        cell_image_to_use = (
            self._cell_image_uncovered
            if cell.is_uncovered
            else self._cell_image_covered
        )

        x_coord = self._get_cell_coordinate(x)
        y_coord = self._get_cell_coordinate(y)

        self._board_image.paste(cell_image_to_use, (x_coord, y_coord))
        self. _draw_overlay(x_coord, y_coord, cell)

    def _get_cell_coordinate(self, coord):
        return (
            ((self.cell_image_size + self._edge_width) * coord)
            + self._edge_width
        )

    def _draw_overlay(self, x, y, cell):
        if cell.is_uncovered:
            if cell.has_mine:
                return self._draw_mine(x, y, cell)
            elif cell.hint != 0:
                self._draw_hint(x, y, cell)
            else:
                return
        elif self.is_solved and cell.has_mine:
            self._draw_solved(x, y, cell)
        elif cell.is_flagged:
            return self._draw_flag(x, y, cell)
        else:
            return

    def _draw_flag(self, x, y, cell):
        self._overlay(x, y, cell, draw_method=CELL_DRAW_METHOD.flag)

    def _draw_hint(self, x, y, cell):
        self._overlay(x, y, cell, draw_method=CELL_DRAW_METHOD.hint)

    def _draw_mine(self, x, y, cell):
        self._overlay(x, y, cell, draw_method=CELL_DRAW_METHOD.mine)

    def _draw_solved(self, x, y, cell):
        self._overlay(x, y, cell, draw_method=CELL_DRAW_METHOD.solved)

    def _get_hint_font_color(self, hint):
        if hint == 1:
            return COLOR.dark_green
        elif hint == 2:
            return COLOR.blue
        else:
            return COLOR.dark_red

    def _overlay(self, x, y, cell, draw_method=CELL_DRAW_METHOD.hint):
        font = None
        cell_text = None
        height_adjustment = None
        fill = None
        draw_cross = False
        if draw_method == CELL_DRAW_METHOD.mine:
            cell_text = '\U00002620'  # unicode point for skull
            fill = COLOR.red
            font = ImageFont.truetype(
                conf.FONT_FILE_PATH,
                size=int(self.cell_image_size / 1.3)
            )
            height_adjustment = -4
        elif draw_method == CELL_DRAW_METHOD.hint:
            cell_text = str(cell.hint)
            fill = self._get_hint_font_color(hint=cell.hint)
            font = ImageFont.truetype(
                conf.FONT_FILE_PATH,
                size=int(self.cell_image_size / 2.5)
            )
            height_adjustment = 0
        elif draw_method == CELL_DRAW_METHOD.flag:
            # TODO: Write logic for flag here
            cell_text = '\U00002690'  # unicode point for flag
            fill = COLOR.green
            font = ImageFont.truetype(
                conf.FONT_FILE_PATH,
                size=int(self.cell_image_size / 1.3)
            )
            height_adjustment = -4
        elif draw_method == CELL_DRAW_METHOD.solved:
            cell_text = '\U00002620'  # unicode point for skull
            fill = COLOR.dark_gray
            font = ImageFont.truetype(
                conf.FONT_FILE_PATH,
                size=int(self.cell_image_size / 1.3)
            )
            height_adjustment = -4
            draw_cross = True
        else:
            error_msg = (
                f"Cannot handle unknown `draw_method={draw_method}`"
            )
            raise ValueError(error_msg)

        font_width, font_height = font.getsize(cell_text)
        draw_context = ImageDraw.Draw(self._board_image)
        draw_context.text(
            (
                (
                    x
                    + (self.cell_image_size / 2)
                    - (font_width / 2)
                ),
                (
                    y
                    + (self.cell_image_size / 2)
                    - (font_height / 2)
                    + height_adjustment
                ),
            ),
            cell_text,
            font=font,
            fill=fill,
            align="center",

        )

        if draw_cross:
            inset_ratio = 0.2
            incr_small = int(self.cell_image_size * inset_ratio)
            incr_large = int(self.cell_image_size * (1 - inset_ratio))

            p1 = (x + incr_small, y + incr_small)
            p2 = (x + incr_large, y + incr_large)
            draw_context.line(
                [p1, p2],
                fill=COLOR.very_dark_gray,
                width=self._edge_width,
                joint=None,
            )

            p3 = (x + incr_small, y + incr_large)
            p4 = (x + incr_large, y + incr_small)
            draw_context.line(
                [p3, p4],
                fill=COLOR.very_dark_gray,
                width=self._edge_width,
                joint=None,
            )

    def _draw_hints(self, cell, x, y, draw_mines=False):
        if not draw_mines and (cell.hint == 0 or cell.hint is None):
            return

        if draw_mines and cell.has_mine:
            cell_text = '\U00002620'  # unicode point for skull
            fill = COLOR.red
            font = ImageFont.truetype(
                conf.FONT_FILE_PATH,
                size=int(self.cell_image_size / 1.3)
            )
            height_adjustment = -4
        else:
            cell_text = str(cell.hint)
            fill = COLOR.blue
            font = ImageFont.truetype(
                conf.FONT_FILE_PATH,
                size=int(self.cell_image_size / 2.5)
            )
            height_adjustment = 0

        font_width, font_height = font.getsize(cell_text)
        draw_context = ImageDraw.Draw(self._board_image)
        draw_context.text(
            (
                (
                    x
                    + (self.cell_image_size / 2)
                    - (font_width / 2)
                ),
                (
                    y
                    + (self.cell_image_size / 2)
                    - (font_height / 2)
                    + height_adjustment
                ),
            ),
            cell_text,
            font=font,
            fill=fill,
            align="center",

        )

    def _create_cell_image(self, cell_state):
        color = None
        if cell_state == CELL_STYLE.covered:
            color = self.COVERED_COLOR
        elif cell_state == CELL_STYLE.uncovered:
            color = self.UNCOVERED_COLOR
        else:
            error_msg = (
                f'Unknown cell_state {cell_state} '
                'specified for cell image color!'
            )
            raise RuntimeError(error_msg)

        return Image.new(
            'RGBA',
            (self.cell_image_size, self.cell_image_size),
            color=color,
        )

    def _create_board_image(self):
        board_image_width = (
            (self.cell_image_size + self._edge_width) * self._board.width
            + self._edge_width
        )
        board_image_height = (
            (self.cell_image_size + self._edge_width) * self._board.height
            + self._edge_width
        )
        return Image.new(
            'RGBA',
            (board_image_width, board_image_height),
            color=COLOR.extra_dark_gray,
        )
