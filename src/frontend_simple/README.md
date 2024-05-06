## File configuration and formatting

Author: Sara Merengo  
Email: sara.merengo@mail.polimi.it

---

This section contains information about how to format the files containing the data for the website to run correctly.

The website will read an .xlsx file named "state_code.xlsx" (e.g. "WA.xlsx", "MA.xlsx",...).
- For local deployment: all .xlsx files must be placed in a folder to be specified when running the website. Please do not place other files inside this folder as it might generate errors, especially if the files are named with state codes but are not formatted as the website expects.

Inside the file, every column should correspond to a question and every row should correspond to an answer, except for the first 3 rows.

The first 3 rows of the file should be structured as following:
1. **Row 1** should contain the **question IDs** (e.g. "StartDate", "Q1_1", "Q1_2",...).
    - Question IDs should be **unique**, that means that no two columns should have the same ID.
    - See Note for questions ending in "_TEXT"
    - One of the question IDs should be "site_name" and represent the name of the hospital. If this column is not present, only the option "All Hospitals" will be available.
2. **Row 2** should contain the **text of the questions** (e.g. "My clinical team asked me how involved in decision making I wanted to be."). This text is what will be showed in the graphs. For questions that will not be showed in graphs (e.g. StartDate, Response ID, Distribution Channel) this row is not important.
3. **Row 3** should contain the **category** of the question. The expected categories are the following, and should be matched exactly in the file:
    - **info**: all technical information about the surveys that will not be shown in the graphs (e.g. Response ID, Distribution Channel); if for any reason you want one question to not appear in the dashboard, you can set its category to info
    - **date**: a column containing the date of the survey; only one column should be labeled this way (e.g. one of StartDate or EndDate)
    - **site_name**: a column containing the name of the hospital the survey refers to; only one column should be labeled this way
    - **preference**: questions in the "Preferences" section of the survey (MADM questions)
    - **trust**: questions in the "Trust and decision making" section of the survey
    - **hospital_xp**: questions in the "TeamBirth experience" section of the survey; with the exception of:
        - **huddle**: question asking whether or not the patient participated in a huddle; only one question should be labeled this way
    - **demographics**: questions in the "Demographics" section of the survey; with the exception of:
        - **age**: question asking the age of the patient; only one question should be labeled this way
        - **race**: question asking the race or ethnicity of the patient; only one question should be labeled this way
        - **education**: question asking the level of education of the patient; only one question should be labeled this way
        - **insurance**: question asking the patient's type of health insurance; only one question should be labeled this way
    - **open_feedback**: all questions that require the patient to write their feedback; if any of the other sections contain open feedback questions, they should be labeled with "open_feedback" instead of their section label

**Note**

Questions whose ID ends in **"_TEXT"** will be deleted unless they are marked as open feedback or one of the unique categories (e.g. huddle, age, education,...). This is because these questions are a part of a different question, which could generate errors or unexpected behaviour. For questions whose answer is entirely in the _TEXT field (e.g. "How long was your labour?"), we recommend marking the main question as info so that it will be deleted and changing the ID of the text so that it does not end exactly in "_TEXT" (any unique ID will be okay).

E.g. Q10 is the question "How long was your labour?"; the answers are either "Prefer not to answer" or "Write the number of hours here:", while Q10_1_TEXT contains the numerical value for the answer or an empty cell for "Prefer not to answer". In this case, mark the category of Q10 as "info" and change the ID for Q10_1_TEXT to Q_10_1 (or any other ID that is not already taken). Then only the numerical value will be taken into consideration, and cells will be automatically filled in with "Prefer not to answer".

## Data elaboration

This section contains information about how the website preprocesses and elaborates the data.

### Error and warning handling

Some automatic mechanisms are in place to avoid formatting errors.
- If a state does not have a "site_name" column, only the option "All Hospitals" will be available
- If there are two or more questions with the **same ID**, all of them will be deleted
- If there is **more than one question** marked as one of the categories that should be **unique** (e.g. huddle, age, education,...), the first one will be kept while the others will be deleted

### General preprocessing

- Empty cells will be automatically filled with "Prefer not to answer"
- Answers that are numerical values will be automatically grouped into ranges which contain 
at least 5 values

### Data censoring
All answers catalogued under "open_feedback" will be automatically censored to remove names, places or numbers (e.g. days spent in the hospital). An underscore ( _ ) in the feedback indicates that a word has been removed. 
As this is an automatic system, it might still make mistakes. We recommend manually checking the feedback before sharing it with hospitals.

### Data anonymisation

All questions catalogued under "demographics", "age", "race", "education" and "insurance" will be anonymised. What this means in practice is that if any answer occurs less than 5 times, it will be grouped under "Other". 
The only exception to this is "Prefer not to answer", which will not be grouped with the other answers as it does not provide any further information.

### Huddle sumup
In the huddle sumup, "Huddle Yes" is the percentage of "Yes" answers while "Huddle No" is the percentage of all other answers.