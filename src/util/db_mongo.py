""" Manage connection to MongoDB, and provides functions for relevent CRUD operation
"""
import copy
import bson
from pymongo import (MongoClient, errors)
from util.common_utils import (get_env, get_logger)

env = get_env()
logger = get_logger("util.db_mongo")
MONGO_DB_NAME = "CICDControllerDB"
MONGO_PIPELINES_TABLE = "pipelines_collection"
MONGO_JOBS_TABLE = "jobs_collection"
# pylint: disable=logging-fstring-interpolation


class MongoAdapter:
    """ Adapter class to provide standardize queries to mongo db
    """

    def __init__(self):
        """ Default Constructor
        """
        self.mongo_uri = env['MONGO_DB_URL'] if 'MONGO_DB_URL' in env else ""

    def get_controller_history(self) -> dict:
        """ Retrieve all pipeline history for the controller

        Returns:
            dict: dictionary contains all pipelines set up before, 
                identified by pipeline['_id'] value
        """
        try:
            mongo_client = MongoClient(self.mongo_uri)
            database = mongo_client[MONGO_DB_NAME]
            pipeline_collection = database[MONGO_PIPELINES_TABLE]
            histories = pipeline_collection.find({})
            results = {}
            for pipeline in histories:
                results[pipeline['_id']] = pipeline
            mongo_client.close()
            return results
        except errors.PyMongoError as e:
            logger.error(
                f"Error when retrieving pipeline history, exception is {e}")
            return None

    def _insert(self, data: dict, db_name: str, collection_name: str) -> str:
        """ Generic Helper method to insert the data

        Args:
            data (dict): data to be inserted, in key=value pairs
            db_name (str): database to be inserted into
            collection_name (str): collection(table) to be inserted into

        Returns:
            str: the inserted_id(converted to str) if successful
        """
        mongo_client = MongoClient(self.mongo_uri)
        database = mongo_client[db_name]
        collection = database[collection_name]
        result = collection.insert_one(data)
        mongo_client.close()
        return str(result.inserted_id)

    def _update(self, data: dict, db_name: str, collection_name: str) -> bool:
        """ Generic Helper method to update the data

        Args:
            data (dict): data to be inserted, in key=value pairs
            db_name (str): database to be updated
            collection_name (str): collection(table) to be updated

        Returns:
            bool: boolean indicator if successful
        """
        mongo_client = MongoClient(self.mongo_uri)
        database = mongo_client[db_name]
        collection = database[collection_name]
        updated_data = copy.deepcopy(data)
        # We need to pop the '_id' as it is immutable and can cause error
        updated_data.pop('_id')
        query_filter = {'_id': bson.objectid.ObjectId(
            data['_id'])}
        update_operation = {'$set': updated_data}
        result = collection.update_one(
            query_filter, update_operation)
        mongo_client.close()
        return result.acknowledged

    def _retrieve(self, doc_id: str, db_name: str, collection_name: str) -> dict:
        """ Retrieve the first found record based on given id

        Args:
            doc_id (str): id of target record
            db_name (str): database to be searched into
            collection_name (str): collection(table) to be searched into

        Returns:
            dict: target record in dict form
        """
        mongo_client = MongoClient(self.mongo_uri)
        database = mongo_client[db_name]
        collection = database[collection_name]
        result = collection.find_one(
            {"_id": bson.objectid.ObjectId(doc_id)})
        mongo_client.close()
        return result

    def _delete(self, doc_id: str, db_name: str, collection_name: str) -> bool:
        """ Delete the first found record based on given id

        Args:
            doc_id (str): id of target record
            db_name (str): targeted database
            collection_name (str): targeted collection(table) 

        Returns:
            bool: boolean indicator if successful
        """
        mongo_client = MongoClient(self.mongo_uri)
        database = mongo_client[db_name]
        collection = database[collection_name]
        result = collection.delete_one(
            {"_id": bson.objectid.ObjectId(doc_id)})
        mongo_client.close()
        return result.acknowledged

    def insert_pipeline(self, pipeline_history: dict, db_name: str = MONGO_DB_NAME,
                        collection_name: str = MONGO_PIPELINES_TABLE) -> str:
        """ Insert a new pipeline history record

        Args:
            pipeline_history (dict): dictionary of the history record in key=value pairs
            db_name (str, optional): database to be inserted into. Defaults to MONGO_DB_NAME.
            collection_name (str, optional): collection(table) to be inserted into. 
                Defaults to MONGO_PIPELINES_TABLE.

        Returns:
            str: the inserted_id(converted to str) if successful
        """
        try:
            return self._insert(pipeline_history, db_name, collection_name)
        except errors.PyMongoError as e:
            logger.warning(
                f"Error inserting new pipeline, exception is {e}")
            return None

    def update_pipeline(self, pipeline_history: dict, db_name: str = MONGO_DB_NAME,
                        collection_name: str = MONGO_PIPELINES_TABLE) -> bool:
        """ Update the pipeline history based on given dict

        Args:
            pipeline_history (dict): updated pipeline_history
            db_name (str, optional): database to be updated Defaults to MONGO_DB_NAME.
            collection_name (str, optional): collection(table) to be updated. 
                Defaults to MONGO_PIPELINES_TABLE.

        Returns:
            bool: if the update is successful or fail
        """
        try:
            return self._update(pipeline_history, db_name, collection_name)
        except errors.PyMongoError as e:
            logger.warning(f"Error updating the pipeline, exception is {e}")
            return False

    def get_pipeline(self, pipeline_id: str, db_name: str = MONGO_DB_NAME,
                     collection_name: str = MONGO_PIPELINES_TABLE) -> dict:
        """ Retrieve the pipeline history based on given id

        Args:
            pipeline_id (str): id of the given pipeline
            db_name (str, optional): target database. Defaults to MONGO_DB_NAME.
            collection_name (str, optional): target collection table. 
                Defaults to MONGO_PIPELINES_TABLE.
        Returns:
            dict: given pipeline in dict form
        """
        try:
            return self._retrieve(pipeline_id, db_name, collection_name)
        except errors.PyMongoError as e:
            logger.warning(f"Error retrieving the pipeline, exception is {e}")
            return {}

    def del_pipeline(self, pipeline_id: str, db_name: str = MONGO_DB_NAME,
                     collection_name: str = MONGO_PIPELINES_TABLE) -> dict:
        """ Delete the pipeline history based on given id

        Args:
            pipeline_id (str): id of the given pipeline
            db_name (str, optional): target database. Defaults to MONGO_DB_NAME.
            collection_name (str, optional): target collection table. 
                Defaults to MONGO_PIPELINES_TABLE.
        Returns:
            dict: given pipeline in dict form
        """
        try:
            return self._delete(pipeline_id, db_name, collection_name)
        except errors.PyMongoError as e:
            logger.warning(
                f"Error deleting the pipeline history, exception is {e}")
            return False

    def insert_job(self, job_log: dict, db_name: str = MONGO_DB_NAME,
                   collection_name: str = MONGO_JOBS_TABLE) -> str:
        """ Insert a new job_log record

        Args:
            job_log (dict): dictionary of the history record in key=value pairs
            db_name (str, optional): database to be inserted into. Defaults to MONGO_DB_NAME.
            collection_name (str, optional): collection(table) to be inserted into. 
                Defaults to MONGO_JOBS_TABLE.

        Returns:
            str: the inserted_id(converted to str) if successful
        """
        try:
            return self._insert(job_log, db_name, collection_name)
        except errors.PyMongoError as e:
            logger.warning(
                f"Error inserting new job log, exception is {e}")
            return None

    def update_job(self, job_log: dict, db_name: str = MONGO_DB_NAME,
                   collection_name: str = MONGO_JOBS_TABLE) -> bool:
        """ Update the job_log based on given dict

        Args:
            job_log (dict): updated job_log
            db_name (str, optional): database to be updated. Defaults to MONGO_DB_NAME.
            collection_name (str, optional): collection(table) to be updated. 
                Defaults to MONGO_JOBS_TABLE.
        Returns:
            bool: if the update is successful or fail
        """
        try:
            return self._update(job_log, db_name, collection_name)
        except errors.PyMongoError as e:
            logger.warning(f"Error updating the job log, exception is {e}")
            return False

    def get_job(self, doc_id: str, db_name: str = MONGO_DB_NAME,
                collection_name: str = MONGO_JOBS_TABLE) -> dict:
        """ retrieve the job based on given id

        Args:
            doc_id (str): id of target job
            db_name (str, optional): target database. Defaults to MONGO_DB_NAME.
            collection_name (str, optional): target collection. Defaults to MONGO_JOBS_TABLE.

        Returns:
            dict: target job in dict form
        """
        try:
            return self._retrieve(doc_id, db_name, collection_name)
        except errors.PyMongoError as e:
            logger.warning(f"Error retrieving the job, exception is {e}")
            return {}

    def del_job(self, job_id: str, db_name: str = MONGO_DB_NAME,
                collection_name: str = MONGO_JOBS_TABLE) -> dict:
        """ Delete the job log based on given id

        Args:
            job_id (str): id of target job
            db_name (str, optional): target database. Defaults to MONGO_DB_NAME.
            collection_name (str, optional): target collection. Defaults to MONGO_JOBS_TABLE.

        Returns:
            dict: target job in dict form
        """
        try:
            return self._delete(job_id, db_name, collection_name)
        except errors.PyMongoError as e:
            logger.warning(f"Error deleting the job log, exception is {e}")
            return False

    def get_pipeline_config(self, repo_name: str, repo_url: str,
                            branch: str, pipeline_name: str) -> dict:
        """Retrieve the _id and pipeline_config based on the given args.

        Returns:
            dict: the _id and pipeline_config fields.
        """
        try:
            query_filter = {
                'repo_name': repo_name,
                'repo_url': repo_url,
                'branch': branch,
                'pipeline_name': pipeline_name
            }
            mongo_client = MongoClient(self.mongo_uri)
            database = mongo_client[MONGO_DB_NAME]
            collection = database['repo_configs']
            pipeline_document = collection.find_one(query_filter, {'_id': 1, 'pipeline_config': 1})

            if pipeline_document:
                return pipeline_document
            logger.warning(
                f"No pipeline config found for '{pipeline_name}' "
                f"in '{repo_name}' on branch '{branch}'."
            )
            return {}
        except errors.PyMongoError as e:
            logger.warning(f"Error retrieving pipeline config: {str(e)}")
            return {}

    def update_pipeline_config(self, repo_name: str, repo_url: str,
                               branch: str, pipeline_name: str,pipeline_config: dict) -> bool:
        """Update the pipeline_config field in the repo_configs collection for a specific pipeline.

        Args:
            repo_name (str): The repository name.
            repo_url (str): The URL of the repository.
            branch (str): The branch of the repository.
            pipeline_name (str): The name of the pipeline to update.
            pipeline_config (dict): The new pipeline configuration to be updated.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            query_filter = {
                'repo_name': repo_name,
                'repo_url': repo_url,
                'branch': branch,
                'pipeline_name': pipeline_name
            }

            update_operation = {
                '$set': {
                    'pipeline_config': pipeline_config
                }
            }
            mongo_client = MongoClient(self.mongo_uri)
            database = mongo_client[MONGO_DB_NAME]
            collection = database['repo_configs']
            result = collection.update_one(query_filter, update_operation)
            mongo_client.close()
            return result.acknowledged
        except errors.PyMongoError as e:
            logger.warning(f"Error updating pipeline config: {str(e)}")
            return False
