from ActiveRecord import ActiveRecord
from TransactionalDatabase import TransactionalDatabase
from map import header
import os, csv, sys


def pump_data(case, dbfile, headers):
    db  = TransactionalDatabase()
    db.open(dbfile)

    count   = 0
    # Read the data from world.csv and print the rows one by one
    with open(f'logs/{case}.log', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            count   = count+1
            db.addkv('samples', list(row.keys()), list(row.values()))
    db.close()

def create_db(dbfile, model, table):
    if os.path.isfile(dbfile):
        os.remove(dbfile)


    headers = []
    for h in header().split(','):
        type    = 'float'
        desc    = 'REAL'

        if h in ['category', 'file']:
            type    = 'string'
            desc    = 'VARCHAR(64)'
        elif h.find('found') != -1:
            type    = 'bool'
            desc    = 'BOOLEAN'


        headers.append((h, type, desc))

    strsql  = []
    strsql.append(f'CREATE TABLE [{table}]( [id] INTEGER NULL PRIMARY KEY')
    for h in headers:
        strsql.append( f',[{h[0]}] {h[2]} NULL')

    strsql.append(')')

    print()

    rec	= ActiveRecord.create(model, dbfile, table)
    rec.execute_sql( '\n'.join(strsql) )
    return headers


case = 'alltests'
dbfile  = f'{case}.s3db'

model = 'sample'
table = 'samples'

headers = create_db(dbfile, model, table)
pump_data(case, dbfile, headers)
#db  = TransactionalDatabase()
#db.open( 'world.db' )
