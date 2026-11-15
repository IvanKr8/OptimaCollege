import os
import logging
from console_ui import ConsoleCanvas
from document_tree import DocumentContainer
from app_states import AppState, DirectoryState, FileViewState


class FileManagerApp:
    """Context class maintaining the active state and coordinating user interaction."""
    def __init__(self, start_dir: str = None, canvas: ConsoleCanvas = None):
        self.current_dir = os.path.abspath(start_dir if start_dir else os.getcwd())
        self.canvas = canvas if canvas is not None else ConsoleCanvas()
        self.state: AppState = DirectoryState()
        self.running = True

    def set_state(self, new_state: AppState) -> None:
        self.state = new_state

    def stop(self) -> None:
        self.running = False

    def open_file(self, file_path: str) -> None:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            doc = DocumentContainer(os.path.basename(file_path))
            doc.load_lines(lines)
            logging.info(f"Відкрито файл {file_path}")
            self.set_state(FileViewState(file_path, doc))
        except (OSError, UnicodeDecodeError) as err:
            logging.error(f"Не вдалося відкрити файл {file_path}: {err}")
            if isinstance(self.state, DirectoryState):
                self.state.status_message = "Помилка читання файлу або непідтримуване кодування."

    def step(self, command: str) -> None:
        """Executes a single command cycle for deterministic testing and interactive runs."""
        self.state.handle_command(self, command)

    def run(self) -> None:
        logging.info("Запуск консольного файлового менеджера.")
        while self.running:
            self.state.render(self)
            try:
                user_input = input("Введіть команду > ")
                self.step(user_input)
            except (KeyboardInterrupt, EOFError):
                self.stop()


if __name__ == "__main__":
    app = FileManagerApp()
    app.run()
