#!/usr/bin/env python
import os
import numpy as np
import csv
import urllib.request
import re

# suppress tf and cuda messages
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

from transformers import AutoModelForSequenceClassification
from transformers import TFAutoModelForSequenceClassification
from transformers import AutoTokenizer

from scipy.special import softmax


# Tasks:
# emoji, emotion, hate, irony, offensive, sentiment
# stance/abortion, stance/atheism, stance/climate, stance/feminist, stance/hillary
TASK = 'sentiment'
MODEL = f"cardiffnlp/twitter-roberta-base-{TASK}"

SPACES = re.compile(r'\s+')


class RobertaSentimentAnalysis(object):

    """RobertaSentimentAnalysis object."""
    def __init__(self):
        self.tokenizer, self.labels, self.model = self.prepare()

    def prepare(self):
        tokenizer = AutoTokenizer.from_pretrained(MODEL)
        # download label mapping
        labels = []
        mapping_link = f"https://raw.githubusercontent.com/cardiffnlp/tweeteval/main/datasets/{TASK}/mapping.txt"
        with urllib.request.urlopen(mapping_link) as f:
            html = f.read().decode('utf-8').split("\n")
            csvreader = csv.reader(html, delimiter='\t')
        labels = [row[1] for row in csvreader if len(row) > 1]
        # PT
        model = AutoModelForSequenceClassification.from_pretrained(MODEL)
        model.save_pretrained(MODEL)
        tokenizer.save_pretrained(MODEL)
        return tokenizer, labels, model

    # Preprocess text (username and link placeholders)
    def preprocess(self, text):
        text = text.replace('\\r', ' ').replace('\\n', ' ')
        text = SPACES.sub(' ', text)

        new_text = []

        for t in text.split(" "):
            t = '@user' if t.startswith('@') and len(t) > 1 else t
            t = 'http' if t.startswith('http') else t
            new_text.append(t)
        return " ".join(new_text)

    def predict(self, text, show=False):
        text = self.preprocess(text)
        encoded_input = self.tokenizer(text, return_tensors='pt')
        output = self.model(**encoded_input)
        scores = output[0][0].detach().numpy()
        scores = softmax(scores)

        ranking = np.argsort(scores)
        ranking = ranking[::-1]
        
        result = {}
        for i in range(scores.shape[0]):
            l = self.labels[ranking[i]]
            s = scores[ranking[i]]
            result[l] = s

        if show:
            print(text)
            for i, (k, v) in enumerate(result.items()):
                print(f"{i+1}. {k} {v:.4f}")

        return result


if __name__ == '__main__':
    rob = RobertaSentimentAnalysis()
    result = rob.predict("@CashApp $TJbuddy1 lemme hold some of that BTC", show=True)
