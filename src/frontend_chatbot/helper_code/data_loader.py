"""
This file contains utility functions for loading, updating and managing the data and its 
configuration for each state.
"TODO" comments indicate where the code needs to be updated with proper data loading for deployment.
Currently this works for local deployment reading files from a specified directory.

This file contains functions to:
- load and update data
- return dataframes and configurations for a given state code and hospital
- perform validity checks on state code and hospital name - state code pairs
- get lists of states and hospitals
- format hospitals with names and urls
- separate the data from the configuration in the loaded files
- return warnings for the user if there are any issues with the data files

The "url" of a hospital is the lowercase name with no spaces and no non-alphanumeric characters.
E.g. "All Hospitals" -> "allhospitals", "Providence St. Peter" -> "providencestpeter".
The assumption is that this url is unique for each hospital in a state.

For each state, one file is expected containing the configuration in the first three header rows
and the data in the following rows. The configuration is loaded into a dataframe with columns
"ID", "Text", and "Category". The data is loaded into a dataframe with the first three header rows
dropped. 

Both data and configuration are managed as pandas dataframes.

"""

import pandas as pd
import numpy as np
import re
import os

# TODO:
# - Update with proper data loading

#region CONSTANTS

DATA_PATH = '/data/'

STATE_CODES = {"AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA", "HI", "ID", 
               "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", 
               "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", 
               "OR", "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", 
               "WI", "WY"}
CODE_STATE_DICT = {"AL": "ALABAMA", "AK": "ALASKA", "AZ": "ARIZONA", "AR": "ARKANSAS",
                   "CA": "CALIFORNIA", "CO": "COLORADO", "CT": "CONNECTICUT", 
                   "DE": "DELAWARE", "FL": "FLORIDA", "GA": "GEORGIA", "HI": "HAWAII",
                   "ID": "IDAHO", "IL": "ILLINOIS", "IN": "INDIANA", "IA": "IOWA",
                   "KS": "KANSAS", "KY": "KENTUCKY", "LA": "LOUISIANA", "ME": "MAINE",
                   "MD": "MARYLAND", "MA": "MASSACHUSETTS", "MI": "MICHIGAN",
                   "MN": "MINNESOTA", "MS": "MISSISSIPPI", "MO": "MISSOURI", 
                   "MT": "MONTANA", "NE": "NEBRASKA", "NV": "NEVADA", 
                   "NH": "NEW HAMPSHIRE", "NJ": "NEW JERSEY", "NM": "NEW MEXICO",
                   "NY": "NEW YORK", "NC": "NORTH CAROLINA", "ND": "NORTH DAKOTA",
                   "OH": "OHIO", "OK": "OKLAHOMA", "OR": "OREGON", "PA": "PENNSYLVANIA",
                   "RI": "RHODE ISLAND", "SC": "SOUTH CAROLINA", "SD": "SOUTH DAKOTA",
                   "TN": "TENNESSEE", "TX": "TEXAS", "UT": "UTAH", "VT": "VERMONT",
                   "VA": "VIRGINIA", "WA": "WASHINGTON", "WV": "WEST VIRGINIA",
                   "WI": "WISCONSIN", "WY": "WYOMING"}

#endregion

# Dictionaries to store the dataframes and configurations for each state
STATE_DF_DICT = {}
STATE_CONFIG_DICT = {}
VALID_STATES = set()
WARNINGS = []

#region WARNINGS

def get_warnings():
    """ 
    Returns a list of warnings for the user.
    """
    update_warnings()
    return WARNINGS

#TODO: Update this with proper data loading for deployment
def update_warnings():
    """
    Updates the warnings:
    - checks for unrecognised state codes in the data files
    - checks for invalid file extensions in the data files (only .xlsx files are allowed)
    """
    WARNINGS.clear()
    filenames = os.listdir(DATA_PATH)

    for filename in filenames:
        split_filename = filename.split(".")
        if len(split_filename) != 2:
            WARNINGS.append(f"Invalid file format: {filename}.")
        else:    
            name = filename.split(".")[0]
            extension = filename.split(".")[1]

            if name not in STATE_CODES:
                WARNINGS.append(f"Unrecognised state code in file: {filename}.")
            if extension != "xlsx":
                WARNINGS.append(f"Invalid file extension in file: {filename}.")

#endregion

#region DATA LOADING + UPDATING

#TODO: Update this with proper data loading for deployment
def _load_state_data(state_code):
    """
    state_code: string
    Loads the dataframe and configuration for a given state.
    Returns True if the data was loaded successfully, False otherwise.
    The file must be in the format "state_code.xlsx" and located in the DATA_PATH.
    """
    if state_code not in STATE_CODES:
        return False
    
    path = DATA_PATH + state_code + ".xlsx"

    if os.path.isfile(path):
        # load df
        data = pd.read_excel(path, header=[0, 1, 2])
        # drop header rows 1 and 2
        df = data.droplevel([1,2], axis=1)
        STATE_DF_DICT[state_code] = df.copy()

        # load config
        config = pd.DataFrame(data.columns.tolist(), columns=["ID", "Text", "Category"])
        STATE_CONFIG_DICT[state_code] = config.copy()
        return True
    else:
        return False

def get_state_df(state_code):
    """ 
    state_code: string
    Returns the dataframe for a given state code and loads it if it is not 
    already loaded
    """
    if state_code not in STATE_CODES:
        return None
    
    if state_code in STATE_DF_DICT:
        return STATE_DF_DICT[state_code]
    
    # if the load is successful, return the dataframe
    if _load_state_data(state_code):
        return STATE_DF_DICT[state_code]
    else:
        return None
    
def get_config(state_code):
    """ 
    state_code: string
    Returns the configuration for a given state code and loads it if it is not 
    already loaded
    """
    if state_code not in STATE_CODES:
        return None
    
    if state_code in STATE_CONFIG_DICT:
        return STATE_CONFIG_DICT[state_code]
    
    # if the load is successful, return the configuration
    if _load_state_data(state_code):
        return STATE_CONFIG_DICT[state_code]
    else:
        return None

#endregion

#region FILTER BY HOSPITAL

def get_hospital_df(state, hospital):
    """
    state: state code
    hospital: hospital url (lowercase name with no spaces and no non-alphanumeric characters)
    Returns the dataframe for a given state and hospital.
    """
    # check if the hospital exists for the given state
    if not valid_hospital(state, hospital):
        print("Invalid hospital: ", hospital, " for state: ", state)
        return None
    
    hospital = get_formatted_hospital(state, hospital)
    hospital = hospital['name']

    df = get_state_df(state)
    site_column = "site_name"
    
    if hospital == "All Hospitals":
        return df
    else:
        hospital_df = df[df[site_column] == hospital]
        #reset index
        hospital_df.reset_index(drop=True, inplace=True)
        return hospital_df

#endregion

#region VALIDITY CHECKS

#TODO: Update this with proper data loading for deployment
def valid_state(state):
    """ 
    state: state code
    returns True if there is a file corresponding to the state code, False otherwise.
    This function does not try to load the data, it only checks if the file exists, so errors
    might still occur when trying to load the data.
    """
    if state in VALID_STATES:
        return True
    
    # update valid states
    files = os.listdir(DATA_PATH)
    if f"{state}.xlsx" in files:
        VALID_STATES.add(state)
        return True

    return False

def valid_hospital(state, hospital):
    """
    state: state code
    hospital: hospital url (lowercase name with no spaces and no non-alphanumeric characters)
    returns True if the hospital is valid for the given state, False otherwise.
    """
    if not valid_state(state):
        return False
    
    for h in get_hospitals_list(state):
        if h['url'] == hospital:
            return True
    return False

#endregion

#region STATE AND HOSPITAL LISTS

def get_formatted_states_list():
    """ 
    Returns a list of all states with a non-empty df.
    Each state is represented by a dictionary with keys "code" and "name".
    (This is needed for proper formatting in the html template)
    """
    state_list = []
    for state in STATE_CODES:
        if valid_state(state):
            state_list.append({"code": state, "name": CODE_STATE_DICT[state]})
    return state_list

def get_hospitals_list(state):
    """ 
    state: state code
    Returns a list of all hospitals for a given state,
    including the option "All Hospitals".
    Each hospital is represented by a dictionary with keys "allcaps", "name", and "url".
    "allcaps" is the hospital name in all caps, "name" is the hospital name, and "url" is the
    hospital url (lowercase with no spaces and no non-alphanumeric characters).
    (This is needed for proper formatting in the html template)
    """
    if not valid_state(state):
        return []

    df = get_state_df(state)
    
    all = "All Hospitals"
    site_column = "site_name"
    if site_column not in df.columns:
        WARNINGS.append(f"Column 'site_name' not found in data for state: {state}.")
        return format_hospitals([all])
    hospitals = df[site_column].unique().tolist()
    hospitals.insert(0, all)
    # remove "site_name" and nan
    if "site_name" in hospitals:
        hospitals.remove("site_name")
    if np.nan in hospitals:
        hospitals.remove(np.nan)
    return format_hospitals(hospitals)

def format_hospitals(hospitals):
    """
    hospitals: list of hospital names
    Formats a list of hospitals into a list of dictionaries with keys "allcaps", 
    "name", and "url".
    "allcaps" is the hospital name in all caps, "name" is the hospital name, and "url" is the
    hospital url (lowercase with no spaces and no non-alphanumeric characters).
    (This is needed for proper formatting in the html template)
    """
    formatted_list = []
    for hospital in hospitals:
        allcaps_name = hospital.upper()
        url = re.sub(r'[^\w\s]', '', hospital).replace(' ', '').lower()
        formatted_hospital = {'allcaps': allcaps_name, 'name': hospital, 'url': url}
        formatted_list.append(formatted_hospital)
    return formatted_list

def get_formatted_hospital(state, hospital_url):
    """
    state: state code
    hospital_url: hospital url (lowercase name with no spaces and no non-alphanumeric characters)
    Returns the formatted hospital dictionary for a given state and hospital url.
    The state is necessary to check that the hospital is valid.
    """
    hospitals = get_hospitals_list(state)
    for h in hospitals:
        if h['url'] == hospital_url:
            return h
    return None

#endregion

# empty space