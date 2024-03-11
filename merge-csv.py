import os
import pandas as pd
from datetime import datetime

dir = 'output'
errors = 0
success = 0
l = []
for file in os.listdir(dir):
    filepath = os.path.join(dir, file)
    try:
        df = pd.read_csv(filepath)
        l.append(df)
    except pd.errors.EmptyDataError:
        print('Empty data')
        errors += 1
    except UnicodeDecodeError:
        print('Unicode error')
        errors += 1

print('Total erros: %s' % errors)
print('Successes: %s' % len(l))

df = pd.concat(l)
# print(df['link'])
df.to_csv('%s_urls.csv' % datetime.now().strftime('%Y-%m-%d'), index=False)
