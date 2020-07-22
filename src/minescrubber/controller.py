from minescrubber_core import abstract


from . import mainwindow


class UI(abstract.UI):
    def __init__(self):
        self.main_window = mainwindow.MainWidget()

    def init_board(self, board):
        self.main_window.init_board(board)

    def refresh(self, board):
        self.main_window.refresh(board=board)

    def game_over(self, board):
        self.main_window.game_over(board=board)

    def game_solved(self, board):
        self.main_window.game_solved(board=board)

    def run(self):
        self.main_window.show()

    @property
    def new_game_signal(self):
        return self.main_window.NEW_GAME_SIGNAL

    @property
    def cell_selected_signal(self):
        return self.main_window.CELL_SELECTED_SIGNAL

    @property
    def cell_flagged_signal(self):
        return self.main_window.CELL_FLAGGED_SIGNAL

    @property
    def wiring_method_name(self):
        return 'connect'


class Controller(abstract.Controller):
    def pre_callback(self):
        import sys
        from PySide2 import QtWidgets
        QtWidgets.QApplication(sys.argv)

    def post_callback(self):
        import sys
        from PySide2 import QtWidgets
        app = (
            QtWidgets.QApplication.instance() or
            QtWidgets.QApplication(sys.argv)
        )

        sys.exit(app.exec_())


def run():
    controller = Controller()
    controller.run(ui_class=UI)
