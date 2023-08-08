import backoff
import openai

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
def chat_completion_request(
    messages, functions=None, model=GPT35, function_call=None, temperature=0
):
    json_data = {"model": model, "messages": messages, "temperature": temperature}
    if functions is not None:
        json_data.update({"functions": functions})
    if function_call is not None:
        json_data.update({"function_call": {"name": function_call}})
    try:
        return openai.ChatCompletion.create(**json_data)
    except Exception as e:
        print("Unable to generate ChatCompletion response")
        print(f"Exception: {e}")
        return e
