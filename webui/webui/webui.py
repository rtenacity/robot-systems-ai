"""The main Chat app."""

import reflex as rx
import os

from webui import styles
from webui.components import chat, modal, navbar, sidebar
from webui.state import State
def clear_filepath():
    destination_dir = "/Users/rohanarni/Projects/robot-systems-ai/webui/assets/"

    files_in_directory = os.listdir(destination_dir)
    mp4_files = [file for file in files_in_directory if file.endswith(".mp4")]

    for mp4_file in mp4_files:
        file_path = os.path.join(destination_dir, mp4_file)
        os.remove(file_path)



@rx.page(title="SystemsAI")
def index() -> rx.Component:
    clear_filepath()
    """The main app."""
    return rx.vstack(
        navbar(),
        chat.chat(),
        chat.action_bar(),
        sidebar(),
        modal(),
        bg=styles.bg_medium_color,
        color=styles.text_light_color,
        min_h="100vh",
        align_items="stretch",
        spacing="0",
    )


# Add state and page to the app.
app = rx.App(style=styles.base_style)
app.add_page(index)
