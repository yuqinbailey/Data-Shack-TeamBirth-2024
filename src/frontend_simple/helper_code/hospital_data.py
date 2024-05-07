"""

This module provides classes and methods to handle data for a single hospital (or the option 
"All Hospitals", which is treated as a hospital).
It relies on the data_loader module to load the data and the configuration for the state 
and hospital.

Classes:
- HospitalData: represents the data for a single hospital and provides methods to access and
preprocess the data. It should be used whenever data for a single hospital is needed, as it
performs the necessary preprocessing and anonymization steps.
- Configuration: represents the configuration for a state and provides helper methods. It is
used internally by HospitalData to access the configuration and process data preprocessing 
and requests. It should not be used directly.
- AnswerList: represents a list of answers for a question. It is used internally by
Configuration to store the answer lists for each question. It should not be used directly.

Preprocessing steps:
- configuration preprocessing: 
    - remove columns marked as "info"
    - remove duplicate columns for categories which should only have one column (only the first
    column is kept, a warning is added if there are more than one column for a category)
    - remove duplicate question IDs (all duplicated are removed, a warning is added for each
    duplicate ID)
    - remove columns marked as "_TEXT" unless they are open feedback or one of the one column 
    categories (see ONE_COLUMN_CATEGORIES)
    - delete columns that do not appear in the configuration
    - check that all ONE_COLUMN_CATEGORIES are present and add an error if they are not
- date preprocessing:
    - convert the date to datetime format
    - add a column "Year-Month" with the date in the format "YYYY-MM" (this column is also added
    to the configuration with category "Year-Month" and ID "Year-Month")
- standardize answers:
    - replace "Prefers not to answer" with "Prefer not to answer"
    - replace "other" with "Other"
    - replace null values with "Prefer not to answer"
- anonymize data:
    - replace values that occur less than MIN_K times with "Other" for demographics questions
    - group numerical questions into ranges so that each range has at least MIN_K values
- censor feedback:
    - replace entities with underscores in open feedback

The following methods are provided by the HospitalData class:
- errors and warnings:
    - get_errors(): returns a list of errors concerning the data
    - get_warnings(): returns a list of warnings concerning the data
- general information and statistics:
    - total_survey_number(): returns the total number of surveys
    - survey_trend_by_month(): returns the number of surveys for each year-month pair as a 
    dictionary with the keys being the year-month ("YYYY-MM" format) and the values being the 
    number of surveys
    - start_date(): returns the earliest date for which there is a survey in the format "MM/DD/YYYY"
    - end_date(): returns the latest date for which there is a survey in the format "MM/DD/YYYY"
    - huddle_sumup(): returns the sumup of the huddle as a dictionary with the keys "Huddle Yes" 
    (the percentage of "Yes" answers) and "Huddle No" (the percentage of all other answers); 
    both percentages are expressed as a number between 0 and 100 with two decimal places
- open feedback:
    - get_feedback(): returns the open feedback concatenated in one dataframe with one column
    "Feedback"
    - get_word_counts(): returns a dictionary with all unique words in the feedback and their
    counts, ordered by count
    - get_top_words(n): returns the top n words in the feedback as a list without their respective
    counts
    - get_word_count(word): returns the count of the word in the feedback
    - get_feedbacks_with_word(word): returns the feedbacks that contain the word
    - get_sentiment_ordered_feedback(ordered_by): returns the feedback ordered by sentiment score
    (ordered_by can be "Positive", "Neutral" or "Negative", default is "Positive")
- multiple choice:
    - get_multiple_choice(question_id): returns answers to the multiple choice question in a 
    dictionary with the keys being the answers and the values being the counts

Notes about the open feedback:
- All functions that return feedback return censored feedback.
- All functions providing word counts use stemming: words that get stemmed to the same word are
counted together and searched for together. The first word that is encountered is chosen to
represent all other words that get stemmed to the same word.

The following methods are provided by the Configuration class:
- column categories:
    - get_columns_of_category(category): returns a list of column IDs of a given category
    - get_columns_of_categories(categories): returns a list of column IDs of given categories
    - get_category_of_column(column): returns the category of a given column ID
    - get_all_categories(): returns a list of all column categories in the configuration
- getters:
    - get_ids(): returns a list of all column IDs in the configuration
    - get_categories(): returns a list of all categories in the configuration
    - get_question_text(id): returns the text of the question with the given ID
    - get_answer_list(id): returns the answer list for the question with the given ID
- utils:
    - remove_columns(columns): removes the columns from the configuration
    - set_answer_list(id, answer_list): sets the answer list for the question with the given ID

"""

import pandas as pd
import numpy as np
import re, os
import spacy
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")
sentiment_model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"

import helper_code.data_loader as dl
import helper_code.multiplechoice_const as mc

# K-anonymity parameter
# If a value occurs less than MIN_K times, it is replaced with "Other"
# (Only applied to demographics questions)
MIN_K = 5
ONE_COLUMN_CATEGORIES = ["huddle", "age", "insurance", "race", "education", "date", "site_name"]



class HospitalData:
    """
    Represents the data for a single hospital (or the option "All Hospitals").
    Provides methods to access and preprocess the data.
    """


    def __init__(self, state_code, hospital_url):
        """
        state_code: the state code (string)
        hospital_url: the hospital url (string) (lowercase, no spaces, no punctuation)
        """
        self.state = state_code
        self.hospital = hospital_url
        self.df = dl.get_hospital_df(state_code, hospital_url)
        if self.df is None:
            raise ValueError("Invalid state or hospital: ", state_code, hospital_url)
        self.config = Configuration(state_code)    

        self.errors = []
        self.warnings = []

        if self.df is None or self.config is None:
            raise ValueError("Invalid state or hospital: ", state_code, hospital_url)

        self.preprocess()
        self.feedback = None
        self.preprocessed_feedback = None
        self.stemmed_feedback = None
        self.word_counts = None
        self.stemmer = SnowballStemmer('english')
        self.sentiment_scores = None
    

    #region Errors and Warnings

    def get_errors(self):
        """
        Returns a list of errors concerning the data.
        """
        return self.errors
    
    def get_warnings(self):
        """
        Returns a list of warnings concerning the data.
        """
        return self.warnings

    #endregion

    #region Preprocessing (multiple choice and open feedback)

    def preprocess(self):
        """
        Preprocesses the data:
        - configuration preprocessing (see preprocess_config() method)
        - converts the date to datetime format and adds a column "Year-Month" with the date in 
        the format "YYYY-MM"
        - replaces "Prefers not to answer" with "Prefer not to answer"
        - replaces "other" with "Other"
        - replaces null values with "Prefer not to answer"
        - anonymizes the demographics questions
        - censors the open feedback
        """
        self._preprocess_config()
        self._preprocess_date()
        
        # Standardize: replace "Prefers not to answer" with "Prefer not to answer"
        for c in self.df.columns:
            to_change_df = self.df[self.df[c] == "Prefers not to answer"]
            # if there are values to change
            if not to_change_df.empty:
                self.df.loc[self.df[c] == "Prefers not to answer", c] = "Prefer not to answer"
        # Standardize: replace "other" with "Other"
        for c in self.df.columns:
            to_change_df = self.df[self.df[c] == "other"]
            # if there are values to change
            if not to_change_df.empty:
                self.df.loc[self.df[c] == "other", c] = "Other"
        
        self._compute_answers_lists()
        self._anonymize_data()
        self._censor_feedback()

        # Standardize: convert to string and replace null values with "Prefer not to answer" 
        # to do after everything else as it could modify column data type
        for c in self.df.columns:
            if self.df[c].dtype == float or self.df[c].dtype == int:
                self.df[c] = self.df[c].astype(str)
            self.df[c] = self.df[c].fillna("Prefer not to answer")
    
    def _preprocess_config(self):
        """
        This should always be called before any other preprocessing steps as it modifies 
        the configuration and could prevent errors in further steps.
        Preprocessing steps based on the configuration:
        - remove columns marked as "info"
        - remove duplicate columns for categories which should only have one column
        (and add a warning if there are more than one column for a category)
        - remove duplicate question IDs
        - remove columns marked as "_TEXT" unless they are open feedback or one of the
        one column categories
        - check that df columns match the configuration and delete not-matching columns
        - check that all one column categories are present
        """

        # Remove columns marked as "info"
        info_columns = self.config.get_columns_of_category("info")
        if info_columns is not None and len(info_columns) > 0:
            self.df = self.df.drop(columns=info_columns)
            self.config.remove_columns(info_columns)
        
        # Remove duplicate columns for categories which should only have one column
        for category in ONE_COLUMN_CATEGORIES:
            columns = self.config.get_columns_of_category(category)
            if len(columns) > 1:
                self.warnings.append(f"{len(columns)} columns for category {category}. Only the first column will be kept.")
                self.df = self.df.drop(columns=columns[1:])
                self.config.remove_columns(columns[1:])
        
        # Remove questions with duplicate IDs
        ids = self.df.columns.tolist()
        duplicates = set([x for x in ids if ids.count(x) > 1])
        for d in duplicates:
            self.warnings.append(f"Duplicate question ID: {d}. The question will be deleted.")
            self.df = self.df.drop(columns=d)
            self.config.remove_columns([d])
        
        # Remove columns that end as "_TEXT"
        text_columns = [c for c in self.df.columns if c.endswith("_TEXT")]
        for c in text_columns:
            if self.config.get_category_of_column(c) not in ["open_feedback"] and self.config.get_category_of_column(c) not in ONE_COLUMN_CATEGORIES:
                self.df = self.df.drop(columns=c)
                self.config.remove_columns([c])
        
        # Check that df columns match the configuration
        df_columns = self.df.columns.tolist()
        config_columns = self.config.get_ids()
        for c in df_columns:
            if c not in config_columns:
                self.errors.append(f"An error occured with question {c}. The column will be deleted.")
                self.df = self.df.drop(columns=c)
        
        # Check that all one column categories are present
        categories = self.config.get_categories()
        for category in ONE_COLUMN_CATEGORIES:
            if category not in categories:
                self.errors.append(f"Missing question category: {category}.")

    def _preprocess_date(self):
        """
        Converts the date column to datetime format and adds a column "Year-Month" with the date
        in the format "YYYY-MM".
        The date column is necessary to get the start and end date, while the "Year-Month" column
        is used for monthly trends.
        """
        date_column = self.config.get_columns_of_category("date")[0]
        
        self.df.loc[:, date_column] = self.df[date_column].apply(pd.to_datetime)
        self.df["Year-Month"] = self.df[date_column].apply(self._date_to_year_month)
        
    def _date_to_year_month(self, date):
        """
        date: datetime object
        returns the date in the format "YYYY-MM"
        """
        return f"{date.year}-{date.month:02d}"

    def _anonymize_data(self):
        """
        Anonymizes the data by replacing values that occur less than MIN_K times with "Other".
        """
        columns = self.config.get_columns_of_categories(
            ["demographics", "age", "race", "insurance", "education"])
        for column in columns:
            if self.df[column].dtype == float or self.df[column].dtype == int:
                self._anonymize_numerical_question(column)
            elif self.df[column].dtype == object:
                self._anonymize_textual_question(column)
        # group answers for other questions as well if they are numerical
        for column in self.df.columns:
            if self.df[column].dtype == float or self.df[column].dtype == int:
                self._anonymize_numerical_question(column)

    def _anonymize_textual_question(self, question_id): 
        """
        question_id: the id of the question to anonymize (string)
        Anonymizes the answers to a question by replacing values that occur less than MIN_K 
        times with "Other".
        """

        # if answer dtype is float, return
        if self.df[question_id].dtype == float or self.df[question_id].dtype == int:
            return
        
        value_counts = self.df[question_id].value_counts()
        keys = value_counts.keys().tolist()

        for key in keys:
            if pd.isna(key):
                continue
            if key == "Prefer not to answer":
                continue
            if value_counts[key] < MIN_K:
                self.df.loc[self.df[question_id] == key, question_id] = "Other"
    
    def _censor_feedback(self):
        """
        Censors the open feedback by replacing entities with underscores.
        """
        columns = self.config.get_columns_of_category("open_feedback")
        if columns is None or len(columns) == 0:
            return
        for col in columns:
            # apply _censor_entities to each row
            self.df[col] = self.df[col].apply(self._censor_entities)

    def _censor_entities(self, text):
        """
        text: the text to censor (string)
        Returns text with the entities censored with underscores.
        """
        if pd.isna(text):
            return text
        doc = nlp(text)
        censored_text = ' '.join(['_' if token.ent_type_ else token.text for token in doc])
        # delete spaces before ".", ",", "?", "!", ":", ";", ")", "]", "}", "'"
        censored_text = re.sub(r'\s([.,?!:;)\]}\'"])', r'\1', censored_text)
        # delete spaces after "(", "[", "{", "'"
        censored_text = re.sub(r'([(\[{\'"]) ', r'\1', censored_text)
        return censored_text
    
    def _anonymize_numerical_question(self, column):
        """
        column: the id of the question to anonymize (string)
        column should be a numerical question.
        The function groups the answers to the question in ranges i-i+range and a last range
        last_value+, automatically selecting both the range size and the last value so that
        each bucket has at least MIN_K values.
        """
        # check that the column is numerical
        if self.df[column].dtype != float and self.df[column].dtype != int:
            return
        
        max_value = int(self.df[column].max()) + 1
        last_value = max_value + 1
        min_range = 1

        chosen_range = False
        while not chosen_range:
            chosen_range = True
            # check that every bucket has at least MIN_K values
            for i in range(0, max_value, min_range):
                remaining_values = len(self.df[self.df[column] >= i])
                if i > 0 and remaining_values < MIN_K*2 and remaining_values > MIN_K:
                    last_value = i
                    break

                count = len(
                    self.df[(self.df[column] >= i) & (self.df[column] < i + min_range)]
                    )
                if count < MIN_K and count != 0:
                    increase = 10 ** (len(str(min_range)) - 1)
                    min_range += increase
                    chosen_range = False
                    break
            if min_range >= max_value:
                break
        
        answer_list = []
        for i in range(0, last_value, min_range):
            answer_list.append(f"{i}-{i+min_range}")
        if last_value < max_value:
            answer_list.append(f"{last_value}+")
        answer_list.append("Prefer not to answer")
        self.config.set_answer_list(column, answer_list)
        
        self.df[column] = self.df[column].apply(
            lambda x: self._replace_numerical_value(x, min_range, last_value)
        )
    
    def _replace_numerical_value(self, value, min_range, last_value):
        if np.isnan(value):
            return "Prefer not to answer"
        if value >= last_value:
            return f"{last_value}+"
        lower = value - value % min_range
        upper = lower + min_range
        return f"{int(lower)}-{int(upper)}"
    
    def _compute_answers_lists(self):
        """
        For every question, checks if there is a standard list of answers and if there is it
        sets it in the configuration.
        """
        for column in self.df.columns:
            if self.config.get_category_of_column(column) in ONE_COLUMN_CATEGORIES:
                continue
            if self.config.get_category_of_column(column) == "open_feedback":
                continue
            if self.df[column].dtype == float or self.df[column].dtype == int:
                continue
            unique_values = self.df[column].unique()
            if len(unique_values) <= 1:
                continue
            answer_list = mc.get_standard_list(unique_values)
            if answer_list is not None and len(answer_list) > 0:
                self.config.set_answer_list(column, answer_list)


    #endregion

    #region General Info: Survey Count, Start Date, End Date, Huddle Sumup
        
    def total_survey_number(self):
        """
        Returns the total number of surveys.
        """
        return len(self.df)

    def survey_trend_by_month(self):
        """
        Returns the number of surveys for each year-month pair.
        Returns a dictionary with the keys being the year-month ("YYYY-MM" format) and the 
        values being the number of surveys for each month.
        Sets all months with no surveys to 0.
        """
        date_column = "Year-Month"
        start_date = self.df[date_column].min()
        start_year = start_date[:4]
        start_month = start_date[5:]
        end_date = self.df[date_column].max()
        end_year = end_date[:4]
        end_month = end_date[5:]

        year_month = {}

        for y in range(int(start_year), int(end_year)+1):
            for m in range(1, 13):
                if y == int(start_year) and m < int(start_month):
                    continue
                if y == int(end_year) and m > int(end_month):
                    break
                year_month[f"{y}-{m:02d}"] = len(self.df[self.df[date_column] == f"{y}-{m:02d}"])

        return year_month
    
    def start_date(self):
        """
        Returns the earliest date for which there is a survey in the format "MM/DD/YYYY".
        """
        if self.df is None:
            return None
        start_date = self.df[self.config.get_columns_of_category("date")[0]].min()
        return f"{start_date.month}/{start_date.day}/{start_date.year}"
    
    def end_date(self):
        """
        Returns the latest date for which there is a survey in the format "MM/DD/YYYY".
        """
        if self.df is None:
            return None
        end_date = self.df[self.config.get_columns_of_category("date")[0]].max()
        return f"{end_date.month}/{end_date.day}/{end_date.year}"
    
    def huddle_sumup(self):
        """
        Returns the sumup of the huddle as a dictionary with the keys "Huddle Yes" and "Huddle No".
        "Huddle Yes" is the percentage of "Yes" answers, 
        "Huddle No" is the percentage of all other answers.
        Both percentages are expressed as a number between 0 and 100 with two decimal places.
        """
        columns = self.config.get_columns_of_category("huddle")
        if columns is None or len(columns) == 0:
            return None
        sumup = {}
        column = columns[0]
        sumup["Huddle Yes"] = (len(self.df[self.df[column] == "Yes"]) / len(self.df) * 100)
        sumup["Huddle No"] = (len(self.df[self.df[column] != "Yes"]) / len(self.df) * 100)
        # return only two decimal places
        sumup["Huddle Yes"] = int(sumup["Huddle Yes"] * 100) / 100
        sumup["Huddle No"] = int(sumup["Huddle No"] * 100) / 100
        return sumup

    #endregion

    #region Open Feedback
    # all functions that return feedback return censored feedback

    def get_feedback(self):
        """
        Returns the open feedback concatenated in one dataframe with one column "Feedback".
        The feedback is already censored.
        All of the answers with type "open_feedback" are considered.
        """
        if self.feedback is not None:
            return self.feedback
        columns = self.config.get_columns_of_category("open_feedback")
        if columns is None or len(columns) == 0:
            return None
        # concatenate columns into one
        self.feedback = pd.DataFrame()
        self.feedback["Feedback"] = pd.concat([self.df[col] for col in columns], 
                                            axis=0, ignore_index=True)
        self.feedback = self.feedback.dropna()
        self.feedback.reset_index(drop=True, inplace=True)
        return self.feedback.copy()
    
    def _get_preprocessed_feedback(self):
        """
        Returns the preprocessed feedback: lowercase, no stopwords, no non-letter characters.
        The feedback is always censored.
        Returns a dataframe with one column "Feedback".
        """
        if self.preprocessed_feedback is not None:
            return self.preprocessed_feedback
        if self.feedback is None:
            self.get_feedback()
        self.preprocessed_feedback = pd.DataFrame()
        self.preprocessed_feedback["Feedback"] = self.feedback["Feedback"].apply(self._preprocess_for_word_count)
        return self.preprocessed_feedback.copy()

    def _get_stemmed_feedback(self):
        """
        Returns the stemmed and preprocessed feedback.
        The feedback is always censored.
        Returns a dataframe with one column "Feedback".
        """
        if self.stemmed_feedback is not None:
            return self.stemmed_feedback
        if self.preprocessed_feedback is None:
            self._get_preprocessed_feedback()
        self.stemmed_feedback = pd.DataFrame()
        self.stemmed_feedback["Feedback"] = self.preprocessed_feedback["Feedback"].apply(
            lambda x: ' '.join([self.stemmer.stem(word) for word in x.split()]))
        return self.stemmed_feedback.copy()

    def _preprocess_for_word_count(self, text):
        """
        text: the text to preprocess (string)
        Preprocesses the text for word count. Converts text to lowercase, removes stopwords 
        and non-letter characters.
        """
        text = text.lower()
        # remove everything that is not a letter
        text = re.sub(r'[^a-z]', ' ', text)
        # remove stopwords
        stop_words = set(stopwords.words('english'))
        text = ' '.join([word for word in text.split() if word not in stop_words])
        return text
    
    def get_word_counts(self):
        """
        Returns a dictionary will all unique words in the feedback (excluding stopwords) and
        their counts, ordered by count.
        The word count uses stemming: words that get stemmed to the same word are counted together.
        If two or more words get stemmed to the same word, the word that appears first in 
        the feedback is chosen as key and all others are counted towards the same key.
        """
        if self.word_counts is not None:
            return self.word_counts
        
        if self.preprocessed_feedback is None:
            self._get_preprocessed_feedback()
        if self.stemmed_feedback is None:
            self._get_stemmed_feedback()

        # get unique words
        words = set()
        for f in self.preprocessed_feedback["Feedback"]:
            words.update(f.split())
        # merge words that get stemmed to the same word
        for w1 in words.copy():
            for w2 in words.copy():
                if w1 in words and w2 in words and w1 != w2 and self.stemmer.stem(w1) == self.stemmer.stem(w2):
                    words.remove(w2)
        # count words in the stemmed feedback
        word_counts = {}
        for w in words:
            word_counts[w] = 0
            stemmed_w = self.stemmer.stem(w)
            for f in self.stemmed_feedback["Feedback"]:
                if stemmed_w in f:
                    word_counts[w] += 1

        # sort by count
        word_counts = dict(sorted(word_counts.items(), key=lambda item: item[1], reverse=True))
        self.word_counts = word_counts
        return word_counts
    
    def get_top_words(self, n):
        """
        n: the number of top words to return (int)
        Returns the top n words in the feedback as a list without their respective counts.
        """
        word_counts = self.get_word_counts()
        return list(word_counts.keys())[:n]
    
    def get_word_count(self, word):
        """
        word: the word to count (string)
        Returns the count of the word in the feedback.
        This count uses stemming: words that get stemmed to the same word are counted together.
        """
        word_counts = self.get_word_counts()
        return word_counts.get(word, 0)

    def get_feedbacks_with_word(self, word):
        """
        word: the word to search for (string)
        Returns the feedbacks that contain the stem of the word.
        Returns a dataframe with one column "Feedback".
        This function uses stemming: feedbacks that contain words that get stemmed to the same word
        as the given word are returned.
        """
        if self.feedback is None:
            self.get_feedback()
        if self.stemmed_feedback is None:
            self._get_stemmed_feedback()
        w = self.stemmer.stem(word)
        return self.feedback[self.stemmed_feedback["Feedback"].str.find(w) >= 0].copy()

    def _get_sentiment_scores(self):
        """
        Returns the sentiment scores for the feedbacks and the feedbacks themselves.
        Returns a dataframe with four colums: "Feedback", "Positive", "Neutral", "Negative".
        """
        if self.sentiment_scores is not None:
            return self.sentiment_scores.copy()
        
        from transformers import pipeline, AutoTokenizer, AutoConfig
        model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
        sentiment = pipeline("sentiment-analysis", model=model_name)
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        config = AutoConfig.from_pretrained(model_name)
        max_sequence_length = config.max_position_embeddings

        feedback_df = self.get_feedback()

        def _sentiment_score(feedback):
            # Tokenize and truncate/pad the input
            tokenized_input = tokenizer(feedback, max_length=max_sequence_length-1, truncation=True)
            # Convert the tokenized input to a string
            feedback = tokenizer.decode(tokenized_input['input_ids'], skip_special_tokens=True)
            
            result = sentiment(feedback, top_k=None)
            neg = [r for r in result if r["label"]=="negative"][0]["score"]
            neutral = [r for r in result if r["label"]=="neutral"][0]["score"]
            pos = [r for r in result if r["label"]=="positive"][0]["score"]
            return neg, neutral, pos
        
        sentiment_scores = feedback_df["Feedback"].apply(_sentiment_score).apply(pd.Series)
        sentiment_scores.columns = ["Negative", "Neutral", "Positive"]
        sentiment_scores.index = feedback_df.index
        sentiment_scores = pd.concat([feedback_df, sentiment_scores], axis=1)
        self.sentiment_scores = sentiment_scores
        return self.sentiment_scores.copy()

    def get_sentiment_ordered_feedback(self, ordered_by="Positive"):
        """
        ordered_by: "Positive", "Neutral" or "Negative". Default is "Positive".
        Returns the feedback ordered by sentiment score.
        """
        if ordered_by not in ["Positive", "Neutral", "Negative"]:
            return None
        
        sentiment_scores = self._get_sentiment_scores()
        sentiment_scores = sentiment_scores.sort_values(by=ordered_by, ascending=False)
        return sentiment_scores["Feedback"].copy()


    #endregion

    #region Multiple Choice

    def get_multiple_choice(self, question_id):
        """
        question_id: the ID of the multiple choice question (string)
        Returns answers to the multiple choice question in a dictionary.
        The keys are the answers and the values are the counts.
        If the question_id is not found in the data, returns None.
        If the question is of type "open_feedback" or "info", returns None.
        If the question has no standard list, returns the answers in alphabetical order with
        "Other" at the end if it is in the list.
        If the question has a standard list, returns the answers in the order of the standard list 
        and sets the count to 0 if the answer is not in the data.
        """
        if question_id not in self.df.columns:
            return None
        question_type = self.config.get_category_of_column(question_id)
        if question_type == "open_feedack" or question_type == "info":
            return None

        unique_answers = self.df[question_id].unique()
        answers_list = self.config.get_answer_list(question_id)
        # if there is no answer list or the unique answers are not part of the answer list
        if answers_list is None or len(answers_list) == 0 or not set(unique_answers).issubset(set(answers_list)):
            answers_list = self.df[question_id].unique().tolist()
            # order alphabetically
            answers_list.sort()
            # if "Other" is in the list, move it to the end
            if "Other" in answers_list:
                answers_list.remove("Other")
                answers_list.append("Other")
            if "Prefer not to answer" in answers_list:
                answers_list.remove("Prefer not to answer")
                answers_list.append("Prefer not to answer")
        answers = {}
        for a in answers_list:
            answers[a] = len(self.df[self.df[question_id] == a])
        return answers


    #endregion


class Configuration:
    """
    Represents the configuration for a state (configuration is identical for all hospitals
    in the same state).
    Provides methods to access the configuration.
    """

    def __init__(self, state_code):
        """
        state_code: the state code (string)
        """
        self.state = state_code
        self.config = dl.get_config(state_code)
        self.config = self.config._append(
            {"ID": "Year-Month", "Text": "Year-Month", "Category": "Year-Month"},
            ignore_index=True)
        self.config["Answer_List"] = [AnswerList([]) for _ in range(len(self.config))]
        # add new row
        if self.config is None:
            raise ValueError("Invalid state: ", state_code)
    
    #region Column Categories

    def get_columns_of_category(self, category):
        """
        category: column category (string)
        Returns a list of column IDs of a given category.
        """
        return self.config[self.config["Category"] == category]["ID"].tolist()

    def get_columns_of_categories(self, categories):
        """
        categories: list of column categories
        Returns a list of column IDs of given categories.
        """
        columns = []
        for category in categories:
            columns.extend(self.get_columns_of_category(category))
        return columns

    def get_category_of_column(self, column):
        """
        column: column ID (string)
        Returns the category of a given column ID.
        """
        return self.config[self.config["ID"] == column]["Category"].values[0]

    #endregion

    #region Getters

    def get_ids(self):
        """
        Returns a list of all column IDs in the configuration.
        """
        return self.config["ID"].tolist()
    
    def get_categories(self):
        """
        Returns a list of all categories in the configuration.
        """
        return self.config["Category"].unique().tolist()
    
    def get_question_text(self, id):
        """
        id: the ID of the question (string)
        Returns the text of the question with the given ID.
        """
        return self.config[self.config["ID"] == id]["Text"].values[0]
    
    def get_answer_list(self, id):
        """
        id: the ID of the question (string)
        Returns the answer list for the question with the given ID.
        """
        return self.config[self.config["ID"] == id]["Answer_List"].values[0].answers

    #endregion

    #region Utils

    def remove_columns(self, columns):
        """
        columns: list of column IDs to remove
        Removes the columns from the configuration.
        """
        self.config = self.config[~self.config["ID"].isin(columns)]
    
    def set_answer_list(self, id, answer_list):
        """
        id: the ID of the question (string)
        answer_list: the list of answers for the question
        Sets the answer list for the question with the given ID.
        """
        self.config.loc[self.config["ID"] == id, "Answer_List"] = AnswerList(answer_list)

    #endregion


class AnswerList:
    def __init__(self, answers):
        self.answers = answers

#empty space