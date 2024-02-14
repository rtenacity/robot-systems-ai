import os
import reflex as rx
from dotenv import load_dotenv
from langchain.prompts.chat import ChatPromptTemplate
from langchain.schema import BaseOutputParser
from langchain_openai import ChatOpenAI
from webui import styles
from webui.components import loading_icon
import shutil
import time
from webui.grid_scene import *
from webui.template import Template

temp = Template()

load_dotenv()

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

human_template = "Prompt: The blue robot cannot go to the right side of the barrier. The red robot cannot go to the left side of the barrier. An object has been loaded at load zone D, and it needs to move to load zone A. Prompt: {text}"

template = temp.return_template()
model = ChatOpenAI(model = 'gpt-3.5-turbo', openai_api_key = api_key)

class QA(rx.Base):
    """A question and answer pair."""

    question: str
    answer: str
    
class ImageURL():
    
    def __init__(self):
        self.file_version = 0
        self.filename = "AIScene_0.mp4"
        self.fileaddr = "/" + self.filename
    
    def update_file(self):
        self.file_version += 1
        self.filename = f"AIScene_{self.file_version}.mp4"
        self.fileaddr = "/" + self.filename
    
        
img = ImageURL()

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
    
    url_index:int = 0
    
    url_list:list = []
    
    url:str = ""

    def create_chat(self):
        """Create a new chat."""
        # Add the new chat to the list of chats.
        self.current_chat = self.new_chat_name
        self.chats[self.new_chat_name] = []

        # Toggle the modal.
        self.modal_open = False
    
    def update_url(self, new_url:str):
        self.url_list.append(new_url)
        self.url_index+=1
        self.url = new_url

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
        img.update_file()
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
        
        
        reason = parsed[0]
        code = parsed[1]
        
        exec_code = code.replace("python", "")

        exec_code = "config.output_dir = 'assets'\n" +  exec_code + "\nAIScene2 = AIScene() \nAIScene2.render()"
        exec(exec_code)
    
        
        source_path = "/Users/rohanarni/Projects/robot-systems-ai/webui/media/videos/1920p60/AIScene.mp4"

        destination_dir = "/Users/rohanarni/Projects/robot-systems-ai/webui/assets/"

        destination_path = os.path.join(destination_dir, img.filename)

        shutil.move(source_path, destination_path)
            
        answer_text = add_br_tags(reason)
        
        self.chats[self.current_chat][-1].answer += answer_text
        self.chats = self.chats
        
        answer_text = rf"""
```python3
{code}
```
"""     

        
        self.chats[self.current_chat][-1].answer += answer_text
        self.chats = self.chats
        
        time.sleep(5)
        self.processing = False
        
        self.update_url(img.fileaddr)



