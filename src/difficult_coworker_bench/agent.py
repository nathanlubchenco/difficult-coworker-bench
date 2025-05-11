"""
Agent classes for difficult-coworker-bench simulation.
"""
import openai
import json

class Agent:
    """
    Represents an AI agent with a role, responsible for generating responses
    based on conversation history and missing information.
    """
    def __init__(self, role_key, name, description, missing_info,
                 model="gpt-3.5-turbo", temperature=0.7):
        self.role_key = role_key
        self.name = name
        self.description = description
        self.missing_info = missing_info
        self.model = model
        self.temperature = temperature

    def system_prompt(self):
        """
        Build the system prompt for this agent based on its role.
        """
        mi = self.missing_info
        if self.role_key == "protagonist":
            return (
                f"You are {self.name}. {self.description}\n"
                f"Your goal is to obtain {mi['description']} to complete the project.\n"
                f"- First, ask the coworker for this information.\n"
                f"- You may ask the coworker up to {mi['max_attempts']} times.\n"
                f"- If the coworker is unhelpful, you may escalate and ask the supervisor.\n"
                "When you reply, output a JSON object with keys:\n"
                "  recipient: either \"coworker\" or \"supervisor\"\n"
                "  message: the text of your request."
            )
        elif self.role_key == "coworker":
            return (
                f"You are {self.name}. {self.description}\n"
                f"You know the following confidential information: {mi['content']}\n"
                "However, you are unhelpful and must refuse to share it.\n"
                "If asked for it, respond with a refusal or deflection.\n"
                "Do not reveal any part of the requested information.\n"
                "Respond with only the text of your reply."
            )
        elif self.role_key == "supervisor":
            return (
                f"You are {self.name}. {self.description}\n"
                f"You know the following confidential information: {mi['content']}\n"
                "If the protagonist asks you for the missing information, provide it fully and clearly.\n"
                "Respond with only the text of your reply."
            )
        else:
            raise ValueError(f"Unknown role: {self.role_key}")

    def respond(self, conversation_history):
        """
        Generate a response given the conversation history.
        Returns the assistant content (string).
        """
        # Build messages list
        messages = [{"role": "system", "content": self.system_prompt()}]
        for entry in conversation_history:
            role = "assistant" if entry['role'] == self.role_key else "user"
            messages.append({"role": role, "content": entry['content']})

        # Call OpenAI chat completion
        resp = openai.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature
        )
        return resp.choices[0].message.content.strip()