### Required Libraries ###
from datetime import datetime
from dateutil.relativedelta import relativedelta
import json
import boto3
import requests
### Functionality Helper Functions ###
def parse_int(n):
    """
    Securely converts a non-integer value to integer.
    """
    try:
        return int(n)
    except ValueError:
        return float("nan")
def build_validation_result(is_valid, violated_slot, message_content):
    """
    Define a result message structured as Lex response.
    """
    if message_content is None:
        return {"isValid": is_valid, "violatedSlot": violated_slot}
    return {
        "isValid": is_valid,
        "violatedSlot": violated_slot,
        "message": {"contentType": "PlainText", "content": message_content},
    }

def get_btcprice():
    """
    Retrieves the current price of bitcoin in dollars from the alternative.me Crypto API.
    """
    client = boto3.resource('dynamodb')
    table = client.Table('crypto_pricing')  
    resp = table.scan()
    return resp['Items'][len(resp['Items'])-1]['amount']
    #return 46897.01
    #bitcoin_api_url = "https://api.alternative.me/v2/ticker/bitcoin/?convert=USD"
    #response = requests.get(bitcoin_api_url)
    #response_json = response.json()
  ##  price_dollars = parse_float(response_json["data"]["1"]["quotes"]["USD"]["price"])
    #return response_json["data"]["1"]["quotes"]["USD"]["price"]
    
    # Get the current price of bitcoin in dolars and make the conversion from dollars to bitcoin.
def convert_to_dollar():
    btc_value = parse_float(dollars) / get_btcprice()
    btc_value = round(btc_value, 4)

### Dialog Actions Helper Functions ###
def get_slots(intent_request):
    """
    Fetch all the slots and their values from the current intent.
    """
    return intent_request["currentIntent"]["slots"]

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    """
    Defines an elicit slot type response.
    """
    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "ElicitSlot",
            "intentName": intent_name,
            "slots": slots,
            "slotToElicit": slot_to_elicit,
            "message": message,
        },
    }
def delegate(session_attributes, slots):
    """
    Defines a delegate slot type response.
    """
    return {
        "sessionAttributes": session_attributes,
        "dialogAction": {"type": "Delegate", "slots": slots},
    }
def close(session_attributes, fulfillment_state, message):
    """
    Defines a close slot type response.
    """
    response = {
        "sessionAttributes": session_attributes,
        "dialogAction": {
            "type": "Close",
            "fulfillmentState": fulfillment_state,
            "message": message,
        },
    }
    return response
### Intents Handlers ###
def recommend_portfolio(intent_request):
    """
    Performs dialog management and fulfillment for recommending a portfolio.
    """
    first_name = get_slots(intent_request)["firstName"]
    age = get_slots(intent_request)["age"]
    initial_investment = get_slots(intent_request)["initialAmount"]
    risk_level = get_slots(intent_request)["riskLevel"]
    source = intent_request["invocationSource"]
    validation_result = validate_data(age, initial_investment, intent_request)
    current_price = get_btcprice()
    print(current_price)
   
    if float(initial_investment) < float(current_price) :
        return close(intent_request["sessionAttributes"], 'Fulfilled',
            {
                "contentType": "PlainText",
                "content": "Your initial invesment is less than current BTC price",
            }
        )
    
    if source == "DialogCodeHook":
        #if type(risk_level) is not None and type(initial_investment) is not None:
         #   return elicit_slot({}, 'DCA_investment', get_slots(intent_request), 'riskLevel',  str(get_btcprice()) )
        # Perform basic validation on the supplied input slots.
        # Use the elicitSlot dialog action to re-prompt
        # for the first violation detected.
        slots = get_slots(intent_request)
        if not validation_result["isValid"]:
            return elicit_slot(
                intent_request["sessionAttributes"],
                intent_request["currentIntent"]["name"],
                slots,
                validation_result["violatedSlot"],
                validation_result["message"],
            )
        # Fetch current session attibutes
        output_session_attributes = intent_request["sessionAttributes"]
        return delegate(output_session_attributes, get_slots(intent_request))
    # Get the initial investment recommendation
    riskLevel = {"simple": "10% DCA purchases monthly",
    "steady": "20% DCA investments monthly",
    "low": "30% DCA investments monthly",
    "medium": "40% DCA investments weekly",
    "high": "50% DCA investments daily",
    "yolo": "exceed 50% DCA investments daily"}
    
    riskLevels = {"simple": .1,
    "steady": 0.2,
    "low": 0.3,
    "medium": 0.4,
    "high": 0.5}
    initial_recommendation = riskLevels[risk_level.lower()]
    
    currrentbtcprice = get_btcprice()
    #pricedifference = currrentbtcprice -  initial_investment
    # if float(currrentbtcprice) < float(initial_investment):
    #     return close(intent_request["sessionAttributes"], 'Fulfilled',
    #         {
    #             "contentType": "PlainText",
    #             "content": "Good job, please use this app when you're at a loss.",
    #         }
    #     )
    ininvest = float(initial_investment) / float(currrentbtcprice)
    rem = ininvest - 1
    
    print(riskLevels[risk_level.lower()])
    DCAAmt = rem * riskLevels[risk_level.lower()]
    return close(intent_request["sessionAttributes"], 'Fulfilled',
            {
                "contentType": "PlainText",
                "content": "You're loss is " + str(DCAAmt),
            }
        )    
    ### YOUR FINAL INVESTMENT RECOMMENDATION CODE ENDS HERE ###
    # Return a message with the initial recommendation based on the risk level.
    return close(
        intent_request["sessionAttributes"],
        "Fulfilled",
        {
            "contentType": "PlainText",
            "content": """{} thank you for your information;
            based on the risk level you defined, my recommendation is to choose an investment portfolio with {}
            """.format(
                first_name, initial_recommendation
            ),
        },
    )
def loss(initial_investment):
    currrentbtcprice = get_btcprice()
    #pricedifference = currrentbtcprice -  initial_investment
    if currrentbtcprice < initial_investment:
        return close({}, 'Fulfilled', "Good job, please use us when your at a loss.")
        
        
        ### YOUR DATA VALIDATION CODE STARTS HERE ###
def validate_data(age, investment_amount, intent_request):
    if age:
        age = int(age)
    if age is not None:
        if age < 0 or age > 65:
            return build_validation_result(
                False,
                "age",
                "You must be under 65 to use this service."
                "Please try again."
            )
    if investment_amount is not None:
        investment_amount = float(
            investment_amount
            )
        if investment_amount < 1000:
            return build_validation_result(
                False,
                "investmentAmount",
                "The amount to invest should be greater than $1000 USD."
                "Please provide a correct amount in USD to begin the DCA process.",
                )
    return build_validation_result(True, None, None)
    
def return_current_price(event):
    return get_btcprice()
    #name = event['bot']['name']
    #alias = event['bot']['alias']
    #user = event['userId']
    #client = boto3.client('lex-runtime')
    #response = client.put_session(
    #    botName=name,
    #    botAlias=alias,
    #    userId=user,
    #    dialogAction={
    #        'type': 'ElicitSlot',
    #        'intentName': 'DCA_Me',
    #        'message': str(current_price),
    #        'slotToElicit': 'riskLevel',
    #        'messageFormat': 'PlainText'
    #    }
    #)
    #print(response)
    
### Intents Dispatcher ###

def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """
    intent_name = intent_request["currentIntent"]["name"]
    # Dispatch to bot's intent handlers
    if intent_name == "DCA_Me":
        return recommend_portfolio(intent_request)
    raise Exception("Intent with name " + intent_name + " not supported")
### Main Handler ###
def lambda_handler(event, context):
    print(event)
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    return dispatch(event)