ALL_FORMATS = {
    'google': {
        'base_url': 'https://news.google.com/rss/search?q={0}',
        'time_url': 'https://news.google.com/rss/search?q={0}+after:{1}+before:{2}',
        'dt_format': '%Y-%m-%d',
        # 'columns': ['title', 'links', 'link', 'id', 'guidislink', 'published',
        #             'published_parsed', 'summary', 'title_detail.type',
        #             'title_detail.language', 'title_detail.base', 'title_detail.value',
        #             'summary_detail.type', 'summary_detail.language', 'summary_detail.base',
        #             'summary_detail.value', 'source.href', 'source.title']
    },
    'bing': {
        'base_url': 'https://www.bing.com/news/search?q={0}&format=rss',
        'columns': ['title_detail.value', 'title_detail.type',
                    'link', 'published_parsed', 'news_source'],
    },
}
