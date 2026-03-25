import json
import os
from pathlib import Path
from datetime import datetime

# Get project root directory
config_file_path = Path(__file__).resolve()
project_dir = config_file_path.parents[2]


class Config:
    # System settings
    cuda_visible_devices = '0'

    # Sandbox settings
    start_datetime = '2024-09-01 12:00 AM'
    time_increment_per_iteration = '01:00:00'
    # 24 hours * 14 days
    max_iteration = 24 * 14
    prompt_folder = f'{project_dir}/reverie/prompts/prompt-1'
    data_dir = f'{project_dir}/data'
    story_name = "story01"
    story_dir = f"{data_dir}/{story_name}"
    output_dir = f'{project_dir}/output/14days/{story_name}/{datetime.now().strftime("%Y-%m-%d-%H-%M")}'
    log_dir = f"{output_dir}/logs"
    embedding_model_name = "jinaai/jina-embeddings-v3"

    # database
    database_url = f"sqlite:///{output_dir}/db.sqlite"

    # prompt
    ## Model name
    llm_model_name = 'gpt-4o-mini'
    ## Model temperature
    temperature = 0.8
    ## Maximum retries
    max_retries = 5
    ## Timeout
    timeout = 60
    ## Maximum context window size, 0.8 is a conservative estimate
    max_context_length = int(128000 * 0.8)
    ## Maximum number of generated tokens
    max_tokens = 8000
    ## OpenAI
    base_url = 'https://api.openai.com/v1'
    api_key = os.getenv('OPENAI_API_KEY', '<YOUR_API_KEY>')

    # plan
    ## Random values in choose_reaction
    plan = {
        'move': 0.6,
        'chat': 0.3,
        'none': 0.1,
        'abnormal_factor': 0.3
    }

    # execute
    ## Number of words spoken per second during chat
    execute = {
        'chat_avg_speed': 3,
        'round_num': 2,
    }

    # reflect
    reflect = {
        # Random ratio for memory selection in generate_focal_points()
        'random_memory_ratio': 0.3
    }

    # storyteller
    storyteller = {
        'window_of_day': 2
    }

    # faiss_manager
    faiss_manager = {
        'dimension': 512
    }

    @classmethod
    def save_to_json(cls, file_path):
        # Ignore classmethod
        def custom_serializer(obj):
            if isinstance(obj, classmethod):
                return None
            raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")

        config_dict = {k: v for k, v in vars(cls).items() if not k.startswith('__') and not callable(v)}

        # Ensure the directory exists
        os.makedirs(os.path.dirname(file_path), exist_ok=True)

        # Write the dictionary to a JSON file
        with open(file_path, 'w') as f:
            json.dump(config_dict, f, default=custom_serializer, indent=4)


os.environ['CUDA_VISIBLE_DEVICES'] = Config.cuda_visible_devices

Config.save_to_json(f"{Config.output_dir}/config.json")
