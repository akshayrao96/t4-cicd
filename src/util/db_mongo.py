""" Manage connection to MongoDB, and provides functions for relevent CRUD operation
"""
import copy
from datetime import datetime, timezone
import bson
from pymongo import (MongoClient, errors)
from util.common_utils import (get_env, get_logger)

env = get_env()
logger = get_logger("util.db_mongo")
MONGO_DB_NAME = "CICDControllerDB"
MONGO_PIPELINES_TABLE = "repo_configs"
MONGO_JOBS_TABLE = "jobs_history"
MONGO_REPOS_TABLE = "sessions"
# pylint: disable=logging-fstring-interpolation


class MongoAdapter:
    """ Adapter class to provide standardize queries to mongo db
    """

    def __init__(self):
        """ Default Constructor
        """

        # store the mongoDB url in bash rc file. Using atlas for this.
        # self.mongo_uri = os.getenv('MONGO_DB_URL')
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

    def _retrieve(
            self,
            doc_id: str,
            db_name: str,
            collection_name: str) -> dict:
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

    def insert_pipeline(
            self,
            pipeline_history: dict,
            db_name: str = MONGO_DB_NAME,
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

    def update_pipeline(
            self,
            pipeline_history: dict,
            db_name: str = MONGO_DB_NAME,
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

    def insert_job(self, repo_id: str, pipeline_config: dict, stages_to_run: list = None) -> str:
        """
        Inserts a new job with initialized stages into the jobs table.

        Args:
            repo_id (str): Repository ID for the job.
            pipeline_config (dict): Configuration of pipeline stages.
            stages_to_run (list, optional): Stages to initialize; defaults to all.

        Returns:
            str: ID of the inserted job document.
        """
        repo = self._retrieve(repo_id, MONGO_DB_NAME, MONGO_PIPELINES_TABLE)
        all_stages = list(pipeline_config.get("stages", {}).keys())
        stages_to_initialize = stages_to_run if stages_to_run else all_stages

        stage_logs = []
        for stage_name in stages_to_initialize:
            if stage_name in all_stages:
                stage_log = {
                    "stage_name": stage_name,
                    "stage_status": "pending",
                    "jobs": []
                }
                stage_logs.append(stage_log)
        pending_stages = [stage["stage_name"] for stage in stage_logs]
        logger.info(f"Initialized stages: {', '.join(pending_stages)}")

        job_data = {
            "pipeline_number": bson.ObjectId(),
            "run_number": len(repo.get("job_run_history", [])) + 1,
            "git_commit_hash": repo.get("last_commit_hash"),
            "pipeline_config_used": pipeline_config,
            "success": None,
            "logs": stage_logs
        }
        return self._insert(job_data, MONGO_DB_NAME, MONGO_JOBS_TABLE)

    def update_job_logs(self, jobs_id: str, stage_name: str, 
                        stage_status: str, jobs_log: dict) -> bool:
        """
        Updates the status and the jobs log for a specific stage.

        Args:
            jobs_id (str): ID of the job to update.
            stage_name (str): Name of the stage to update.
            stage_status (str): New status of the stage.
            jobs_log (dict): Log information for the stage.

        Returns:
            bool: True if the update succeeded, False otherwise.
        """
        try:
            jobs = self._retrieve(jobs_id, MONGO_DB_NAME, MONGO_JOBS_TABLE)
            if not jobs:
                logger.warning(f"Jobs with ID {jobs_id} not found.")
                return False
            stage_log = next((stage for stage in jobs["logs"] 
                              if stage["stage_name"] == stage_name), None)
            if not stage_log:
                logger.warning(f"Stage '{stage_name}' not initialized. Cannot update job log.")
                return False
            stage_log["stage_status"] = stage_status
            stage_log["jobs"] = jobs_log
            return self._update(jobs, MONGO_DB_NAME, MONGO_JOBS_TABLE)
        except Exception as e:
            logger.warning(f"Error updating job log for jobs_id {jobs_id}: {e}")
            return False

    def create_job_log(self, job_name: str, job_status: str, allow_failure: bool = False,
                    logs: list = None, error_output: str = None) -> dict:
        """
        Creates a job log entry.

        Args:
            job_name (str): Name of the job.
            job_status (str): Current status of the job (e.g., "started" / "completed").
            allow_failure (bool, optional): the job is allowed to fail or not.
            logs (list, optional): List of log.
            error_output (str, optional): Error output.

        Returns:
            dict: A dictionary representing the job log entry.
        """
        job_log = {
            "job_name": job_name,
            "job_status": job_status,
            "allow_failure": allow_failure,
            "logs": logs or [],
            "error_output": error_output
        }
        if job_status == "started":
            job_log["start_time"] = datetime.now(timezone.utc)
        elif job_status == "completed":
            job_log["completion_time"] = datetime.now(timezone.utc)
        return job_log

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

    def insert_repo(self, repo_data: dict, db_name: str = MONGO_DB_NAME,
                    collection_name: str = MONGO_REPOS_TABLE) -> str:
        """ Insert a new repository record into repos_collection

        Args:
            repo_data (dict): dictionary of the repository data
            db_name (str, optional): database to be inserted into. Defaults to MONGO_DB_NAME.
            collection_name (str, optional): collection(table) to be inserted into. Defaults to MONGO_REPOS_TABLE.

        Returns:
            str: the inserted_id (converted to str) if successful
        """
        try:
            return self._insert(repo_data, db_name, collection_name)
        except errors.PyMongoError as e:
            logger.warning(f"Error inserting new repository, exception is {e}")
            return None

    def get_last_set_repo(self, db_name: str = MONGO_DB_NAME,
                          collection_name: str = MONGO_REPOS_TABLE) -> dict:
        """ Retrieve the last set repository from the user

        Args:
            db_name (str, optional): target database. Defaults to MONGO_DB_NAME.
            collection_name (str, optional): collection(table) to retrieve from. Defaults to MONGO_REPOS_TABLE.

        Returns:
            dict: last repository entry in dict form, or None if not found
        """
        try:
            mongo_client = MongoClient(self.mongo_uri)
            database = mongo_client[db_name]
            collection = database[collection_name]
            result = collection.find_one(sort=[("time", -1)])
            mongo_client.close()
            return result
        except errors.PyMongoError as e:
            logger.warning(
                f"Error retrieving last set repository, exception is {e}")
            return None

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
                'pipelines.pipeline_name': pipeline_name
            }
            projection = {
                "_id": 1,
                "pipelines": {
                    "$elemMatch": {"pipeline_name": pipeline_name}
                }
            }
            mongo_client = MongoClient(self.mongo_uri)
            database = mongo_client[MONGO_DB_NAME]
            collection = database[MONGO_PIPELINES_TABLE]
            pipeline_document = collection.find_one(query_filter, projection)
            mongo_client.close()
            if pipeline_document and "pipelines" in pipeline_document:
                # Flatten the result to directly access pipeline_config
                pipeline_document["pipeline_config"] = pipeline_document["pipelines"][0].get("pipeline_config")
                del pipeline_document["pipelines"]
                return pipeline_document
            logger.warning(
                f"No pipeline config found for '{pipeline_name}' "
                f"in '{repo_name}' on branch '{branch}'."
            )
            return {}
        except errors.PyMongoError as e:
            logger.warning(f"Error retrieving pipeline config: {str(e)}")
            return {}

    def update_pipeline_config(
            self,
            repo_name: str,
            repo_url: str,
            branch: str,
            pipeline_name: str,
            pipeline_config: dict) -> bool:
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
                'pipelines.pipeline_name': pipeline_name
            }

            update_operation = {
                '$set': {
                    'pipelines.$.pipeline_config': pipeline_config
                }
            }
            mongo_client = MongoClient(self.mongo_uri)
            database = mongo_client[MONGO_DB_NAME]
            collection = database[MONGO_PIPELINES_TABLE]
            result = collection.update_one(query_filter, update_operation)
            mongo_client.close()
            return result.acknowledged
        except errors.PyMongoError as e:
            logger.warning(f"Error updating pipeline config: {str(e)}")
            return False

    def get_repo(self, repo_name: str, repo_url: str, branch: str) -> dict:
        """ Retrieve a repo document based on repo_name, repo_url, and branch
            from the repo_configs collection.

        Args:
            repo_name (str): The name of the repository.
            repo_url (str): The URL of the repository.
            branch (str): The branch of the repository.

        Returns:
            dict: The repository document if found, otherwise None.
        """
        try:
            with MongoClient(self.mongo_uri) as mongo_client:
                database = mongo_client[MONGO_DB_NAME]
                collection = database[MONGO_PIPELINES_TABLE]
                query_filter = {
                    "repo_name": repo_name,
                    "repo_url": repo_url,
                    "branch": branch
                }
                return collection.find_one(query_filter) or {}
        except errors.PyMongoError:
            return {}

    def create_pipeline_document(self, pipeline_name: str, file_name: str, pipeline_config: dict) -> dict:
        """Generate a new pipeline document for insertion into pipelines.

        Args:
            pipeline_name (str): The name of the pipeline.
            file_name (str): The name of the YAML file for the pipeline.
            pipeline_config (dict): The pipeline configuration details.

        Returns:
            dict: A dictionary representing the new pipeline document.
        """
        return {
            "pipeline_name": pipeline_name,
            "pipeline_file_name": file_name,
            "pipeline_config": pipeline_config,
            "job_run_history": [],
            "active": False,
            "running": False,
            "last_commit_hash": ""
        }
