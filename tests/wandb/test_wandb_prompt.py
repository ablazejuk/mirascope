"""Tests for `WandbPrompt`."""
from unittest.mock import MagicMock, patch

import pytest
from openai.types import CompletionUsage
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
    Function,
)
from pydantic import BaseModel
from wandb.sdk.data_types.trace_tree import Trace

from mirascope.base.tools import convert_function_to_tool
from mirascope.openai import OpenAIChatCompletion, OpenAITool
from mirascope.wandb.prompt import WandbPrompt


class GreetingsPrompt(WandbPrompt):
    """This is a test prompt. {greeting}!"""

    greeting: str


@pytest.mark.parametrize("span_type", ["tool", "llm"])
def test__init(span_type):
    """Test initialization."""
    prompt = GreetingsPrompt(span_type=span_type, greeting="Hello")
    assert prompt.span_type == span_type
    assert prompt.call_params.model == "gpt-3.5-turbo-0125"


def test_init_invalid_span_type():
    """Test initialization with invalid span type."""
    with pytest.raises(ValueError):
        WandbPrompt(span_type="invalid")


@patch(
    "wandb.sdk.data_types.trace_tree.Trace.add_child",
    new_callable=MagicMock,
)
def test_trace_completion(mock_Trace: MagicMock):
    """Test `trace` method with `OpenAIChatCompletion`."""
    prompt = GreetingsPrompt(span_type="llm", greeting="Hello")
    completion = OpenAIChatCompletion(
        completion=ChatCompletion(
            id="test",
            choices=[
                Choice(
                    finish_reason="tool_calls",
                    index=0,
                    logprobs=None,
                    message=ChatCompletionMessage(
                        content="HI!",
                        role="assistant",
                        function_call=None,
                        tool_calls=None,
                    ),
                )
            ],
            created=0,
            model="gpt-3.5-turbo-0125",
            object="chat.completion",
            system_fingerprint=None,
            usage=CompletionUsage(completion_tokens=1, prompt_tokens=2, total_tokens=3),
        ),
        tool_types=[convert_function_to_tool(tool_fn, OpenAITool)],
        start_time=0,
        end_time=0,
    )
    span = prompt.trace(completion, parent=Trace(name="test"))
    assert span.name == "GreetingsPrompt"
    assert span.kind == "LLM"
    assert span.status_code == "SUCCESS"
    assert span.status_message is None
    if span.metadata:
        assert span.metadata["call_params"]["model"] == "gpt-3.5-turbo-0125"  # type: ignore
        assert span.metadata["usage"] == {
            "completion_tokens": 1,
            "prompt_tokens": 2,
            "total_tokens": 3,
        }
    assert span.inputs == {"user": "This is a test prompt. Hello!"}
    assert span.outputs == {"assistant": "HI!"}
    mock_Trace.assert_called_once()


def tool_fn(word: str) -> str:
    """Test function."""
    return word + "!"


@patch(
    "wandb.sdk.data_types.trace_tree.Trace.add_child",
    new_callable=MagicMock,
)
def test_trace_completion_tool(mock_Trace: MagicMock):
    """Test `trace` method with `OpenAIChatCompletion`."""
    prompt = GreetingsPrompt(span_type="tool", greeting="Hello")
    completion = OpenAIChatCompletion(
        completion=ChatCompletion(
            id="test",
            choices=[
                Choice(
                    finish_reason="tool_calls",
                    index=0,
                    logprobs=None,
                    message=ChatCompletionMessage(
                        content=None,
                        role="assistant",
                        function_call=None,
                        tool_calls=[
                            ChatCompletionMessageToolCall(
                                id="1",
                                function=Function(
                                    arguments='{"word": "pizza"}',
                                    name="ToolFn",
                                ),
                                type="function",
                            )
                        ],
                    ),
                )
            ],
            created=0,
            model="gpt-3.5-turbo-0125",
            object="chat.completion",
            system_fingerprint=None,
            usage=CompletionUsage(completion_tokens=1, prompt_tokens=2, total_tokens=3),
        ),
        tool_types=[convert_function_to_tool(tool_fn, OpenAITool)],
        start_time=0,
        end_time=0,
    )
    span = prompt.trace(completion, parent=Trace(name="test"))
    assert span.name == "GreetingsPrompt"
    assert span.kind == "TOOL"
    assert span.status_code == "SUCCESS"
    assert span.status_message is None
    if span.metadata:
        assert span.metadata["call_params"]["model"] == "gpt-3.5-turbo-0125"  # type: ignore
        assert span.metadata["usage"] == {
            "completion_tokens": 1,
            "prompt_tokens": 2,
            "total_tokens": 3,
        }
    assert span.inputs == {"user": "This is a test prompt. Hello!"}
    assert span.outputs == {
        "assistant": {
            "tool_call": {
                "id": "1",
                "function": {"arguments": '{"word": "pizza"}', "name": "ToolFn"},
                "type": "function",
            },
            "word": "pizza",
        },
        "tool_output": "pizza!",
    }
    mock_Trace.assert_called_once()


class MyModel(BaseModel):
    param: str


def test_trace_base_model():
    """Tests `trace` method with `BaseModel`."""
    prompt = GreetingsPrompt(span_type="tool", greeting="Hello")

    completion = MyModel(param="test")
    with pytest.raises(ValueError):
        prompt.trace(completion, parent=Trace(name="test"))
    completion._completion = OpenAIChatCompletion(
        completion=ChatCompletion(
            id="test",
            choices=[
                Choice(
                    finish_reason="tool_calls",
                    index=0,
                    logprobs=None,
                    message=ChatCompletionMessage(
                        content="HI!",
                        role="assistant",
                        function_call=None,
                        tool_calls=None,
                    ),
                )
            ],
            created=0,
            model="gpt-3.5-turbo-0125",
            object="chat.completion",
            system_fingerprint=None,
            usage=CompletionUsage(completion_tokens=1, prompt_tokens=2, total_tokens=3),
        ),
        tool_types=[convert_function_to_tool(tool_fn, OpenAITool)],
        start_time=0,
        end_time=0,
    )
    span = prompt.trace(completion, parent=Trace(name="test"))
    assert span.name == "GreetingsPrompt"
    assert span.kind == "TOOL"
    assert span.status_code == "SUCCESS"


def test_trace_error():
    """Test `trace_error` method."""
    error = Exception("Test error")
    prompt = GreetingsPrompt(span_type="llm", greeting="Hello")
    span = prompt.trace_error(error, parent=Trace(name="test"))
    assert span.name == "GreetingsPrompt"
    assert span.kind == "LLM"
    assert span.status_code == "ERROR"
    assert span.status_message == "Test error"
    if span.metadata:
        assert span.metadata["call_params"]["model"] == "gpt-3.5-turbo-0125"
    assert span.inputs == {"user": "This is a test prompt. Hello!"}
    assert span.outputs is None
