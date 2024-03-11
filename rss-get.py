import argparse
import random
import time
import requests
import pandas as pd
import feedparser
import json
from datetime import datetime
from tqdm import tqdm
import os
import settings
import newspaper
from pprint import pprint
import logging


class RSSer():
    def __init__(self, source, format):
        logging.debug(format)
        self.source = source
        self.base_url = format['base_url']
        if 'time_url' in format:
            self.time_url = format['time_url']
        else:
            self.time_url = None
        # self.columns = format['columns']

    def search_keyword(self, keyword, date_start=None, date_end=None):
        # if the initial formatting is None
        if date_start is None:
            query = self.base_url.format(keyword)
        else:
            if self.time_url is not None:
                query = self.time_url.format(keyword, date_start, date_end)
            else:
                logging.debug('%s has no time based search' % self.source)
                query = None

        logging.debug('query: %s' % query)
        if query is not None:
            return requests.get(query, headers={'Accept': 'application/json'}), query
        else:
            return None, query

    def response_to_df(self, response):
        logging.debug('response: %s' % response.text)
        d = feedparser.parse(response.text)  # convert response to a dictionary
        # logging.debug(pprint(d))
        df = pd.json_normalize(d['entries'])
        # logging.debug(df.columns)
        # df = df.loc[:, self.columns]
        return df


def main(args):
    # initialize a saved list to track all files that have saved for the argument
    saved = []

    # iterate through all specified rss sources
    for source in args.sources:
        logging.debug('Searching %s' % source)
        rss = RSSer(source, format=settings.ALL_FORMATS[source])
        logging.debug(rss.base_url)
        logging.debug(args.keywords)

        for keyword in tqdm(args.keywords):
            start_date_str = None
            end_date_str = None

            if args.start_date is not None and 'dt_format' in settings.ALL_FORMATS[source]:
                start_date_str = datetime.strftime(
                    args.start_date, settings.ALL_FORMATS[source]['dt_format'])
            if args.end_date is not None and 'dt_format' in settings.ALL_FORMATS[source]:
                end_date_str = datetime.strftime(
                    args.end_date, settings.ALL_FORMATS[source]['dt_format'])

            r, query = rss.search_keyword(
                keyword, start_date_str, end_date_str)
            assert query is not None
            logging.debug(r)
            # logging.debug(r.text)
            if r is not None:
                df = rss.response_to_df(r)
                logging.debug(df)

                # texts = rss.get_texts(df)
                # logging.debug(texts)
                #
                # df['text'] = texts
                if args.outdir is not None:
                    filename = '%s_%s_%s.csv' % (datetime.now().strftime(
                        '%Y-%m-%d'), source, keyword)
                    filepath = os.path.join(args.outdir, filename)
                    df['query'] = query
                    df.to_csv(filepath, index=False)
                    saved.append(filepath)
    logging.info('-' * 80)
    for f in saved:
        logging.info('File saved: %s' % f)
    logging.info('Total files saved: %s' % len(saved))


def clean_args(args):
    # If either the end date or the start date is not None (i.e., if at least one date time is specified)
    if args.end_date is not None or args.start_date is not None:
        # If there is no end date, or if the end date is in the future
        if args.end_date is None or args.end_date > datetime.now():
            # Set the future end date to now
            args.end_date = datetime.now()

    srcs = list(settings.ALL_FORMATS.keys())
    # if some sources are specified
    if not args.sources is None:
        # filter the source for the set of all possible existing sources. This removes duplicate calls and also calls of sources that do not exist
        args.sources = list(set([v for v in args.sources if v in srcs]))

    # if no souces specified after the filter, or no sources originally specified, fill the sources with all current existing sources
    if args.sources is None or len(args.sources) <= 0:
        args.sources = srcs

    return args


def check_args(args):

    if not (args.keywords or args.input_file):
        raise ValueError('Either keywords or input file needs to be specified')
    if args.keywords and args.input_file:
        raise ValueError('Cannot input both keywords and input files')

    # if the end date is specified
    if not args.end_date is None:
        # and if the start date is not specified
        if args.start_date is None:
            raise ValueError('End date passed with no start date')
        # or if the start date specified is later than the end date
        elif args.start_date > args.end_date:
            raise ValueError('End date (%s) is before the start date (%s)' % (
                args.end_date, args.start_date))

    # if the output directory is specified and it does not exist
    if not args.outdir is None and not os.path.isdir(args.outdir):
        raise ValueError('Output directory (%s) is not a valid directory' % (
            os.path.abspath(args.outdir)))
    return args


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='DSPG pull from RSS sources')
    parser.add_argument('-k', '--keywords', nargs='+',
                        help='Keywords to parse')
    parser.add_argument('-i', '--input_file', type=str,
                        help='New line delimited keywords file')
    parser.add_argument('-s', '--sources', nargs='+',
                        help='Sources (%s) to parse from. If None, parses all possible sources' % (list(settings.ALL_FORMATS.keys())), required=False)
    parser.add_argument('-o', '--outdir', type=str)
    parser.add_argument('-sd', '--start_date', help='Start date of the search in Y-m-d format. If none and end date provided, or if provided date further than now, raises error',
                        type=lambda s: datetime.strptime(s, '%Y-%m-%d'))
    parser.add_argument('-ed', '--end_date', help='End date of the search in Y-m-d format. If none provided, uses the current time',
                        type=lambda s: datetime.strptime(s, '%Y-%m-%d'))
    parser.add_argument('-v', '--verbose',
                        action=argparse.BooleanOptionalAction)

    args = parser.parse_args()
    args = clean_args(args)
    check_args(args)

    if args.verbose:
        logging.basicConfig(
            format='%(levelname)s:%(message)s', level=logging.DEBUG)
    else:
        logging.basicConfig(
            format='%(levelname)s:%(message)s', level=logging.INFO)
    logging.debug(args)
    if args.input_file:
        args.keywords = ''.join(
            open(args.input_file, 'r').readlines()).split('\n')
    main(args)
