"""Basic Prompt + LLM Example."""
from mirascope.prompt import MirascopePromptTemplate


prev_revision_id = "None"

revision_id = "0001"


class MyPrompt(MirascopePromptTemplate):
    """This is a prompt 0001. It has a {noun} and a {verb}."""

    noun: str
    verb: str
