import dask.dataframe as dd


def get_texts(self, df, sleep=(0.1, 1)):
    if not 'link' in df.columns:
        raise Exception("url column not found")

    def text_from_url(url):
        # sleep for a random time from .1 to 1 second
        time.sleep(random.uniform(sleep[0], sleep[1]))
        try:
            article = newspaper.Article(url)
            article.download()
            return newspaper.fulltext(article.html)
        except:
            try:
                tokenizer = Tokenizer('english')
                sumy_parser = HtmlParser.from_url(url, tokenizer)
                output_string = ""
                for paragraph in sumy_parser.document.paragraphs:
                    # ._text is only available at sentence basis, so iterated here to preserve formatting
                    for sentence in paragraph.sentences:
                        output_string += sentence._text
                    output_string += "\n"
                return output_string
            except:
                logging.debug('Cannot connect to ' + url)
                return
    # use dask to speed up with parallel computing
    dask_df = dd.from_pandas(df, chunksize=10)
    texts = dask_df.loc[:, 'link'].apply(
        text_from_url, meta=('text', 'str')).compute()
    return texts
