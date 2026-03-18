"""LaunchRequestHandler — greets the user and opens the session."""

from ask_sdk_core.dispatch_components import AbstractRequestHandler  # type: ignore[attr-defined]
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response  # type: ignore[attr-defined]

WELCOME = (
    "Hello! I'm your Gemini-powered assistant. Ask me anything! "
    "— Ciao! Sono il tuo assistente Gemini. Chiedimi pure!"
)


class LaunchRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_request_type  # type: ignore[attr-defined]
        return is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        return (
            handler_input.response_builder
            .speak(WELCOME)
            .set_should_end_session(False)
            .response
        )
