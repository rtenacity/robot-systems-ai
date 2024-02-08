"""The main Chat app."""

import reflex as rx
import os

from webui import styles
from webui.components import chat, modal, navbar, sidebar
from webui.state import State

def clear_filepath():
    destination_dir = "/Users/rohanarni/Projects/robot-systems-ai/webui/assets/"

    # List all the files in the directory
    files_in_directory = os.listdir(destination_dir)

    # Filter out the files that end with .mp4
    mp4_files = [file for file in files_in_directory if file.endswith(".mp4")]

    # Loop through the list of .mp4 files and delete each one
    for mp4_file in mp4_files:
        file_path = os.path.join(destination_dir, mp4_file)  # Get the full path of the file
        os.remove(file_path)

@rx.page(title="RobotAI")
def index() -> rx.Component:
    clear_filepath()
    """The main app."""
    return rx.vstack(
        navbar(),
        chat.chat(),
        chat.action_bar(),
        sidebar(),
        modal(),
        bg=styles.bg_dark_color,
        color=styles.text_light_color,
        min_h="100vh",
        align_items="stretch",
        spacing="0",
    )


# Add state and page to the app.
app = rx.App(style=styles.base_style)
app.add_page(index)
