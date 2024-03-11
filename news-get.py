import argparse
import random
import time
import logging
import glob
import os
import validators
import queue
from threading import Thread
from threading import Lock
from tqdm import tqdm
from urllib.parse import urlparse

import dask.dataframe as dd
import pandas as pd

import newspaper

from sumy.parsers.html import HtmlParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

from selenium.webdriver import Chrome
from selenium.webdriver import ChromeOptions
# from selenium.webdriver.common.keys import Keys
# from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager


class NewsGetter:

    def __init__(self, output_dir, severity=1, **kwargs):
        self.language = kwargs.get('language', 'english')
        self.severity = severity
        self.outdir = output_dir
        self.tokenizer = Tokenizer(self.language)
        self.connection_error = []  # list recording the urls that cannot be scraped
        self.recent_sites = []  # this list tracks recently accessed sites to avoid over-ping one site
        if self.severity >= 2:
            ops = ChromeOptions()
            # ops.add_argument('headless')
            ops.add_argument('--window-size=1920,1080')  # to ensure no content is hidden if in smaller windows
            self.driver = Chrome(ChromeDriverManager().install(), options=ops)

    def text_from_url(self, url, sleep=(0, 0.1)):
        time.sleep(random.uniform(sleep[0], sleep[1]))
        output_string = ''
        try:
            article = newspaper.Article(url, language='en')
            article.download()
            output_string = newspaper.fulltext(article.html)
        except:
            try:
                sumy_parser = HtmlParser.from_url(url, self.tokenizer)
                for paragraph in sumy_parser.document.paragraphs:
                    for sentence in paragraph.senteces:
                        output_string += sentence._text
                    output_string += '\n'
            except:
                if self.severity < 2:  # if not trying selenium, raise a debug log
                    self.connection_error.append('Cannot connect to ' + url)
                    return
        if len(output_string) < 400:
            # 400 char is arbitrary threshold, identify "successful connection but rejected by robot test"
            # if connection failed in the previous two attempts, output_string = ''
            if self.severity < 2:
                self.connection_error.append('Cannot scrap text from ' + url)
                return  # if blocked by robot test, do not return anything
            else:
                try:
                    self.driver.get(url)
                except:  # when selenium also fails to connect
                    self.connection_error.append('Cannot connect to ' + url)
                    return
                html_source = self.driver.page_source
                output_string = newspaper.fulltext(html_source)
        return output_string

    def sum_from_url(self, url, sleep=(0, 0.1), **kwargs):
        time.sleep(random.uniform(sleep[0], sleep[1]))
        try:
            sumy_parser = HtmlParser.from_url(url, self.tokenizer)
        except:
            try:
                article = newspaper.Article(url, language='en')
                article.download()
                sumy_parser = HtmlParser.from_string(article.html, article.source_url, self.tokenizer)
            except:
                if self.severity < 2:
                    self.connection_error.append('Cannot connect to ' + url)
                    return
                else:
                    try:
                        self.driver.get(url)
                    except:
                        self.connection_error.append('Cannot connect to ' + url)
                        return
                    sumy_parser = HtmlParser.from_string(self.driver.page_source, url, self.tokenizer)
        summarizer = LsaSummarizer(Stemmer(self.language))
        summarizer.stop_words = get_stop_words(self.language)
        try:
            summary = summarizer(sumy_parser.document, kwargs.get('sentence_count', 10))
            summerized = ''
            for sentence in summary:
                summerized += (sentence._text + " ")
            return summerized
        except:
            # when the text scrapped is empty, print an error log
            self.connection_error.append('Cannot scrap text from ' + url)
            return

    def texts_from_csv(self, csv_dir, summarize=False, thread_count=16):

        class Worker(Thread):

            def __init__(self, url_queue: queue.Queue, getter: NewsGetter, lock: Lock, taskbar):
                Thread.__init__(self)
                self.queue = url_queue
                self.result = pd.Series(dtype=str)
                self.news_getter = getter
                self.task_bar = taskbar
                self.lock = lock

            def run(self):
                while True:
                    (index, url) = self.queue.get()
                    if url == '':
                        # print(threading.active_count())
                        break
                    site = urlparse(url).netloc
                    site = '.'.join(site.split('.')[-2:])  # ignore the sub-domain

                    # this chunk is to avoid requesting the same site too frequently
                    if site in self.news_getter.recent_sites:
                        time.sleep(3)
                        # print('Sleep triggered for site ' + site)
                    self.lock.acquire()  # the lock for the outerclass's list of visited sites
                    self.news_getter.recent_sites.append(site)
                    # the "cushion" for visited url is avg. 2 urls per thread
                    if len(self.news_getter.recent_sites) >= 2 * thread_count:
                        del self.news_getter.recent_sites[0]
                    self.lock.release()

                    if summarize:
                        text = self.news_getter.sum_from_url(url)
                    else:
                        text = self.news_getter.text_from_url(url)
                    self.result = pd.concat([self.result,
                                             pd.Series([text], index=[index])])
                    self.queue.task_done()
                    self.task_bar.update(1)

        urls = queue.Queue()

        csv_files = glob.glob(csv_dir + "/*.csv")
        if len(csv_files) == 0:
            raise Exception("No .csv files found in directory: " + csv_dir)
        for file in csv_files:
            self.connection_error = []
            self.recent_sites = []
            df = pd.read_csv(file)
            outdir = self.outdir + "\\" + file.split("\\")[-1]
            url_column = df.loc[:, 'link']  # this column name is universal across output files of feedparser
            print("Processing {0} links from {1}".format(len(url_column), file))
            queue_size = 0
            for i in url_column.index:
                urls.put((i, url_column[i]))
                queue_size += 1
            workers = []
            print("{} threads initiated".format(thread_count))
            lock = Lock()
            with tqdm(total=queue_size) as pbar:
                for i in range(thread_count):
                    urls.put(('', ''))  # this is the stopper indicating no more urls left
                    worker = Worker(urls, self, lock, pbar)
                    worker.start()
                    workers.append(worker)

                for worker in workers:
                    worker.join()  # join worker to wait until all finish

            for failed_message in self.connection_error:
                print(failed_message)

            texts = pd.Series(dtype=str)
            for worker in workers:
                pd.concat([texts, worker.result])
            df['text'] = texts
            df.to_csv(outdir, mode='w+')
            print('file saved to ' + outdir)


def main(args):
    getter = NewsGetter(severity=args.severity, output_dir=args.output_dir, laguage='english')
    if args.dir_to_csv is not None:
        getter.texts_from_csv(args.dir_to_csv, args.summarize, args.threads_count)
    if args.urls is not None:
        urls_output = pd.DataFrame(columns=['url', 'text'])
        for url in args.urls:
            if args.summarize:
                retrieved = [url, getter.sum_from_url(url)]
                urls_output = pd.concat([urls_output, pd.DataFrame([retrieved], columns=urls_output.columns)])
            else:
                retrieved = [url, getter.text_from_url(url)]
                urls_output = pd.concat([urls_output, pd.DataFrame([retrieved], columns=urls_output.columns)])
        urls_output.to_csv(args.output_dir + "\\" + 'url_output.csv')
        print('file saved to ' + args.output_dir + '\\' + 'url_output.csv')
    return


def check_args(args):
    if args.urls is None:
        if args.dir_to_csv is None:
            raise ValueError("must input at least one of valid url or .csv containing urls")
    else:
        for url in args.urls:
            if not validators.url(url):
                raise ValueError(url + 'is not a valid url')

    if args.dir_to_csv is not None:
        if not os.path.isdir(args.dir_to_csv):
            raise ValueError("dir_to_csv {} is not a valid directory".format(args.dir_to_csv))

    if args.severity is not None:
        if args.severity > 4 or args.severity < 1:
            raise ValueError("input severity is not valid")
    else:
        args.severity = 1

    if args.summarize is None:
        args.summarize = False

    if not args.output_dir is None and not os.path.isdir(args.output_dir):
        raise ValueError('Output directory (%s) is not a valid directory' % (
            os.path.abspath(args.outdir)))

    if args.threads_count is None:
        args.threads_count = 8

    return args


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Acquiring news articles from urls")
    parser.add_argument("-u", "--urls", nargs="+", help="urls to desired news text", required=False)
    parser.add_argument("-dir", "--dir_to_csv", help="directory to the csv files generated by rss_get.py",
                        required=False)
    parser.add_argument('-sum', "--summarize", help='whether to summarize text', action=argparse.BooleanOptionalAction)
    parser.add_argument("-s", "--severity",
                        help="level 1: get html directly; level 2: use selenium to bypass robot test; level 3: set "
                             "minimum wait time to bypass javascript; level 4 (under construction): use credentials",
                        nargs="?", const=1, type=int, required=False)
    parser.add_argument('-o', '--output_dir', type=str, required=True)
    parser.add_argument('-t', '--threads_count', nargs='?', const=8, type=int)
    args = parser.parse_args()
    args = check_args(args)
    main(args)
