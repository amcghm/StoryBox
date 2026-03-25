import torch

from langchain_openai import ChatOpenAI
from langchain_community.chat_models import ChatOllama
from langchain_huggingface import HuggingFacePipeline
from langchain_huggingface import ChatHuggingFace
from transformers import AutoModel
from loguru import logger

from reverie.config.config import Config


def get_chat_model(
        model_name,
        temperature,
        base_url='http://localhost:11434'
):
    # Ollama
    if model_name in {'llama3.1:8b-instruct-fp16'}:
        chat_model = ChatOllama(
            model=model_name,
            temperature=temperature,
            base_url=base_url
        )

    # Huggingface
    elif model_name in {'mistralai/Mistral-7B-Instruct-v0.3'}:
        llm = HuggingFacePipeline.from_model_id(
            model_id=model_name,
            task="text-generation",
            pipeline_kwargs={"max_new_tokens": 32 * 1024},
            device=0,
            model_kwargs={"torch_dtype": torch.bfloat16}
        )
        chat_model = ChatHuggingFace(llm=llm)

    # OpenAI
    elif model_name in {'gpt-5-nano', 'gpt-4o-mini', 'gemini-1.5-flash'}:
        chat_model = ChatOpenAI(
            model=model_name,
            temperature=temperature,
            max_retries=Config.max_retries,
            timeout=Config.timeout,
            base_url=Config.base_url,
            api_key=Config.api_key,
            max_tokens=Config.max_tokens
        )

    else:
        raise ValueError(f"Model '{model_name}' is not supported.")

    return chat_model


def get_embedding_model(model_name):
    embedding_model = AutoModel.from_pretrained(model_name, trust_remote_code=True)
    embedding_model = embedding_model.to('cuda')
    return embedding_model


logger.debug(f"Loading embedding model: {Config.embedding_model_name}")
embedding_model = get_embedding_model(Config.embedding_model_name)
logger.debug(f"Loaded embedding model: {Config.embedding_model_name}")
