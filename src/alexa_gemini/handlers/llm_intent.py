"""LLMIntentHandler — core chat loop."""

from ask_sdk_core.dispatch_components import AbstractRequestHandler  # type: ignore[attr-defined]
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model import Response  # type: ignore[attr-defined]

from alexa_gemini.config import load_config
from alexa_gemini.services.gemini import GeminiService

REPROMPT = (
    "Sorry, I didn't catch that. What would you like to ask? "
    "— Scusa, non ho capito. Cosa vorresti chiedere?"
)


class LLMIntentHandler(AbstractRequestHandler):
    def can_handle(self, handler_input: HandlerInput) -> bool:
        from ask_sdk_core.utils import is_intent_name  # type: ignore[attr-defined]
        return is_intent_name("LLMIntent")(handler_input)

    def handle(self, handler_input: HandlerInput) -> Response:
        slots = handler_input.request_envelope.request.intent.slots  # type: ignore[union-attr]
        question_slot = slots.get("question") if slots else None
        question = (question_slot.value or "").strip() if question_slot else ""

        if not question:
            return (
                handler_input.response_builder
                .speak(REPROMPT)
                .set_should_end_session(False)
                .response
            )

        session_attrs = handler_input.attributes_manager.session_attributes
        history: list[dict[str, object]] = (
            session_attrs.get("history", []) if session_attrs is not None else []
        )

        config = load_config()
        service = GeminiService(config)
        response_text, updated_history = service.chat(question, history)

        if session_attrs is not None:
            session_attrs["history"] = updated_history

        return (
            handler_input.response_builder
            .speak(response_text)
            .set_should_end_session(False)
            .response
        )
