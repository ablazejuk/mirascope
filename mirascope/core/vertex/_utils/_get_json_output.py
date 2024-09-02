"""Get JSON output from a Vertex response."""

import json

from proto.marshal.collections import RepeatedComposite

from ..call_response import VertexCallResponse
from ..call_response_chunk import VertexCallResponseChunk


def get_json_output(
    response: VertexCallResponse | VertexCallResponseChunk, json_mode: bool
) -> str:
    """Extracts the JSON output from a Vertex response."""
    if isinstance(response, VertexCallResponse):
        if json_mode and response.content:
            return response.content
        elif tool_calls := [
            part.function_call
            for part in response.response.parts
            if part.function_call.args
        ]:
            return json.dumps(
                {
                    k: v if not isinstance(v, RepeatedComposite) else list(v)
                    for k, v in tool_calls[0].args.items()
                }
            )
        else:
            raise ValueError("No tool call or JSON object found in response.")
    elif not json_mode:
        raise ValueError("Vertex only supports structured streaming in json mode.")
    return response.content
