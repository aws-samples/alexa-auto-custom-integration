import boto3

from urllib.request import Request
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.utils import is_request_type, is_intent_name, get_account_linking_access_token, get_request_type, get_intent_name, get_slot_value_v2, get_simple_slot_values
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.ui import SimpleCard, output_speech
from ask_sdk_model import Response
from ask_sdk_core.skill_builder import SkillBuilder

import ask_sdk_core.utils as ask_utils
import logging
import json
import time
import requests

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
sb = SkillBuilder()

client = boto3.client('dynamodb')



class CheckAccountLinkedHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        print("check account is done")
        return not get_account_linking_access_token(handler_input)


    def handle(self, handler_input):
        print("Can CheckAccountLinkedHandler-------------------------------------------------------")
        return handler_input.response_builder.speak("Need to link account in Alexa App").response


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (is_intent_name("AMAZON.CancelIntent")(handler_input) or
                is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        print("Can CancelOrStopIntentHandler-------------------------------------------------------")
        # type: (HandlerInput) -> Response
        speech_text = "Goodbye!"

        handler_input.response_builder.speak(speech_text).set_card(
            SimpleCard("My Car", speech_text))
        return handler_input.response_builder.response


class FallbackIntentHandler(AbstractRequestHandler):
    """
    This handler will not be triggered except in supported locales,
    so it is safe to deploy on any locale.
    """

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        print("Can FallbackIntentHandler-------------------------------------------------------")
        # type: (HandlerInput) -> Response
        speech_text = (
            "The my car skill can't help you with that.  "
            "You can say hello!!")
        reprompt = "You can say hello!!"
        handler_input.response_builder.speak(speech_text).ask(reprompt)
        return handler_input.response_builder.response


class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""

    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        print("Can SessionEndedRequestHandler-------------------------------------------------------")
        # type: (HandlerInput) -> Response
        return handler_input.response_builder.response


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """Catch all exception handler, log exception and
    respond with custom message.
    """

    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        print("Can CatchAllExceptionHandler-------------------------------------------------------")
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)

        speech = "Sorry, there was some problem. Please try again!!"
        handler_input.response_builder.speak(speech).ask(speech)

        return handler_input.response_builder.response


class RequestInfoHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        logger.info("handler input request_envelope and context is: ")
        logger.info(handler_input.request_envelope)
        logger.info(handler_input.context)
        return is_request_type("IntentRequest")(handler_input) and is_intent_name("RequestInfoIntent")(handler_input)

    def handle(self, handler_input):
        print(
            "Can RequestInfoHandler-------------------------------------------------------")
        output_string = "You current vehicle status: " + \
            get_status(handler_input)
        return handler_input.response_builder.speak("Here is what you are looking for, " + output_string).set_card(
            SimpleCard("Car Status Check", output_string)
        ).response


class CarCtrlAirCondPwrHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        logger.info("handler input request_envelope and context is: ")
        logger.info(handler_input.request_envelope)
        logger.info(handler_input.context)
        return is_request_type("IntentRequest")(handler_input) and is_intent_name("CarCtrlAirCondPwrIntent")(handler_input)

    def handle(self, handler_input):
        print("Can CarCtrlAirCondPwrHandler-------------------------------------------------------")
        output_string = "Sending remote vehicle control commands: " + \
            set_status(handler_input)
        return handler_input.response_builder.speak("Here is what you are looking for, " + output_string).set_card(
            SimpleCard("Remote vehicle Control", output_string)
        ).response


class CarCtrlAirCondTempHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        logger.info("handler input request_envelope and context is: ")
        logger.info(handler_input.request_envelope)
        logger.info(handler_input.context)
        return is_request_type("IntentRequest")(handler_input) and is_intent_name("CarCtrlAirCondTempIntent")(handler_input)

    def handle(self, handler_input):
        print("Can CarCtrlAirCondTempHandler-------------------------------------------------------")
        output_string = "Sending remote vehicle control commands: " + \
            set_status(handler_input)
        return handler_input.response_builder.speak("Here is what you are looking for, " + output_string).set_card(
            SimpleCard("Remote vehicle Control", output_string)
        ).response

class CarCtrlAirCondFanHandler(AbstractRequestHandler):
    def can_handle(self, handler_input):
        print("handler input request_envelope and context is: ")
        return is_request_type("IntentRequest")(handler_input) and is_intent_name("CarCtrlAirCondFanIntent")(handler_input)

    def handle(self, handler_input):
        print("Can CarCtrlAirCondTempHandler-------------------------------------------------------")
        output_string = "Sending remote vehicle control commands: " + \
            set_status(handler_input)
        return handler_input.response_builder.speak("Here is what you are looking for, " + output_string).set_card(
            SimpleCard("Remote vehicle Control", output_string)
        ).response


# Util functions

def get_vin_key(handler_input):
    access_token = get_account_linking_access_token(handler_input)
    content = requests.get('https://api.amazon.com/user/profile?access_token='+access_token).content
    user_email_address = json.loads(content)['email']
    data = client.get_item(
        TableName='user_table',
        Key={
            'email_address': {
                'S': user_email_address
            }
        })
    return data["Item"]["vin"]["S"]


def get_status(handler_input):
    intent = ask_utils.get_intent_name(handler_input)
    key = get_vin_key(handler_input)
    resolved_id = get_resolved_id(
        handler_input.request_envelope.request, "infoTypeRequested")

    data = read_dynamodb(key)
    output_string = "with "

    if resolved_id == "MLG":
        output_string = "with " + data["Item"]["MLG"]["S"] + \
        " " + data["Item"]["MLG_unit"]["S"] + " mileage left"

    if resolved_id == "BAT":
        output_string = "battery with " + \
        data["Item"]["BAT"]["S"] + " " + \
        data["Item"]["BAT_unit"]["S"] + " left"

    return output_string


def set_status(handler_input):
    intent = ask_utils.get_intent_name(handler_input)
    output_string = " Set status: "
    vin_key = get_vin_key(handler_input)
    if intent == "CarCtrlAirCondPwrIntent":
        resolved_id = get_resolved_id(
            handler_input.request_envelope.request, "SetConditionRequested")
        print("------Set Status------ with INTENT = " +
              intent + "------ with Resolve ID = " + resolved_id)
        output_string = set_ac_pwr(resolved_id, vin_key)

    if intent == "CarCtrlAirCondTempIntent":
        slot_values = ask_utils.get_slot_value_v2(handler_input, "AC_TEMP_SET")
        print(format(slot_values))
        print("------Set Status------ with INTENT = " + intent +
              "------ with Slots AC_TEMP_SET = " + slot_values.value)
        output_string = set_ac_status("AC_TEMP_SET", slot_values.value, vin_key)

    if intent == "CarCtrlAirCondFanIntent":
        slot_values = ask_utils.get_slot_value_v2(handler_input, "AC_FAN_SET")
        print(format(slot_values))
        print("------Set Status------ with INTENT = " + intent +
              "------ with Slots AC_FAN_SET = " + slot_values.value)
        output_string = set_ac_status("AC_FAN_SET", slot_values.value, vin_key)

    return output_string

def get_ac_status(key):
    data = read_dynamodb(key)
    ac_status = "OFF"
    if data["Item"]["AC_PWR_SET"]["S"] == "1":
        ac_status = "ON"

    output_string = "air condition is " + data["Item"]["AC_PWR_SET"]["S"] + " with temperature of" + \
        data["Item"]["AC_TEMP_SET"]["S"] + \
        " and FAN speed level of " + data["Item"]["AC_FAN_SET"]["S"]
    return output_string

def set_ac_pwr(key, vin_key):
    output_string = "Air conditioner ERROR"
    if (key == "AC_PWR_ON"):
        set_dynamodb("AC_PWR_SET", "ON", vin_key)
        output_string = "Air conditioner ON"
    if (key == "AC_PWR_OFF"):
        set_dynamodb("AC_PWR_SET", "OFF", vin_key)
        output_string = "Air conditioner OFF"
    return output_string

def set_ac_status(key, value, set_ac_status, vin_key):
    output_string = "Air conditioner ERROR"
    if (key == "AC_TEMP_SET"):
        set_dynamodb(key, value, vin_key)
        output_string = "Set Air conditioner Temperature to " + value + " degrees"
    if (key == "AC_FAN_SET"):
        set_dynamodb(key, value, vin_key)
        output_string = "Set Air conditioner Fan Speed to Level " + value
    return output_string


sb.add_request_handler(CheckAccountLinkedHandler())
sb.add_request_handler(RequestInfoHandler())
sb.add_request_handler(CarCtrlAirCondPwrHandler())
sb.add_request_handler(CarCtrlAirCondTempHandler())
sb.add_request_handler(CarCtrlAirCondFanHandler())
# default_request_handler
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()


# Utility functions
def get_resolved_id(request, slot_name):
    """Resolve the slot name from the request using resolutions."""
    # type: (IntentRequest, str) -> Union[str, None]
    # slots_res_id = handler_input.request_envelope.request.intent.slots.infoTypeRequested.resolutions.resolutions_per_authority[0].values[0].value.id
    try:
        return (request.intent.slots[slot_name].resolutions.
                resolutions_per_authority[0].values[0].value.id)
    except (AttributeError, ValueError, KeyError, IndexError, TypeError) as e:
        logger.info("Couldn't resolve {} for request: {}".format(
            slot_name, request))
        logger.info(str(e))
        return None
TABLE_NAME = ''

def read_dynamodb(key):
    try:
        data = client.get_item(
            TableName='car_status_table',
            Key={
                'vin': {
                    'S': key
                }
            })
    except:
        logger.error("Can not read dynamo table")
        raise
    else:
        return data


def set_dynamodb(key, value, vin_key):
    try:
        client.update_item(
            TableName='car_status_table',
            Key={
                'vin': {
                    'S': vin_key
                }
            },
            AttributeUpdates={
                key: {
                    'Value': {
                        'S': value
                    }
                },
                'TS':{
                    'Value': {
                        'S': str(int(round(time.time() * 1000)))
                    }
                }
            }
        )
    except:
        logger.error("Can not set dynamodb table")
        raise
