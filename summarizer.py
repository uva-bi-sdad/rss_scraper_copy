"""
@Steve, 2022-06-07
This file contains the implementation of getting summaries and original texts with sumy package
This may not be used later in the project, but kept here for reference as we proceed
"""

from sumy.parsers.html import HtmlParser
# from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

class Summerizer:
    def __init__(self, sentenceCount=10, language='english'):
        self.SENTENCE_COUNT = sentenceCount
        self.tokenizer = Tokenizer(language)
        self.stemmer = Stemmer(language)
        self.stopwords = get_stop_words(language)

    def get_text(self, url):
        parser = HtmlParser.from_url(url, self.tokenizer)
        output_string = ""
        for paragraph in parser.document.paragraphs:
            # ._text is only available at sentence basis, so iterated here to preserve formatting
            for sentence in paragraph.sentences:
                output_string += sentence._text
            output_string += "\n"
        return output_string

    def sum_html(self, url):
        parser = HtmlParser.from_url(url, self.tokenizer)
        summarizer = LsaSummarizer(self.stemmer)
        summarizer.stop_words = self.stopwords

        summary = summarizer(parser.document, self.SENTENCE_COUNT)
        summerized = ''
        for sentence in summary:
            summerized += (sentence._text + " ")
        return summerized