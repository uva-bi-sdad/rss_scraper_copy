import pandas as pd
import requests
import os
from urllib.parse import urlsplit, urlunsplit
import urllib.robotparser
import traceback
from tqdm import tqdm
from datetime import datetime

'''
Look for the robots.txt on each site, and see if the robots.txt contains links to the sitemap. Use the robots and the sitemap to search for potential rss feeds
'''


def parse_robot(robot_url):
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robot_url)
    rp.read()
    return rp.site_maps()


if __name__ == '__main__':
    df = pd.read_csv('search_engines.csv')
    # df = df[df['accessible'] == 1]
    robot_access = []
    time_accessed = []
    sitemaps = []
    for url in tqdm(list(df['href'])):
        robot_appended = False
        try:
            # https://stackoverflow.com/questions/35616434/how-can-i-get-the-base-of-a-url-in-python
            split_url = urlsplit(url)
            print('%s' % (split_url.netloc))
            # print(os.path.dirname(url))
            url = split_url.scheme + r'://' + split_url.netloc
            r = requests.get(url)
            if r.status_code == 200:
                robots = url + '/robots.txt'
                robot_r = requests.get(robots)
                print('\t\t[%s]: %s' % (robots, robot_r))
                if robot_r.status_code == 200:
                    sitemap = parse_robot(robots)
                    robot_access.append(robots)
                    sitemaps.append(sitemap)
                else:
                    robot_access.append('')
                    sitemaps.append('')
                robot_appended = True
                # sitemap = url + '/sitemap.xml'
                # print('\t\t[%s]: %s' % (sitemap, requests.get(sitemap)))

        except:
            print(traceback.format_exc())
            print('\tFAIL')
        finally:
            # keeping the row count the same across the files even during failure
            if not robot_appended:
                robot_access.append('')
                sitemaps.append('')
            time_accessed.append(datetime.now())
            print('-' * 80)
    df['found_robots'] = robot_access
    df['found_sitemaps'] = sitemaps
    df['time_accessed'] = time_accessed
    df['ignore'] = 0  # for manual checking in the future...
    df.to_csv('search_engine_robots.csv', index=False)
    print(df)
