from typing import Union
import json
from loguru import logger

from reverie.common.llm import get_chat_model
from reverie.common.utils import parse_json_response, parse_yaml_response
from reverie.config.config import Config


class PromptManager:
    def __init__(self, prompt_folder_path: str):
        self.prompt_folder_path = prompt_folder_path.rstrip('/')
        self.llm_model_name = Config.llm_model_name
        self.temperature = Config.temperature
        self.max_retries = Config.max_retries

        logger.debug(f"Using llm: {self.llm_model_name}")

    def chat_with_llm(self, prompt: str) -> str:
        llm = get_chat_model(self.llm_model_name, self.temperature)
        res = llm.invoke(prompt)
        return res.content

    async def async_chat_with_llm(self, prompt: str) -> str:
        llm = get_chat_model(self.llm_model_name, self.temperature)
        res = await llm.ainvoke(prompt)
        return res.content

    def create_prompt(self, prompt_file_name: str, prompt_inputs: Union[list[str], str]) -> str:
        prompt_file_name = prompt_file_name.removesuffix('.txt')
        prompt_file_path = f"{self.prompt_folder_path}/{prompt_file_name}.txt"

        # Convert inputs to a list format
        if isinstance(prompt_inputs, str):
            prompt_inputs = [prompt_inputs]

        # Convert all elements in the list to string format
        prompt_inputs = [str(input) for input in prompt_inputs]

        with open(prompt_file_path) as f:
            prompt = f.read()

        # Replace variables in the prompt
        for i, input in enumerate(prompt_inputs):
            prompt = prompt.replace(f"!<INPUT {i}>!", input)

        if "<commentblockmarker>###</commentblockmarker>" in prompt:
            prompt = prompt.split("<commentblockmarker>###</commentblockmarker>")[-1]

        # Truncate from the front based on the maximum context window size, i.e., keep the latter part
        tokens = prompt.split(' ')
        if len(tokens) > Config.max_context_length:
            tokens = tokens[-Config.max_context_length:]
        prompt = ' '.join(tokens)

        return prompt

    def chat_and_parse(self,
                       prompt_file_name: str,
                       prompt_inputs: Union[list[str], str],
                       json_response: bool = False,
                       required_keys: Union[list[str], None] = None,
                       yaml_response: bool = False) -> Union[list, dict, str, None]:
        prompt = self.create_prompt(prompt_file_name, prompt_inputs)

        # logger.debug(f"[{prompt_file_name}] prompt: {prompt}")

        for i in range(self.max_retries):
            response = self.chat_with_llm(prompt)
            # logger.debug(f"[{prompt_file_name}] response: {response}")

            # Response might be None
            if not response:
                continue

            if json_response:
                try:
                    response = parse_json_response(response)
                    if not response:
                        continue
                    # Check for required JSON keys
                    if required_keys:
                        missing_keys = [key for key in required_keys if key not in response]
                        if missing_keys:
                            logger.error(f"Missing keys in response: {missing_keys}")
                            continue
                except json.JSONDecodeError as e:
                    logger.error(e)
                    logger.error(response)
                    continue

            if yaml_response:
                try:
                    response = parse_yaml_response(response)
                except Exception as e:
                    logger.error(e)
                    logger.error(response)
                    continue

            return response

        return None

    async def async_chat_and_parse(self,
                                   prompt_file_name: str,
                                   prompt_inputs: Union[list[str], str],
                                   json_response: bool = False,
                                   required_keys: Union[list[str], None] = None,
                                   yaml_response: bool = False) -> Union[list, dict, str, None]:
        prompt = self.create_prompt(prompt_file_name, prompt_inputs)

        # logger.debug(f"[{prompt_file_name}] prompt: {prompt}")

        for i in range(self.max_retries):
            response = await self.async_chat_with_llm(prompt)
            # logger.debug(f"[{prompt_file_name}] response: {response}")

            # Response might be None
            if not response:
                continue

            if json_response:
                try:
                    response = parse_json_response(response)
                    if not response:
                        continue
                    # Check for required JSON keys
                    if required_keys:
                        missing_keys = [key for key in required_keys if key not in response]
                        if missing_keys:
                            logger.error(f"Missing keys in response: {missing_keys}")
                            continue
                except json.JSONDecodeError as e:
                    logger.error(e)
                    continue

            if yaml_response:
                try:
                    response = parse_yaml_response(response)
                except Exception as e:
                    logger.error(e)
                    continue

            return response

        return None


prompt_manager = PromptManager(Config.prompt_folder)
