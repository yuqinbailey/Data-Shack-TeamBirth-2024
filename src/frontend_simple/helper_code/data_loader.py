import pandas as pd
import numpy as np
import re
import os

# TODO:
# - Update with proper data loading

#region CONSTANTS

# DATA_PATH_REL = "../../../Data/"
# DATA_PATH = os.path.join(os.path.dirname(__file__), DATA_PATH_REL)
DATA_PATH = "/data/"

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

def valid_state(state):
    return state in STATE_CODES

#endregion

STATE_DF_DICT = {}
STATE_CONFIG_DICT = {}

#region DATA LOADING + UPDATING

#TODO: Update this with proper data loading
def load_state_df(state_code):
    """
    Loads the dataframe for a given state code and returns it
    """
    if state_code not in STATE_CODES:
        return None
    
    path = DATA_PATH + state_code + ".csv"
    if os.path.isfile(path):
        df = pd.read_csv(path, sep=";", header=[0, 1, 2])
        # drop header rows 1 and 2
        df = df.droplevel([1,2], axis=1)
        return preprocess(df)
    else:
        return None

def load_config(state_code):
    """
    Loads the configuration for a given state code and returns it
    """
    if state_code not in STATE_CODES:
        return None
    path = DATA_PATH + state_code + ".csv"
    if not os.path.isfile(path):
        return None
    
    df = pd.read_csv(path, sep=";", header=[0, 1, 2])
    config = pd.DataFrame(df.columns.tolist(), columns=["ID", "Text", "Type"])
    return config

def get_state_df(state_code):
    """ 
    Returns the dataframe for a given state code and loads it if it is not 
    already loaded
    """
    if state_code not in STATE_CODES:
        return None
    
    if state_code in STATE_DF_DICT:
        return STATE_DF_DICT[state_code]
    
    path = DATA_PATH + state_code + ".csv"
    if os.path.isfile(path):
        if state_code not in STATE_DF_DICT:
            STATE_DF_DICT[state_code] = load_state_df(state_code)
        return STATE_DF_DICT[state_code]
    else:
        return None
    
def get_config(state_code):
    """ 
    Returns the configuration for a given state code and loads it if it is not 
    already loaded
    """
    if state_code not in STATE_CODES:
        return None
    
    if state_code in STATE_CONFIG_DICT:
        return STATE_CONFIG_DICT[state_code]
    
    path = DATA_PATH + state_code + ".csv"
    if os.path.isfile(path):
        if state_code not in STATE_CONFIG_DICT:
            STATE_CONFIG_DICT[state_code] = load_config(state_code)
        return STATE_CONFIG_DICT[state_code]
    else:
        return None 

def update_state_df(state_code):
    """
    Updates the dataframe for a given state code and loads it if it is not
    already loaded
    """
    if state_code not in STATE_CODES:
        return None
    
    STATE_DF_DICT[state_code] = load_state_df(state_code)
    return STATE_DF_DICT[state_code]
    
def update_config(state_code):
    """
    Updates the configuration for a given state code and loads it if it is not
    already loaded
    """
    if state_code not in STATE_CODES:
        return None
    
    STATE_CONFIG_DICT[state_code] = load_config(state_code)
    return STATE_CONFIG_DICT[state_code]
    
def update_all_state_dfs():
    """
    Updates the dataframes for all states and loads them if they are not
    already loaded
    """
    for state_code in STATE_CODES:
        update_state_df(state_code)

def update_all_configs():
    """
    Updates the configurations for all states and loads them if they are not
    already loaded
    """
    for state_code in STATE_CODES:
        update_config(state_code)

#endregion

#region FILTER BY HOSPITAL

def get_hospital_df(state, hospital):
    """
    Returns the dataframe for a given state and hospital.
    Takes into input the state code and the url form of the hospital name (lowercase 
    without spaces and special characters).
    """
    if not valid_hospital(state, hospital):
        print("Invalid hospital")
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

#region DATA FORMATTING AND PREPROCESSING

def preprocess(df):
    """ Preprocesses the dataframe """
    df = df.copy()
    add_year_month_column(df)
    return df

def date_to_year_month(date):
    """
    Convert date to YYYY-MM format
    """
    y = str(date.year)
    m = str(date.month)
    if (date.month < 10):
        m = "0" + m
    return f"{y}-{m}"

def add_year_month_column(df):
    """
    Add a "Year-Month" column to the dataframe with the start date in the format
    "YYYY-MM"
    """
    start_date_column = "StartDate"
    
    df[start_date_column] = df[start_date_column].apply(pd.to_datetime)
    df["Year-Month"] = df[start_date_column].apply(date_to_year_month)

#endregion

#region UTILS

def get_columns_of_type(state, type):
    """
    Returns a list of columns of a given type for a given state
    """
    config = get_config(state)
    if config is None:
        return None
    return config[config["Type"] == type]["ID"].tolist()

def get_type_of_column(state, column):
    """
    Returns the type of a given column for a given state
    """
    config = get_config(state)
    if config is None:
        return None
    return config[config["ID"] == column]["Type"].values[0]

def get_column_types(state):
    """
    Returns a dictionary of column types for a given state
    """
    config = get_config(state)
    if config is None:
        return None
    return config["Type"].unique().tolist()

#endregion

#region VALIDITY CHECKS

def valid_df_state(state):
    """ 
    Returns True if the state has a valid dataframe, False otherwise.
    Takes into input the state code.
    """
    return get_state_df(state) is not None

def valid_hospital(state, hospital):
    """ 
    Returns True if the hospital is valid for the given state, False otherwise.
    Validity check based on state code and hospital url (lowecase name with
    no spaces and no special characters).
    """
    if not valid_df_state(state):
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
    Each state is represented by a dictionary with keys "code" and "name" 
    """
    state_list = []
    for state in STATE_CODES:
        if valid_df_state(state):
            state_list.append({"code": state, "name": CODE_STATE_DICT[state]})
    return state_list

def get_hospitals_list(state):
    """ 
    Returns a list of all hospitals for a given state,
    including the option "All Hospitals".
    Each hospital is represented by a dictionary with keys "allcaps", "name", and "url" 
    """
    if not valid_df_state(state):
        return []

    df = get_state_df(state)
    
    all = "All Hospitals"
    site_column = "site_name"
    if site_column is None:
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
    Formats a list of hospitals into a list of dictionaries with keys "allcaps", 
    "name", and "url"
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