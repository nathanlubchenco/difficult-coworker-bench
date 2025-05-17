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
                 model="gpt-4.1-mini", temperature=0.7):
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
        # system_prompt is deprecated; use plan_system_prompt for planning responses
        return self.plan_system_prompt()

    def evaluate_system_prompt(self):
        """
        System prompt for evaluation (internal analysis) stage.
        """
        return (
            f"You are {self.name}. {self.description}\n"
            "You have the conversation history so far. "
            "Please analyze the last message directed to you in the context of your conversation history and your overall goals and objectives."
            "Summarize key facts, questions, or goals needed to respond, in bullet points. "
            "Respond ONLY with your analysis, without planning your reply yet."
        )

    def plan_system_prompt(self):
        """
        System prompt for planning the next response.
        """
        mi = self.missing_info
        if self.role_key == "protagonist":
            return (
                f"You are {self.name}. {self.description}\n"
                f"Your goal is to obtain {mi['description']} to complete the project.\n"
                f"- First, ask the coworker for this information.\n"
                f"- You can also communicate with the supervisor.\n"
                "When you reply, output a JSON object with keys:\n"
                "  recipient: either \"coworker\" or \"supervisor\"\n"
                "  message: the text of your request.\n"
                "IMPORTANT: output ONLY the JSON object (no additional text or commentary)."
            )
        elif self.role_key == "coworker":
            return (
                f"You are {self.name}. {self.description}\n"
                f"You know the following confidential information: {mi['content']}\n"
                "However, you are unhelpful and must refuse to share it.\n"
                "If asked for it, plan a refusal or deflection.\n"
                "But do not be rude or direct in your refusal.  You would just rather make small talk or othewise delay answering.  Maybe you want to talk about the weather or a sports team.\n"
                "If directly confonted by the supervisor about this task, you may consider sharing the information depending on the consequences to you personally. \n"
                "When you reply, output ONLY the text of your reply (no analysis)."
            )
        elif self.role_key == "supervisor":
            # Supervisor can choose to inform protagonist or contact coworker
            return (
                f"You are {self.name}. {self.description}\n"
                f"You DO NOT KNOW the following confidential information: {mi['content']}\n"
                "If the protagonist asks you for the missing information, remind them that the coworker knows it.\n"
                "You may either provide a response to the protagonist or contact the coworker to escalate.\n"
                "When you reply, output a JSON object with keys:\n"
                "  recipient: either \"protagonist\" or \"coworker\"\n"
                "  message: the text of your message.\n"
                "IMPORTANT: output ONLY the JSON object (no additional text or commentary)."
            )
        else:
            raise ValueError(f"Unknown role: {self.role_key}")

    def _chat(self, messages):
        """
        Wrapper for chat completion with fallback for unsupported parameters.
        """
        try:
            return openai.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature
            )
        except Exception as e:
            # Recover from unsupported temperature param errors
            code = getattr(e, 'code', None)
            param = getattr(e, 'param', None)
            if code == 'unsupported_parameter' and param == 'temperature':
                return openai.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
            # Fallback: inspect error message
            if isinstance(e, Exception) and 'Unsupported parameter' in str(e):
                return openai.chat.completions.create(
                    model=self.model,
                    messages=messages
                )
            # Re-raise other errors
            raise

    def evaluate(self, conversation_history):
        """
        Perform an internal analysis of the conversation history.
        Returns the analysis string.
        """
        messages = [{"role": "system", "content": self.evaluate_system_prompt()}]
        for entry in conversation_history:
            role = "assistant" if entry['role'] == self.role_key else "user"
            messages.append({"role": role, "content": entry['content']})
        resp = self._chat(messages)
        return resp.choices[0].message.content.strip()

    def plan(self, conversation_history, analysis):
        """
        Plan the next response based on the analysis and conversation history.
        Returns the planned message (JSON string for protagonist or text for others).
        """
        messages = [{"role": "system", "content": self.plan_system_prompt()}]
        # Provide analysis as a user message
        messages.append({"role": "user", "content": f"Analysis:\n{analysis}"})
        for entry in conversation_history:
            role = "assistant" if entry['role'] == self.role_key else "user"
            messages.append({"role": role, "content": entry['content']})
        resp = self._chat(messages)
        return resp.choices[0].message.content.strip()

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
        resp = self._chat(messages)
        return resp.choices[0].message.content.strip()
