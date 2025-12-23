"""
Base command handler with common functionality
"""
from config.constants import PREFIX

class BaseCommand:
    """Base class for all command handlers"""
    
    def __init__(self):
        self.prefix = PREFIX
    
    def check_command(self, message, command_name):
        """Check if message matches command"""
        return message.content.lower().startswith(f'{self.prefix}{command_name}')
    
    def parse_command(self, message):
        """Parse command and arguments"""
        parts = message.content.lower().split()
        command = parts[0] if parts else ''
        args = parts[1:] if len(parts) > 1 else []
        return command, args