import re
import json
from datetime import datetime

from loguru import logger


def parse_json_response(text: str):
    """
    Extract the json code block from plain text and return the result read by json.loads()

    :param text: Plain text
    :return: The result read by json.loads()
    """

    # If there is only a beginning but no end, add the end here as a special case
    if "```json" in text and "}\n```" not in text:
        text += '"\n}\n```'

    json_pattern_1 = r'```json(.*?)```'
    json_pattern_2 = r'```(.*?)```'

    match = re.search(json_pattern_1, text, re.DOTALL)
    match = match if match else re.search(json_pattern_2, text, re.DOTALL)

    if match:
        json_str = match.group(1).strip()
    else:
        json_str = text.strip()

    try:
        data = json.loads(json_str)
        return data

    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error: {e}")
        logger.error(json_str)
        return None


def parse_yaml_response(text: str):
    """
    Extract the yaml code block from plain text and return it in string format
    
    :param text: Plain text
    :return: String format
    """

    yaml_pattern_1 = r'```yaml(.*?)```'
    yaml_pattern_2 = r'```(.*?)```'

    match = re.search(yaml_pattern_1, text, re.DOTALL)
    match = match if match else re.search(yaml_pattern_2, text, re.DOTALL)

    if match:
        yaml_str = match.group(1).strip()
    else:
        yaml_str = text.strip()

    return yaml_str


def format_time_from_db(time_str: str):
    try:
        dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S.%f")
        return dt.strftime("%Y-%m-%d %I:%M %p")
    except (ValueError, TypeError):
        # If the format does not match or is empty, return the original value
        return time_str
