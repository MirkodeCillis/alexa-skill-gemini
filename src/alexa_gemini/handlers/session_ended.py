"""SessionEndedRequestHandler — cleans up when the session closes."""

from ask_sdk_core.dispatch_components import AbstractRequestHandler  # type: ignore[attr-defined]
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response  # type: ignore[attr-defined]


class SessionEndedRequestHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_request_type  # type: ignore[attr-defined]
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        session_attrs = handler_input.attributes_manager.session_attributes
        if session_attrs is not None:
            session_attrs["history"] = []
        return handler_input.response_builder.response
