"""StopCancelIntentHandler — ends the session gracefully."""

from ask_sdk_core.dispatch_components import AbstractRequestHandler  # type: ignore[attr-defined]
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response  # type: ignore[attr-defined]

GOODBYE = "Goodbye! — Arrivederci!"


class StopCancelIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_intent_name  # type: ignore[attr-defined]
        return is_intent_name("AMAZON.StopIntent")(handler_input) or is_intent_name(
            "AMAZON.CancelIntent"
        )(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        session_attrs = handler_input.attributes_manager.session_attributes
        if session_attrs is not None:
            session_attrs["history"] = []
        return (
            handler_input.response_builder
            .speak(GOODBYE)
            .set_should_end_session(True)
            .response
        )
