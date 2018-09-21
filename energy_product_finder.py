# -*- coding: utf-8 -*-
#
from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk.standard import StandardSkillBuilder

from ask_sdk_core.utils import is_request_type, is_intent_name
from ask_sdk_model.ui import SimpleCard
from ask_sdk_core.handler_input import HandlerInput
from ask_sdk_model.dialog.delegate_directive import DelegateDirective
from ask_sdk_model.dialog.elicit_slot_directive import ElicitSlotDirective
from sodapy import Socrata
import os


######## Convert SSML to Card text ############
# This is for automatic conversion of ssml to text content on simple card
# You can create your own simple cards for each response, if this is not
# what you want to use.

from six import PY2
try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser


class SSMLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.full_str_list = []
        if not PY2:
            self.strict = False
            self.convert_charrefs = True

    def handle_data(self, d):
        self.full_str_list.append(d)

    def get_data(self):
        return ''.join(self.full_str_list)

################################################

skill_name = "Energy Product Finder"
help_text = ("Please tell me product category. You can say \'find items for Electric Bulb\'")
reprompt_text = "Sorry I could not find product category. You can say \'find Electric Bulb\'"
sorry_text = "Sorry there is some problem in getting the data"
technology_slot = "Technology"
power_slot = "Power"
const_app_key = os.environ["energy_star_app_token"]
const_domain = "data.energystar.gov"
products = {"Light_Bulb":"sqpq-tg7c",
            "Ceiling_Fan":"qq83-fs92",
            "AC":"gwgp-353b",
            "Refrigerators":"ymjh-yrse"
            }

current_index = "index"
current_item_list = "current_item_list" 
current_product = "current_product"
#next_choice = "  To Know Next Item say Yes"
next_choice = ""

item_found = 0
sb = SkillBuilder()
#sb = StandardSkillBuilder(table_name="energy-product-finder", auto_create_table=True)


@sb.request_handler(can_handle_func=is_request_type("LaunchRequest"))
def launch_request_handler(handler_input: HandlerInput):
    # Handler for Skill Launch

    speech = "Welcome Please tell me the product name. You can say Find items for Light Bulb"    
    handler_input.response_builder.speak(speech ).set_should_end_session(False).ask(reprompt_text)

    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("FindLightBulbIntent"))
def find_light_bulb_handler(handler_input: HandlerInput):
    # Check if a product category has already been recorded in session attributes   
    slots = handler_input.request_envelope.request.intent.slots
    bulb_tech_slot_val = slots[technology_slot].value
    bulb_watt_slot_val = slots[power_slot].value  
    speech = ""
    dialogstate = handler_input.request_envelope.request.dialog_state
    intent_request = handler_input.request_envelope.request.intent    

    if dialogstate.value != "COMPLETED" and (bulb_tech_slot_val is None or bulb_watt_slot_val is None):    
        handler_input.response_builder.set_should_end_session(False)
        handler_input.response_builder.add_directive(DelegateDirective(updated_intent=intent_request))
        return handler_input.response_builder.response
    else:
        if str.upper(bulb_tech_slot_val) not in ["CFL", "LED"]:
            speech = "Please select type of bulb as CFL or LED. Tell me the type of bulb."            
            handler_input.response_builder.set_should_end_session(False)
            handler_input.response_builder.set_should_end_session(ElicitSlotDirective(updated_intent=intent_request,slot_to_elicit=technology_slot))
            
        else:        
            bulb_data = get_bulb_data(technology=str.upper(bulb_tech_slot_val),power=str(bulb_watt_slot_val))     

            if(bulb_data != None):  
                get_bulb_speech_out = get_bulb_speech(bulb_data[0])
                handler_input.response_builder.set_should_end_session(True).speak(get_bulb_speech_out[0])
                handler_input.response_builder.set_card(SimpleCard(title=skill_name, content=get_bulb_speech_out[1]))
                
            else:
                handler_input.response_builder.set_should_end_session(True).speak(sorry_text)
                handler_input.response_builder.set_card(SimpleCard(title=skill_name, content=sorry_text))               
                        
    return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("FindFanIntent"))
def find_fan_handler(handler_input: HandlerInput):
    dialogstate = handler_input.request_envelope.request.dialog_state
    intent_request = handler_input.request_envelope.request.intent
    slots = handler_input.request_envelope.request.intent.slots
    fan_power_slot_val = slots['Fan_Power'].value

    if dialogstate.value != "COMPLETED" and fan_power_slot_val is None:
        handler_input.response_builder.set_should_end_session(False)
        handler_input.response_builder.add_directive(DelegateDirective(updated_intent=intent_request))
        return handler_input.response_builder.response

    else:
        try:
            val = int(fan_power_slot_val)
        except ValueError:
            print("exception occur in fan handler")
            fan_power_slot_val = 40        
        
        fan_data = get_fan_data(fan_power_slot_val)

        if(fan_data != None):   
            get_fan_speech_out = get_fan_speech(fan_data[0])  
            handler_input.response_builder.speak(get_fan_speech_out[0])
            handler_input.response_builder.set_card(SimpleCard(title=skill_name, content=get_fan_speech_out[1])) 
        else:
            handler_input.response_builder.speak(sorry_text)
            handler_input.response_builder.set_card(SimpleCard(title=skill_name, content=sorry_text))
                       
        handler_input.response_builder.set_should_end_session(True)
        return handler_input.response_builder.response



@sb.request_handler(can_handle_func=is_intent_name("FindACIntent"))
def find_ac_handler(handler_input: HandlerInput):

    dialogstate = handler_input.request_envelope.request.dialog_state
    intent_request = handler_input.request_envelope.request.intent
    slots = handler_input.request_envelope.request.intent.slots
    ac_type_val = slots['AC_Type'].value     
    ac_capacity_val = slots['AC_Capacity'].value

    if dialogstate.value != "COMPLETED" and (ac_type_val is None or ac_capacity_val is None):          
        handler_input.response_builder.set_should_end_session(False)
        handler_input.response_builder.add_directive(DelegateDirective(updated_intent=intent_request))
        return handler_input.response_builder.response    
    else:
        if str.upper(ac_type_val).find("WINDOW") >= 0 :
            ac_type_val = "Window"
        elif str.upper(ac_type_val).find("WALL") >= 0:
            ac_type_val = "Through the Wall"
        else:
            ac_type_val = "Window"
        
        ac_data = get_ac_data(ac_type_val, ac_capacity_val)

        if(ac_data != None):   
            get_ac_speech_out = get_ac_speech(ac_data[0])  
            handler_input.response_builder.speak(get_ac_speech_out[0])
            handler_input.response_builder.set_card(SimpleCard(title=skill_name, content=get_fan_speech_out[1])) 
        else:
            handler_input.response_builder.speak(sorry_text)
            handler_input.response_builder.set_card(SimpleCard(title=skill_name, content=sorry_text))              
        handler_input.response_builder.set_should_end_session(True)
        return handler_input.response_builder.response


@sb.request_handler(can_handle_func=is_intent_name("FindFridgeIntent"))
def find_fridge_handler(handler_input: HandlerInput):
    dialogstate = handler_input.request_envelope.request.dialog_state
    intent_request = handler_input.request_envelope.request.intent
    slots = handler_input.request_envelope.request.intent.slots        
    freezer_Location_val = slots['Freezer_Location'].value
    freezer_capacity_val =   slots['Capacity'].value         

    if dialogstate.value != "COMPLETED" and (freezer_Location_val is None or freezer_capacity_val is None):              
        handler_input.response_builder.set_should_end_session(False)
        handler_input.response_builder.add_directive(DelegateDirective(updated_intent=intent_request))
        return handler_input.response_builder.response    

    else:        
        fridge_data = get_fridge_data(freezer_Location_val, freezer_capacity_val)
        if(fridge_data != None):   
            get_fridge_speech_out = get_fridge_speech(fridge_data[0])  
            handler_input.response_builder.set_should_end_session(True).speak(get_fridge_speech_out[0])
            handler_input.response_builder.set_card(SimpleCard(title=skill_name, content=get_fan_speech_out[1]))
        else:
            handler_input.response_builder.set_should_end_session(True).speak(sorry_text)
            handler_input.response_builder.set_card(SimpleCard(title=skill_name, content=sorry_text))            

        return handler_input.response_builder.response


def get_bulb_speech(item: list):
    speech_out = "Sorry there is some problem in finding the data"
    text_out = speech_out
    try:
        speech_out = str.format("Bulb Type {0} , Brand {1}, Power {2},  Model Name {3}, Lumens {4}, Equivalent Traditional Bulb Power {5}, Power Factor {6} and Warrnty Years is {7}",
        item['technology'], item['brand_name'], item['energy_used_watts'], item['model_name'],item['brightness_lumens'],item['wattage_equivalency_watts'],item['power_factor'], item['warranty_years'])
        text_out = str.format("Bulb Type {0}  Brand {1} power {2}  model name {3} lumens \
        {4} warrnty years {5}", item['technology'],item['brand_name'],
        item['energy_used_watts'], item['model_name'],item['brightness_lumens'], item['warranty_years'])

        return [speech_out, text_out]
    except Exception as exc:
        print("Encountered following exception: {0}".format(exc))
        return [speech_out, text_out] 


def get_bulb_data(technology=None, power=None):
    try:
        print("getting bulb data")
        client = Socrata(const_domain, const_app_key)
        _prod = products["Light_Bulb"]
        if (technology != None and  power != None):
            query_data = client.get( _prod, content_type="json", technology=technology, where='energy_used_watts>=' + str(power), order='energy_used_watts', limit=10)
        elif(technology == None and  power != None):
            query_data = client.get( _prod, content_type="json", where='energy_used_watts>=' + str(power), order='energy_used_watts', limit=10)            
        elif technology != None and  power == None:
            query_data = client.get( _prod, technology=technology, content_type="json", limit=10)
        else:
            query_data = client.get( _prod, content_type="json", limit=10)

        item_found = len(query_data)
        if item_found > 0:
            return query_data
        else:
            # try without any filter           
            query_data = client.get( _prod, content_type="json", limit=10)
            item_found = len(query_data)
            if item_found > 0:
                return query_data
            else:
                return None
        
    except Exception as exc:
        print("Encountered following exception in get_bulb_data: {0}".format(exc))
        return None

def get_fan_speech(item: list):
    speech_out = "Sorry there is some problem in finding the data"
    text_out = speech_out
    title = "Ceiling Fan Item Details are "
    try:
        speech_out = str.format("Fan Type {0} , Brand {1}, Product Type {2},  Model Name {3}, Fan Power Consumtion at High Speed {4}, Fan Diameter {5} inches",
        item['indoor_outdoor'], item['brand_name'], item['product_type'], item['model_name'],item['fan_power_consumption_high_speed_w'],item['ceiling_fan_size_diameters_in_inches'])
        text_out = str.format("Fan Type {0} , Brand {1}, Product Type {2},  Model Name {3}",item['indoor_outdoor'], item['brand_name'], item['product_type'], item['model_name'])
        return [title + speech_out, text_out]
    except Exception as exc:
        print("Encountered following exception: {0}".format(exc))
        return [speech_out, text_out] 


def get_fan_data(fan_power):
    try:
        # title_text = "Product details"
        print("getting fan data")
        client = Socrata(const_domain, const_app_key)        
        _prod = products["Ceiling_Fan"]
        if (fan_power != None ):
            query_data = client.get( _prod, content_type="json", where='fan_power_consumption_high_speed_w >=' + str(fan_power), order='fan_power_consumption_high_speed_w ASC',  limit=10)       
        if len(query_data) > 0:
            return query_data
        else:
            query_data = client.get( _prod, content_type="json", where='fan_power_consumption_high_speed_w <=' + str(fan_power), order='fan_power_consumption_high_speed_w DESC',  limit=10)
            if len(query_data)>0:
                return query_data
            else:
                # get generic query
                query_data = client.get( _prod, content_type="json",  limit=10)
                if len(query_data) >0:
                    return query_data
                else:
                    return None            
        
    except Exception as exc:
        print("Encountered following exception in get_fan_data: {0}".format(exc))
        return None



def get_fridge_speech(item: list):
    speech_out = "Sorry there is some problem in finding the data"
    text_out = speech_out
    title = "Refrigerator Item Details are "
    try:
        speech_out = str.format("Brand Name {0} , Freezer Location {1}, Height {2} inches,  Width {3} inches , Capacity {4} cubic feet and  Anual Energy Use {5} Unit per year",
        item['brand_name'], item['type'], item['height_in'], item['width_in'],item['capacity_total_volume_ft3'],item['annual_energy_use_kwh_yr'])
        text_out = str.format(speech_out)
        return [title + speech_out, text_out]
    except Exception as exc:
        print("Encountered following exception: {}".format(exc))
        return [speech_out, text_out] 


def get_fridge_data(location, capacity):
    try:
        # title_text = "Product details"
        print("getting fridge data")
        client = Socrata(const_domain, const_app_key)        
        _prod = products["Refrigerators"]
        if (location != None ):
            query_data = client.get( _prod, content_type="json", type=location, where='capacity_total_volume_ft3  >=' + str(capacity),
            order='capacity_total_volume_ft3 ASC',  limit=10)       
        if len(query_data) > 0:
            return query_data
        else:
            query_data = client.get( _prod, content_type="json", type=location, where='capacity_total_volume_ft3 <=' + str(capacity),
            order='capacity_total_volume_ft3 DESC',  limit=10)
            if len(query_data)>0:
                return query_data
            else:
                # get generic query
                query_data = client.get( _prod, content_type="json",  limit=10)
                if len(query_data) >0:
                    return query_data
                else:
                    return None            
        
    except Exception as exc:
        print("Encountered following exception in get_fridge_data: {0}".format(exc))
        return None



def get_ac_speech(item: list):
    speech_out = "Sorry there is some problem in finding the data"
    text_out = speech_out
    title = "AC Item Details are "
    try:
        speech_out = str.format("Brand Name {0} , Model Number {1}, Type  {2}, Cooling Capacity  {3} BTU perhour, additional_model_information  {4}, Anual Energy Use {5} Unit per year",
        item['brand_name'], item['model_number'], item['type'], item['cooling_capacity_btu_hour'],item['additional_model_information'],item['annual_energy_use_kwh_yr'])
        text_out = str.format(speech_out)
        return [title + speech_out, text_out]
    except Exception as exc:
        print("Encountered following exception in get_ac_speech: {0}".format(exc))
        return [speech_out, text_out] 


def get_ac_data(ac_type, capacity):
    try:
        # title_text = "Product details"
        print("getting ac data")
        client = Socrata(const_domain, const_app_key)        
        _prod = products["AC"]

        if (ac_type != None ):
            query_data = client.get( _prod, content_type="json", type=ac_type, where='cooling_capacity_btu_hour  >=' + str(capacity), order='cooling_capacity_btu_hour ASC',  limit=10)       
        if len(query_data) > 0:
            return query_data
        else:
            query_data = client.get( _prod, content_type="json", type=ac_type, where='cooling_capacity_btu_hour <=' + str(capacity), order='cooling_capacity_btu_hour DESC',  limit=10)
            if len(query_data) > 0:
                return query_data
            else:
                # get generic query
                query_data = client.get( _prod, content_type="json",  limit=10)
                if len(query_data) > 0:
                    return query_data
                else:
                    return None            
        
    except Exception as exc:
        print("Exception occured in get_ac_data : {0}".format(exc))
        return None


@sb.request_handler(can_handle_func=is_intent_name("AMAZON.HelpIntent"))
def help_intent_handler(handler_input):
    # Handler for Help Intent
    handler_input.response_builder.speak(help_text).ask(help_text)
    return handler_input.response_builder.response


@sb.request_handler(
    can_handle_func=lambda input:
        is_intent_name("AMAZON.CancelIntent")(input) or
        is_intent_name("AMAZON.StopIntent")(input))
def cancel_and_stop_intent_handler(handler_input):
    # Single handler for Cancel and Stop Intent
    speech_text = "Goodbye!"

    return handler_input.response_builder.speak(speech_text).response


@sb.request_handler(can_handle_func=is_request_type("SessionEndedRequest"))
def session_ended_request_handler(handler_input):
    # Handler for Session End
    return handler_input.response_builder.response



@sb.request_handler(can_handle_func=is_intent_name("AMAZON.FallbackIntent"))
def fallback_handler(handler_input):
    # AMAZON.FallbackIntent is only available in en-US locale.
    # This handler will not be triggered except in that locale,
    # so it is safe to deploy on any locale
    speech = (
        "The {0} skill can't help you with that.  "
        "You can tell me your product by saying, "
        "Find Light Bulb").format(skill_name)
    reprompt = ("You can tell me product by saying Find AC")
    handler_input.response_builder.speak(speech).ask(reprompt)
    return handler_input.response_builder.response


def convert_speech_to_text(ssml_speech):
    # convert ssml speech to text, by removing html tags
    s = SSMLStripper()
    s.feed(ssml_speech)
    return s.get_data()


# @sb.global_response_interceptor()
# def add_card(handler_input, response):
#     # Add a card by translating ssml text to card content
#     if response.output_speech.ssml is not None:        
#         response.card = SimpleCard(
#             title=skill_name,
#             content=convert_speech_to_text(response.output_speech.ssml))



    

@sb.global_response_interceptor()
def log_response(handler_input, response):
    # Log response from alexa service
    print("Alexa Response: {0}\n".format(response))


@sb.global_request_interceptor()
def log_request(handler_input):
    # Log request to alexa service
    print("Alexa Request: {0}\n".format(handler_input.request_envelope.request))


@sb.exception_handler(can_handle_func=lambda i, e: True)
def all_exception_handler(handler_input, exception):
    # Catch all exception handler, log exception and
    # respond with custom message
    print("Encountered following exception: {0}".format(exception))
    return handler_input.response_builder.response


# Handler to be provided in lambda console.
handler = sb.lambda_handler()