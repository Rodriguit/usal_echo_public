import luigi
from luigi.contrib.s3 import S3Target
from luigi.contrib.postgres import PostgresTarget 
from luigi import LocalTarget

from d01_data.ingestion_dcm import ingest_dcm
from d01_data.ingestion_xtdb import ingest_xtdb
from d02_intermediate.clean_dcm import get_meta_lite

# Note: extra comments in get_postgres_credentials and QueryInfo()
#       will be deleted when methodology is finalized


def get_postgres_credentials():
    '''
    Access postgres credentials from .json in user root directory
    Outputs host postgres server address, db user/password, db name
    '''
    io = dbReadWriteData()
    creds = io.credentials
    return creds["host"], creds["user"], creds["psswd"], creds["database"]
        '''
        filename = os.path.expanduser('~') + '/.psql_credentials.json'
	with open(filename) as f:
		data = json.load(f)
		return data["host"], data["user"], data["psswd"], data["database"]

class QueryInfo():
    def __init__(self, table, update_id):
        self.table = table
        self.update_id = update_id
    def output(self):
#        Returns a PostgresTarget representing the executed query
        return PostgresTarget(host=self.host, database=self.database, user=self.user \
                            password=self.psswd, table=self.table, update_id=self.update_id)
'''                                
   

class S3Bucket(luigi.ExternalTask): # ensure connection to S3 bucket

    def output(self):
	return luigi.S3Target('s3://cibercv/')
	# e.g. https://stackoverflow.com/questions/33332058/luigi-pipeline-beginning-in-s3


class IngestDCM(luigi.Task):
    '''
    Pipeline step of ingesting dicom metadata from .dcm files in database
    Populates postgres db schema raw
    '''
    def requires(self):
	return S3Bucket()

    def output(self):
        host, user, psswd, database = get_postgres_credentials()
        table = 'raw.metadata'
        update_id = 'ingest'
        return PostgresTarget(host, database, user, password, table, update_id)
	
    def run(self):
        ingest_dcm()


class CleanDCM(luigi.Task):
    '''
    Pipeline step of cleaning dicom metadata, i.e. filtering only necessary tags
    Populates postgres db schema clean
    '''
    def requires(self):
        return IngestDCM()
		
    def output(self):
        host, user, password, database = get_postgres_credentials()
        table = 'clean.meta_lite'
        update_id = 'clean'
        return PostgresTarget(host, database, user, password, table, update_id)
    	# https://luigi.readthedocs.io/en/stable/api/luigi.contrib.postgres.html
        # e.g. https://vsupalov.com/luigi-query-postgresql/


class IngestXTDB(luigi.Task):
    '''
    Pipeline step of ingesting Xcelera data from cibercv csv files
    Populates postgres db schema raw
    Assumes that all tables have been ingested if raw.A_measgraphic exists.
    This assumption is because ingest_xtdb() populates all tables at once
    '''
    def requires(self):
        return S3Bucket()

    def output(self): # output tables
        host, user, password, database = get_postgres_credentials()
        table = 'raw.A_measgraphic'
        update_id = 'ingest'
	return PostgresTarget(host, database, user, password, table, update_id)

    def run(self):
        return ingest_xtdb()


class CleanXTDB(luigi.Task):
    '''
    Pipeline step of cleaning Xcelera data
    Populates postgres db schema clean
    Assumes that all tables have been cleaned if clean.a_measgraphic exists.
    This assumption is because clean_tables() cleans all tables at once
    '''
    def requires (self):
	return IngestXTDB()

    def output(self): 
	host, user, password, database = get_postgres_credentials()
        table = 'clean.a_measgraphic'
        update_id = 'clean'
	return PostgresTarget(host, database, user, password, table, update_id)

    def run(self):
        return clean_tables()


