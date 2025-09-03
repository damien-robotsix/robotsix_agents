"""
Tools for the Task Organizer agent.

This module provides a TodoManager class that encapsulates all file operations 
for the TODO-AI.md file.
"""

import os

class TodoManager:
    """Manages the TODO list file."""

    def __init__(self, working_directory: str = None):
        """Initializes the TodoManager with the correct file path."""
        if working_directory is None:
            working_directory = "."
        self.todo_file = os.path.join(working_directory, "TODO-AI.md")

    def add_todo(self, task: str) -> str:
        """Adds a new task to the TODO list."""
        try:
            # Create the directory if it doesn't exist
            os.makedirs(os.path.dirname(self.todo_file), exist_ok=True)
            # Append the task to the file
            with open(self.todo_file, 'a') as f:
                if f.tell() == 0:
                    f.write("# AI-Managed TODO List\n\n")
                f.write(f"- [ ] {task}\n")
            return f"Successfully added task: '{task}'"
        except Exception as e:
            return f"Error adding task: {e}"

    def list_todos(self) -> str:
        """Lists all tasks in the TODO list."""
        try:
            with open(self.todo_file, 'r') as f:
                content = f.read()
                if not content.strip():
                    return "TODO list is empty."
                return content
        except FileNotFoundError:
            return "TODO list not found. It will be created when you add the first task."
        except Exception as e:
            return f"Error reading TODO list: {e}"

    def mark_task_done(self, task_number: int) -> str:
        """Marks a task as done by its number (1-based)."""
        try:
            with open(self.todo_file, 'r') as f:
                lines = f.readlines()

            todo_items_indices = [i for i, line in enumerate(lines) if line.strip().startswith('- [')]

            if not 1 <= task_number <= len(todo_items_indices):
                return f"Error: Invalid task number {task_number}. Please provide a number between 1 and {len(todo_items_indices)}."

            line_to_modify_index = todo_items_indices[task_number - 1]
            line_to_modify = lines[line_to_modify_index]

            if line_to_modify.strip().startswith('- [x]'):
                return f"Task {task_number} is already marked as done."
            
            lines[line_to_modify_index] = line_to_modify.replace('- [ ]', '- [x]', 1)

            with open(self.todo_file, 'w') as f:
                f.writelines(lines)

            return f"Successfully marked task {task_number} as done."
        except FileNotFoundError:
            return "TODO list not found."
        except Exception as e:
            return f"Error marking task as done: {e}"

    def delete_todo_file(self) -> str:
        """Deletes the TODO list file."""
        try:
            if os.path.exists(self.todo_file):
                os.remove(self.todo_file)
                return "TODO list file deleted successfully."
            else:
                return "TODO list file not found, nothing to delete."
        except Exception as e:
            return f"Error deleting TODO list file: {e}"
