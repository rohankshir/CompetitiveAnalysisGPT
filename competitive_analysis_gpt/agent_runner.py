from pydantic import BaseModel, Field
from typing import List, Optional, Dict
import json
import colorama
from colorama import Fore
from competitive_analysis_gpt.llm_util import chat_completion_request, GPT4, GPT35


def convert_pydantic_to_openai_schema(pydantic_model):
    # deep copy the schema
    schema = json.loads(pydantic_model.schema_json())
    # drop 'title' key and replace with 'name'
    result = {
        "name": schema.pop("title"),
        "description": schema.pop("description"),
        "parameters": schema,
    }
    return result


class AgentRunner:
    def __init__(self, functions=None, model=GPT35, complete_function="ResearchComplete"):
        self.conversation_history = []
        self.functions = (
            [convert_pydantic_to_openai_schema(f) for f in functions]
            if functions is not None
            else None
        )
        self.function_map = (
            {f["name"]: functions[i] for i, f in enumerate(self.functions)}
            if functions is not None
            else None
        )
        self.complete = False
        self.num_function_calls = 0
        self.model = model
        self.final_response = None
        self.complete_function = complete_function

    def add_message(self, role, content, name=None, function_call=None):
        message = {"role": role, "content": content}
        if name is not None:
            message.update({"name": name})
        if function_call is not None:
            message.update({"function_call": function_call})
        self.conversation_history.append(message)

    def display_conversation(self, since_index=0):
        role_to_color = {
            "system": Fore.CYAN,
            "user": Fore.GREEN,
            "assistant": Fore.WHITE,
            "function": Fore.MAGENTA,
        }

        for index, message in enumerate(self.conversation_history):
            if index < since_index:
                continue
            role = message["role"]
            # if role == "function":
            #     continue
            content = message.get("content") or message.get("function_call", "")
            content_display_len = 400
            if len(content) > content_display_len:
                content = content[:content_display_len] + "..."
            if role == "function":
                content = f"Function {message['name']}:\n{content}"
            else:
                content = f"{role}:\n{content}"
            color = role_to_color.get(role, Fore.BLACK)
            # Use colorama's init function to enable colored output on Windows
            colorama.init()
            print(color + content + Fore.RESET)
            print("\n")

    def chat_completion_with_function_execution(self, force_complete=False):
        """This function makes a ChatCompletion API call with the option of adding functions
        It updates the conversation history with the response from the API call as well
        if it is a function call, it executes the function, appends the function call and response to the history and returns the function call with response
        else it appends the response to the history and returns the response
        """
        response = chat_completion_request(
            self.conversation_history, self.functions, model=self.model
        )
        # Check for InvalidRequestError
        if isinstance(response, dict) and "error" in response:
            print(response["error"])
            return
        full_message = response["choices"][0]
        if force_complete:
            response = chat_completion_request(
                self.conversation_history,
                self.functions,
                model=self.model,
                function_call=self.complete_function,
            )
            full_message = response["choices"][0]
            function = full_message["message"]["function_call"]
            full_message = response["choices"][0]
            self.complete = True
            try:
                function_instance = self.function_map[function.name].parse_raw(function.arguments)
                function_response = function_instance.execute()
            except Exception as e:
                function_response = function.arguments
                print(e)
                print(function.name)
                print(function.arguments)
            self.final_response = function_response
            self.add_message("assistant", None, function_call=function)
            self.add_message("function", function_response, name=function.name)
            return function, function_response
        if full_message["finish_reason"] == "function_call":
            function = full_message["message"]["function_call"]
            assert function.name in [f["name"] for f in self.functions]
            try:
                function_instance = self.function_map[function.name].parse_raw(function.arguments)
                function_response = function_instance.execute()
            except Exception as e:
                print(e)
                function_response = function.arguments
                print(function.arguments)
            self.add_message("assistant", None, function_call=function)
            self.add_message("function", function_response, name=function.name)
            if function.name == self.complete_function:
                self.complete = True
                self.final_response = function_response
                return function, function_response
            self.num_function_calls += 1
            return function, function_response
        else:
            full_message = full_message["message"]
            self.add_message(full_message["role"], full_message["content"])
            return full_message
