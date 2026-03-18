from dotenv import load_dotenv

load_dotenv()  # loads .env if present (local dev); no-op on Alexa-hosted

from ask_sdk_core.skill_builder import SkillBuilder

from alexa_gemini.handlers.help import HelpIntentHandler
from alexa_gemini.handlers.launch import LaunchRequestHandler
from alexa_gemini.handlers.llm_intent import LLMIntentHandler
from alexa_gemini.handlers.session_ended import SessionEndedRequestHandler
from alexa_gemini.handlers.stop_cancel import StopCancelIntentHandler

sb = SkillBuilder()
sb.add_request_handler(LaunchRequestHandler())
sb.add_request_handler(LLMIntentHandler())
sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(StopCancelIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())

handler = sb.lambda_handler()
