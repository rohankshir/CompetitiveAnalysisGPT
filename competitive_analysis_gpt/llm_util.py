import backoff
import openai

import diskcache as dc
from functools import wraps
import json

cache = dc.Cache("cache")


def cache_key(*args, **kwargs):
    return json.dumps((args, kwargs), sort_keys=True, default=str)


def cache_disk(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = cache_key(*args, **kwargs)
        result = cache.get(key)
        # if result is none or error
        if result is None or isinstance(result, Exception):
            result = func(*args, **kwargs)
            cache.set(key, result)
        else:
            print(type(result))
            print("Cache hit")
        return result

    return wrapper


GPT4 = "gpt-4-32k"
GPT35 = "gpt-3.5-turbo-16k"


@backoff.on_exception(
    wait_gen=backoff.expo,
    exception=(
        openai.error.ServiceUnavailableError,
        openai.error.APIError,
        openai.error.RateLimitError,
        openai.error.APIConnectionError,
        openai.error.Timeout,
    ),
    max_value=60,
    factor=1.5,
)
@cache_disk
def chat_completion_request(
    messages, functions=None, model=GPT35, function_call=None, temperature=0
):
    json_data = {"model": model, "messages": messages, "temperature": temperature}
    if functions is not None:
        json_data.update({"functions": functions})
    if function_call is not None:
        json_data.update({"function_call": {"name": function_call}})
    return openai.ChatCompletion.create(**json_data)
