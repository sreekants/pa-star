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

# NOTE:  Start by running your slurm script. As an output, Slurm dumps 
# a file You should have a file with the name 'perfrun_map_[JobID].log' 
# in your folder you run Slum from eg:perfrun_map_25200388.log is the 
# output of the job with the id 25200388. The file is infact a CSV output
# of the performance metrics of your run. This program generates an SQLite 
# database to simplify querying the database for insights. To use this program, 
# you do the following steps:
#   (1) Rename the slurm output to alltests.log and move it to the logs folder
#   (2) Run this script and expect its output as 'alltest.s3db' in the current folder
#   (3) Run the command 'sqlite3 alltest.s3db' to use the command line 
#       utility against the data

case = 'alltests'
dbfile  = f'{case}.s3db'

model = 'sample'
table = 'samples'

headers = create_db(dbfile, model, table)
pump_data(case, dbfile, headers)
#db  = TransactionalDatabase()
#db.open( 'world.db' )
