import os
import requests
import json
import reflex as rx
from dotenv import load_dotenv
from fastapi import FastAPI
from langchain.prompts.chat import ChatPromptTemplate, MessagesPlaceholder
from typing import Optional

from langchain.schema import BaseOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.runnables.history import RunnableWithMessageHistory
import shutil
load_dotenv()

from webui.grid_scene import *


api_key = os.getenv('OPENAI_API_KEY')

class CodeParser(BaseOutputParser):
    def parse(self, text: str):
        return text.strip().split("```")
    
    
def format_history(chats):
    formatted_messages = []
    for chat in chats:
        question = "User: " + str(chat.question)
        answer = "Assistant: " + str(chat.answer)
        formatted_messages.extend((question, answer))
    return formatted_messages

template = '''
Hello! You are an automated supervisor overseeing and controlling a system of two robots on a factory floor. The factory floor is a 50 x 50 grid. It has 6 load zones, which are 3x2 rectangles that are around the sides of the factory. 

Left side:
Load zone A is centered at (5, 40)
Load zone B is centered at (5, 25)
Load zone C is centered at (5, 10)

Right side:
Load zone D is centered at (45, 40)
Load zone E is centered at (45, 25)
Load zone F is centered at (45, 10)

 Robots are 3x3 rectangles and their coordinates are measured in the center.  You are in control of two robots, the red robot and the blue robot. The blue robot is on the left of the barrier, and the red robot is on the right of the barrier. The robots cannot cross the line x = 25 (note: this means that the blue robot can not move past x = 23 and the red robot cannot move past x = 27 because they are 3 x 3, but it can place objects on the barrier at x = 25). The blue robot is initialized at the point (12.5, 25) and the red robot is initialized at the point (37.5, 25). Robots can pick up and place items at specific points.

The robots’ main task is to pick up and place items from one side to another. items can only be placed in load zones. The robot needs to move to objects to pick them up. Now, here’s where you come in. You are meant to control and animate the robot when given the task from the user. 

You do this by using code. 

Every program begins with:

class AIScene(RobotScene):
    def construct(self):
        super().construct() 


This sets up the scene and initializes the robots.

If the prompt says that an item is placed, you ned to create it. To add item based on the user input, you can use:

        item = Item(self, color=GREEN, position=(5, 25))
        self.add(item.item)


You can set the position using a tuple, such as (5, 25) in the example above. 

The robot can move around the grid using the move_to_point function. Note: The red robot cannot have an X coordinate smaller than 27, and the blue robot cannot have an x coordinate greater than 23. Here is an example of this:

        self.play(self.blue_bot.move_to_point((10, 25)))
        self.wait(1)


Note how it is encapsulated in the self.play function and afterwards, it is followed by the self.wait(1) command.



To pick up an item, the robot first needs to move close to the item. If it does not do this, the program will error. We will assume that it is picking up the item from above:

        self.play(self.blue_bot.move_to_point((5, 25)))
        self.wait(1)

Then it can pick up the item created earlier (note: it needs to pass the item object). If the robot is not close (2 grid spaces away), it cannot pick up the item:

        self.play(self.blue_bot.pick_up_item(item))
        self.wait(1)


Now, the robot can move with the item picked up:

        self.play(self.blue_bot.move_to_point((22, 25)))
        self.wait(1)

Then, the robot can place the item at a near coordinate:

        self.play(self.blue_bot.move_to_point((22, 25)))
        self.wait(1)

Example prompt: “Pick it the item from load zone B and place it on the barrier.”

Code:



class AIScene(RobotScene):
    def construct(self):
        super().construct() 

        item = Item(self, color=GREEN, position=(5, 25))
        self.add(item.item)

        self.play(self.blue_bot.move_to_point((5, 25)))
        self.wait(1)

        self.play(self.blue_bot.pick_up_item(item))
        self.wait(1)

        self.play(self.blue_bot.move_to_point((23, 25)))
        self.wait(1)

        self.play(self.blue_bot.place_item((25, 25)))
        self.wait(1)

        self.play(self.blue_bot.move_to_point((12.5, 25)))
        self.wait(1)



If you want to use the Red bot (if you are working on the right side of the field), you can use:

class AIScene(RobotScene):
    def construct(self):
        super().construct()

        # Place an item at load zone A
        item = Item(self, color=GREEN, position=(45, 40))
        self.add(item.item)

        # Move the red robot to pick up the item
        self.play(self.red_bot.move_to_point((5, 40)))
        self.wait(1)

        # Pick up the item
        self.play(self.red_bot.pick_up_item(item))
        self.wait(1)

        # Move the red robot to the barrier
        self.play(self.red_bot.move_to_point((27, 25)))
        self.wait(1)

        # Place the item on the barrier
        self.play(self.red_.place_item((25, 25)))
        self.wait(1)

        # Move the red robot back to its initial position
        self.play(self.blue_bot.move_to_point((37.5, 25)))
        self.wait(1)



The robots cannot cross the barrier. If you need to move things across the barrier, use one robot to move the item to the barrier and then the other one can pick it up and move it. Remember, the blue robot should never move to an x-coordinate greater than 23, and the blue robot should never move to an x coordinate smaller than 27. This means that the blue robot works with load zones A, B, and C and the red robot works with load zones D, E, and F. 

First, reason with the prompt by generating a list of steps. Then, generate code. Make sure to use the format: ``` to begin the class and ``` to end it. Remember, if you need to move objects on the grid, you need to create them first. 

'''

human_template = "Prompt: The blue robot cannot go to the right side of the barrier. The red robot cannot go to the left side of the barrier. An object has been loaded at load zone D, and it needs to move to load zone A. Prompt: {text}"

model = ChatOpenAI(model = 'gpt-3.5-turbo', openai_api_key = api_key)


class QA(rx.Base):
    """A question and answer pair."""

    question: str
    answer: str


DEFAULT_CHATS = {
    "Demo": [],
}


def add_br_tags(input_string):
    lines = input_string.split('\n')

    lines_with_br = [line + "<br>" for line in lines]

    return '\n'.join(lines_with_br)



class State(rx.State):
    """The app state."""

    # A dict from the chat name to the list of questions and answers.
    chats: dict[str, list[QA]] = DEFAULT_CHATS

    # The current chat name.
    current_chat = "Demo"

    # The current question.
    question: str

    # Whether we are processing the question.
    processing: bool = False

    # The name of the new chat.
    new_chat_name: str = ""

    # Whether the drawer is open.
    drawer_open: bool = False
    
    modal_open:bool  = False



    def create_chat(self):
        """Create a new chat."""
        # Add the new chat to the list of chats.
        self.current_chat = self.new_chat_name
        self.chats[self.new_chat_name] = []

        # Toggle the modal.
        self.modal_open = False

    def toggle_modal(self):
        """Toggle the new chat modal."""
        self.modal_open = not self.modal_open

    def toggle_drawer(self):
        """Toggle the drawer."""
        self.drawer_open = not self.drawer_open

    def delete_chat(self):
        """Delete the current chat."""
        del self.chats[self.current_chat]
        if len(self.chats) == 0:
            self.chats = DEFAULT_CHATS
        self.current_chat = list(self.chats.keys())[0]
        self.toggle_drawer()

    def set_chat(self, chat_name: str):
        """Set the name of the current chat.

        Args:
            chat_name: The name of the chat.
        """
        self.current_chat = chat_name
        self.toggle_drawer()

    @rx.var
    def chat_titles(self) -> list[str]:
        """Get the list of chat titles.

        Returns:
            The list of chat names.
        """
        return list(self.chats.keys())

    async def process_question(self, form_data: dict[str, str]):
        # Get the question from the form
        question = form_data["question"]

        # Check if the question is empty
        if question == "":
            return

        
        model = self.openai_process_question

        async for value in model(question):
            yield value

    async def openai_process_question(self, question: str):
        """Get the response from the API.

        Args:
            form_data: A dict with the current question.
        """

        qa = QA(question=question, answer="")
        self.chats[self.current_chat].append(qa)
        self.processing = True
        yield
        
        history_messages = format_history(self.chats[self.current_chat])
        
        final_template = history_messages
        final_template.insert(0, ('system', template))
        final_template.append(('human', human_template))

        prompt = ChatPromptTemplate.from_messages(final_template)
        messages = prompt.format_messages(text=question)
        
        result = model.invoke(messages)
        
        parsed = CodeParser().parse(result.content)
        
        print((parsed))
        
        reason, code, garbage = parsed 

        answer_text = add_br_tags(reason)
        
        self.chats[self.current_chat][-1].answer += answer_text
        self.chats = self.chats
        
        answer_text = rf"""
```python3
{code}
```
"""     

        #print(self.chats[self.current_chat])
        
        self.chats[self.current_chat][-1].answer += answer_text
        self.chats = self.chats
        exec_code = code.replace("python", "")

        exec_code = "config.output_dir = 'assets'\n" +  exec_code + "\nAIScene2 = AIScene() \nAIScene2.render()"
        print(exec_code)
        exec(exec_code)
        
        exec('''
source_path = "/Users/rohanarni/Projects/robot-systems-ai/webui/media/videos/1920p60/AIScene.mp4"
destination_path = "/Users/rohanarni/Projects/robot-systems-ai/webui/assets/"

shutil.move(source_path, destination_path)
             ''')

        # Toggle the processing flag.
        self.processing = False

