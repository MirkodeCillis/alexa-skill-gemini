"""HelpIntentHandler."""

from ask_sdk_core.dispatch_components import AbstractRequestHandler  # type: ignore[attr-defined]
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response  # type: ignore[attr-defined]

HELP_TEXT = (
    "Just ask me anything — current events, general knowledge, or any question you have. "
    "Say 'stop' to end. "
    "— Chiedimi qualsiasi cosa: notizie, curiosità o qualsiasi domanda. "
    "Di' 'stop' per uscire."
)


class HelpIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        request = handler_input.request_envelope.request
        return (
            request.object_type == "IntentRequest"  # type: ignore[union-attr]
            and request.intent.name == "AMAZON.HelpIntent"  # type: ignore[union-attr]
        )

    def handle(self, handler_input: HandlerInput) -> Response:
        return (
            handler_input.response_builder
            .speak(HELP_TEXT)
            .set_should_end_session(False)
            .response
        )
