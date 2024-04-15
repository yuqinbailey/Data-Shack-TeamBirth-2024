from flask import Flask, redirect, url_for, render_template
import pandas as pd
import numpy as np
import helper_code.hospital_data as data
from helper_code.hospital_data import HospitalData
import helper_code.data_loader as dl

app = Flask(__name__)

SELECT_STATE_PAGE = "state_selection.html"
SELECT_HOSPITAL_PAGE = "hospital_selection.html"
DASHBOARD_HOME_PAGE = "home.html"
CHATBOT_PAGE = "sections/chatbot.html"
PREFERENCES_PAGE = "sections/preferences.html"

@app.route('/')
def index():
    return render_template(SELECT_STATE_PAGE, states=dl.get_formatted_states_list())

#region HOSPITAL AND STATE SELECTION

@app.route('/<state>/')
def select_hospital(state):
    print("state: ", state)
    if dl.valid_state(state):
        hospitals = dl.get_hospitals_list(state)
        return render_template(SELECT_HOSPITAL_PAGE, state=state, hospitals=hospitals)
    print("Invalid state")
    return redirect(url_for('index'))

#endregion

#region DASHBOARD

@app.route('/<state>/<hospital>')
def dashboard_home(state, hospital):
    print("state: ", state)
    print("hospital: ", hospital)
    if not dl.valid_state(state):
        return redirect(url_for('index'))
    if not dl.valid_hospital(state, hospital):
        return redirect(url_for('select_hospital', state=state))
    hospital_data = HospitalData(state, hospital)
    return render_template(DASHBOARD_HOME_PAGE, state=state, 
                            hospital=dl.get_formatted_hospital(state, hospital),
                            survey_trend=hospital_data.survey_trend_by_month(),
                            start_date=hospital_data.start_date(),
                            end_date=hospital_data.end_date(),
                            survey_total = hospital_data.total_survey_number(),
                            huddle_sumup = hospital_data.huddle_sumup(),
    )

#endregion
