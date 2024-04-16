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


# TODO
# - anonymize questions with float dtype
# - add stemmed word counts? (not sure if it is useful)

# K-anonymity parameter
# If a value occurs less than MIN_K times, it is replaced with "Other"
# (Only applied to demographics questions)
MIN_K = 5

class HospitalData:

    def __init__(self, state_code, hospital_url):
        self.state = state_code
        self.hospital = hospital_url
        self.df = dl.get_hospital_df(state_code, hospital_url)
        self.config = dl.get_config(state_code)
        self.preprocess_data()
        self.feedback = None
        self.preprocessed_feedback = None
        self.stemmed_feedback = None
        self.word_counts = None
        self.stemmer = SnowballStemmer('english')
        self.sentiment_scores = None
    
    #region Survey Count, Start Date, End Date, Huddle Sumup
        
    def total_survey_number(self):
        """
        Returns the total number of surveys.
        """
        if self.df is None:
            return 0
        return len(self.df)

    def survey_trend_by_month(self):
        """
        Returns the number of surveys for each year-month.
        """
        start_date = self.df["Year-Month"].min()
        start_year = start_date[:4]
        start_month = start_date[5:]
        end_date = self.df["Year-Month"].max()
        end_year = end_date[:4]
        end_month = end_date[5:]

        year_month = {}

        for y in range(int(start_year), int(end_year)+1):
            for m in range(1, 13):
                if y == int(start_year) and m < int(start_month):
                    continue
                if y == int(end_year) and m > int(end_month):
                    break
                year_month[f"{y}-{m:02d}"] = len(self.df[self.df["Year-Month"] == f"{y}-{m:02d}"])

        return year_month
    
    def start_date(self):
        """
        Returns the earliest date for which there is a survey.
        """
        if self.df is None:
            return None
        start_date = self.df['StartDate'].min()
        return f"{start_date.month}/{start_date.day}/{start_date.year}"
    
    def end_date(self):
        """
        Returns the latest date for which there is a survey.
        """
        if self.df is None:
            return None
        end_date = self.df['StartDate'].max()
        return f"{end_date.month}/{end_date.day}/{end_date.year}"
    
    def huddle_sumup(self):
        """
        Returns the sumup of the huddle.
        """
        columns = dl.get_columns_of_type(self.state, "huddle")
        if columns is None:
            return None
        sumup = {}
        column = columns[0]
        sumup["Huddle Yes"] = len(self.df[self.df[column] == "Yes"])
        sumup["Huddle No"] = len(self.df[self.df[column] != "Yes"])
        return sumup

    #endregion

    #region Preprocessing (multiple choice and open feedback)

    def preprocess_data(self):
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
        
        self.anonymize_data()
        self.censor_feedback()
        
    def anonymize_data(self):
        """
        Anonymizes the data by replacing values that occur less than MIN_K times with "Other".
        """
        columns = dl.get_columns_of_type(self.state, "demographics")
        for column in columns:
            self._anonymize_question(column)

    def _anonymize_question(self, question_id): 
        """
        Anonymizes the answers to a question by replacing values that occur less than MIN_K times with "Other".
        """

        # if answer dtype is float, return
        if self.df[question_id].dtype == float:
            return

        max_iter = 10
        iter = 0
        while iter < max_iter:
            vc = self.df[question_id].value_counts()
            keys = vc.keys().tolist()

            # if nan is in keys, remove it
            if np.nan in keys:
                keys.remove(np.nan)
            if "Prefer not to answer" in keys:
                keys.remove("Prefer not to answer")

            # if there are less than 2 unique values, there is nothing i can merge
            if len(keys) < 2:
                break

            keys.sort(key=lambda x: vc[x], reverse=False)
            small_keys = []
            
            for i in range(len(keys)):
                if vc[keys[i]] < MIN_K:
                    small_keys.append(keys[i])

            if len(small_keys) > 0:
                self.df.loc[self.df[question_id].isin(small_keys), question_id] = "Other"
                if len(small_keys) == 1:
                    second_smallest = keys[1]
                    self.df.loc[self.df[question_id] == second_smallest, question_id] = "Other"
            else:
                break
            iter += 1
    
    def censor_feedback(self):
        """
        Censors the open feedback by replacing entities with underscores.
        """
        columns = dl.get_columns_of_type(self.state, "open_feedback")
        if columns is None:
            return
        for col in columns:
            # apply _censor_entities to each row
            self.df[col] = self.df[col].apply(self._censor_entities)

    def _censor_entities(self, text):
        """
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
    
    #endregion
        
    #region Open Feedback
    # all functions that return feedback return censored feedback

    def get_feedback(self):
        """
        Returns the open feedback concatenated in one dataframe with one column "Feedback".
        The feedback is already censored.
        """
        if self.feedback is not None:
            return self.feedback
        columns = dl.get_columns_of_type(self.state, "open_feedback")
        if columns is None:
            return None
        # concatenate columns into one
        self.feedback = pd.DataFrame()
        self.feedback["Feedback"] = pd.concat([self.df[col] for col in columns], 
                                            axis=0, ignore_index=True)
        self.feedback = self.feedback.dropna()
        self.feedback.reset_index(drop=True, inplace=True)
        return self.feedback.copy()
    
    def get_preprocessed_feedback(self):
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

    def get_stemmed_feedback(self):
        """
        Returns the stemmed and preprocessed feedback.
        The feedback is always censored.
        Returns a dataframe with one column "Feedback".
        """
        if self.stemmed_feedback is not None:
            return self.stemmed_feedback
        if self.preprocessed_feedback is None:
            self.get_preprocessed_feedback()
        self.stemmed_feedback = pd.DataFrame()
        self.stemmed_feedback["Feedback"] = self.preprocessed_feedback["Feedback"].apply(
            lambda x: ' '.join([self.stemmer.stem(word) for word in x.split()]))
        return self.stemmed_feedback.copy()

    def _preprocess_for_word_count(self, text):
        """
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
        """
        if self.word_counts is not None:
            return self.word_counts
        
        if self.preprocessed_feedback is None:
            self.get_preprocessed_feedback()
        if self.stemmed_feedback is None:
            self.get_stemmed_feedback()

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
        Returns the top n words in the feedback as a list without their respective counts.
        """
        word_counts = self.get_word_counts()
        return list(word_counts.keys())[:n]
    
    def get_word_count(self, word):
        """
        Returns the count of the word in the feedback.
        """
        word_counts = self.get_word_counts()
        return word_counts.get(word, 0)

    def get_feedbacks_with_word(self, word):
        """
        Returns the feedbacks that contain the stem of the word.
        Returns a dataframe with one column "Feedback".
        """
        if self.feedback is None:
            self.get_feedback()
        if self.stemmed_feedback is None:
            self.get_stemmed_feedback()
        w = self.stemmer.stem(word)
        return self.feedback[self.stemmed_feedback["Feedback"].str.find(w) >= 0].copy()

    def get_sentiment_scores(self):
        """
        Returns the sentiment scores for the feedbacks and the feedbacks themselves.
        Returns a pandas dataframe with four colums: "Feedback", "Positive", "Neutral", "Negative".
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
        Returns the feedback ordered by sentiment score.
        ordered_by: "Positive", "Neutral", "Negative". Default is "Positive".
        """
        if ordered_by not in ["Positive", "Neutral", "Negative"]:
            return None
        
        sentiment_scores = self.get_sentiment_scores()
        sentiment_scores = sentiment_scores.sort_values(by=ordered_by, ascending=False)
        return sentiment_scores["Feedback"].copy()


    #endregion

    #region Multiple Choice

    def get_multiple_choice(self, question_id):
        """
        Returns answers to the multiple choice question in a dictionary.
        """
        if question_id not in self.df.columns:
            return None
        question_type = self.config[self.config["ID"] == question_id]["Type"].values[0]
        if question_type == "open_feedack" or question_type == "info":
            return None

        unique_answers = self.df[question_id].unique()
        answers_list = mc.get_standard_list(unique_answers)
        if answers_list is None:
            answers_list = unique_answers
            # order alphabetically
            answers_list.sort()
            # if "Other" is in the list, move it to the end
            if "Other" in answers_list:
                answers_list.remove("Other")
                answers_list.append("Other")
        answers = {}
        for a in answers_list:
            answers[a] = len(self.df[self.df[question_id] == a])
        return answers


    #endregion

#empty space