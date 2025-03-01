"""Terminal UI for CLI LLM Chat"""

from prompt_toolkit import Application
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import ScrollablePane
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.styles import Style

class TerminalUI:
    def __init__(self):
        self.kb = KeyBindings()
        self.output_area = TextArea(
            text="Welcome to CLI LLM Chat!\nType your messages below. Type /exit to end the session.\n",
            read_only=True,
            scrollbar=True,
            wrap_lines=True
        )
        self.input_area = TextArea(
            height=1,
            prompt='> ',
            multiline=False,
            style='class:input'
        )
        
        # Create the layout
        self.root_container = HSplit([
            ScrollablePane(self.output_area),
            self.input_area,
        ])
        
        self.layout = Layout(self.root_container)
        
        # Create application
        self.app = Application(
            layout=self.layout,
            full_screen=True,
            mouse_support=True,
            key_bindings=self.kb,
            style=Style.from_dict({
                'input': 'ansiyellow',
            })
        )
        
        # Handle enter key
        @self.kb.add('enter')
        def _(event):
            user_input = self.input_area.text.strip()
            self.input_area.text = ''
            
            if user_input.lower() == '/exit':
                event.app.exit()
                return
                
            # Add user input to output area
            self.append_message("You", user_input)
            
            # Let the caller handle the input
            if self.on_input:
                self.on_input(user_input)
        
        # Handle Ctrl+C and Ctrl+D
        @self.kb.add('c-c')
        @self.kb.add('c-d')
        def _(event):
            event.app.exit()
    
    def append_message(self, sender, message):
        """Add a message to the output area"""
        if sender == "You":
            self.output_area.text += f"\n[You]:\n{message}\n"
        else:
            self.output_area.text += f"\n[Assistant]:\n{message}\n"
        
        # Scroll to bottom
        self.output_area.buffer.cursor_position = len(self.output_area.text)
    
    def run(self, on_input=None):
        """Run the terminal UI"""
        self.on_input = on_input
        self.app.run()
