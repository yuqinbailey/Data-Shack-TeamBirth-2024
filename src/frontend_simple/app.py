from flask import Flask, request, redirect, url_for, render_template, jsonify
from helper_code.hospital_data import HospitalData
import helper_code.data_loader as dl
# import helper_code.chatbot as chatbot
from termcolor import colored

app = Flask(__name__)

SELECT_STATE_PAGE = "state_selection.html"
SELECT_HOSPITAL_PAGE = "hospital_selection.html"
DASHBOARD_HOME_PAGE = "home.html"
CHATBOT_PAGE = "sections/chatbot.html"
PREFERENCES_PAGE = "sections/preferences.html"

@app.route('/')
def index():
    warnings = dl.get_warnings()
    if len(warnings) > 0:
        for warning in warnings:
            print(colored("WARNING: " + warning, 'yellow'))
    else:
        print(colored("No warnings found in the data loading process", 'green'))
    return render_template(SELECT_STATE_PAGE, states=dl.get_formatted_states_list())

#region HOSPITAL AND STATE SELECTION

@app.route('/<state>/')
def select_hospital(state):
    if dl.valid_state(state):
        hospitals = dl.get_hospitals_list(state)
        warnings = dl.get_warnings(state=state)
        if len(warnings) > 0:
            for warning in warnings:
                print(colored("WARNING: " + warning, 'yellow'))
        return render_template(SELECT_HOSPITAL_PAGE, state=state, hospitals=hospitals)
    
    print("Invalid state: ", state)
    return redirect(url_for('index'))

#endregion

#region DASHBOARD

@app.route('/<state>/<hospital>')
def dashboard_home(state, hospital):

    if not dl.valid_state(state):
        print("Invalid state: ", state)
        return redirect(url_for('index'))
    if not dl.valid_hospital(state, hospital):
        print("Invalid hospital: ", hospital)
        return redirect(url_for('select_hospital', state=state))
    
    hospital_data = HospitalData(state, hospital)
    errors = hospital_data.get_errors()
    if len(errors) > 0:
        for error in errors:
            print(colored("ERROR: " + error, 'red'))
    warnings = hospital_data.get_warnings()
    if len(warnings) > 0:
        for warning in warnings:
            print(colored("WARNING: " + warning, 'yellow'))
    if len(errors) == 0 and len(warnings) == 0:
        print(colored(f"Data was loaded correctly for {hospital}, {state}", 'green'))
        
    return render_template(DASHBOARD_HOME_PAGE, state=state, 
                            hospital=dl.get_formatted_hospital(state, hospital),
                            survey_trend=hospital_data.survey_trend_by_month(),
                            start_date=hospital_data.start_date(),
                            end_date=hospital_data.end_date(),
                            survey_total = hospital_data.total_survey_number(),
                            huddle_sumup = hospital_data.huddle_sumup(),
    )

#endregion

#region CHATBOT

@app.route('/<state>/<hospital>/chatbot/')
def chatbot_page(state, hospital):
    # Check if the state and hospital are valid
    if not dl.valid_state(state):
        print("Invalid state: ", state)
        return redirect(url_for('index'))
    if not dl.valid_hospital(state, hospital):
        print("Invalid hospital: ", hospital)
        return redirect(url_for('select_hospital', state=state))
    
    return render_template(CHATBOT_PAGE, state=state, 
                           hospital=dl.get_formatted_hospital(state, hospital))

@app.route('/<state>/<hospital>/chatbot/response', methods=['POST'])
def chatbot_response(state, hospital):
    if not dl.valid_state(state) or not dl.valid_hospital(state, hospital):
        return jsonify({"response": f"Invalid state or hospital: {state}, {hospital}"})

    return jsonify({"response": "The chatbot is not currently connected."})

    # data = request.json
    # user_message = data.get('message', '')

    # # Simulate a chatbot response (convert the message to uppercase)
    # response = chatbot.get_chatbot_response(user_message)
    # 
    # return jsonify({"response": response})

#endregion