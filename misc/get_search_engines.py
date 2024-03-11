import pandas as pd
from bs4 import BeautifulSoup
import requests


if __name__ == '__main__':
    url = 'https://www.stanventures.com/blog/top-search-engines-list/'

    r = requests.get(url)
    soup = BeautifulSoup(r.text, 'html.parser')

    print(soup)

    # li = soup.find_all('span', {'class': 'ez-toc-section'})

    print('-' * 80)

    li = soup.find_all('span', {'class': 'ez-toc-section'})
    search_engines = []

    for e in li:
        print(e['id'])
        src = soup.find('span', {'id': e['id']}).find_parent('h3')
        children = src.findChildren("a", recursive=False)
        print('Printing children: ')
        for child in children:
            print(child)
            print(child['href'])
            search_engines.append(child['href'])

    df = pd.DataFrame()
    df['href'] = search_engines
    df.to_csv('search_engines.csv', index=False)
