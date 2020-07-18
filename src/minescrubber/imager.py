import collections


from PIL import Image, ImageFont, ImageDraw, ImageQt


from . import conf


def _declare_constants(obj_name, **name_value_dict):
    "A named tuple generator used for declaring contants"
    ConstantContainer = collections.namedtuple(
        obj_name,
        name_value_dict.keys(),
    )
    return ConstantContainer(*name_value_dict.values())


CELL_STYLE = _declare_constants(
    obj_name='CELL_STYLE',
    covered='covered',
    uncovered='uncovered',
)


class BoardImage:
    COVERED_COLOR = (145, 156, 255)
    UNCOVERED_COLOR = (200, 200, 200)
    EDGE_COLOR = (27, 27, 27)
    FONT_COLOR = (0, 0, 255)
    MINE_FONT_COLOR = (255, 0, 0)
    EDGE_WIDTH_CONTROL = 12  # Lesser produces thicker edges (12 is ideal)

    def __init__(self, board):
        self.init_image(board=board)

    @property
    def qt_image(self):
        return ImageQt.ImageQt(self._board_image)

    def draw(self):
        for y in range(self._board.height):
            for x in range(self._board.width):
                slot = (x, y)
                cell = self._board.data[slot]

                if self._board.mines:
                    cell_image_to_use = self._cell_image_uncovered
                else:
                    cell_image_to_use = (
                        self._cell_image_covered
                        if cell.is_covered
                        else self._cell_image_uncovered
                    )

                x_coord = (
                    ((self.cell_image_size + self._edge_width) * x)
                    + self._edge_width
                )

                y_coord = (
                    ((self.cell_image_size + self._edge_width) * y)
                    + self._edge_width
                )

                self._board_image.paste(
                    cell_image_to_use,
                    (x_coord, y_coord),
                )

                # Game Over
                if self._board.mines:
                    self._draw_hints(
                        cell=cell,
                        x=x_coord,
                        y=y_coord,
                        draw_mines=True,
                    )
                elif cell.hint is None or cell.hint == 0 or cell.is_covered:
                    continue
                else:
                    self._draw_hints(cell=cell, x=x_coord, y=y_coord)

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

    def _draw_hints(self, cell, x, y, draw_mines=False):
        if cell.hint == 0:
            return

        if draw_mines and cell.has_mine:
            cell_text = '\U00002620'  # unicode point for skull
            fill = self.MINE_FONT_COLOR
            font = ImageFont.truetype(
                conf.FONT_FILE_PATH,
                size=int(self.cell_image_size / 1.3)
            )
            height_adjustment = -4
        else:
            cell_text = str(cell.hint)
            fill = self.FONT_COLOR
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

    def show(self):
        self._board_image.show()

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
            color=self.EDGE_COLOR,
        )

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


def test_board_image():
    import random
    cell_size = 120
    edge_width = int(cell_size / 12)
    width = 4
    height = 4
    font_size = int(cell_size / 2)
    uncovered_color = (145, 156, 255)
    covered_color = (255, 145, 156)
    board_color = (54, 54, 54)

    font_file_path = (
        '/Users/alok/dev/github/minescrubber/src/minescrubber/resources'
        '/mono.ttf'
    )
    font = ImageFont.truetype(font_file_path, size=font_size)

    cell_image_covered = Image.new(
        'RGBA',
        (cell_size, cell_size),
        color=covered_color,
    )

    cell_image_uncovered = Image.new(
        'RGBA',
        (cell_size, cell_size),
        color=uncovered_color,
    )

    board_image_width = (
        ((cell_size + edge_width) * width) + edge_width
    )
    board_image_height = (
        ((cell_size + edge_width) * height) + edge_width
    )

    board_image = Image.new(
        'RGBA',
        (board_image_width, board_image_height),
        color=board_color,
    )

    for y in range(height):
        for x in range(width):
            cell_image_to_use = (
                cell_image_covered
                if (x + y) % 2 == 0
                else cell_image_uncovered
            )

            x_coord = ((cell_size + edge_width) * x) + edge_width
            y_coord = ((cell_size + edge_width) * y) + edge_width

            board_image.paste(
                cell_image_to_use,
                (x_coord, y_coord),
            )

            cell_text = str(random.randint(1, 8))
            font_width, font_height = font.getsize(cell_text)
            draw_context = ImageDraw.Draw(board_image)
            draw_context.text(
                (
                    x_coord + (cell_size / 2) - (font_width / 2),
                    y_coord + (cell_size / 2) - (font_height / 2),
                ),
                cell_text,
                font=font,
                fill=(0, 0, 255),
                align="center",

            )

    board_image.show()
