""" Manage connection to MongoDB, and provides functions for relevent CRUD operation
"""
import copy
from datetime import datetime, timezone
import time
import bson
# from bson import ObjectId
from pydantic import ValidationError
from pymongo import (MongoClient, errors)
from util.common_utils import (get_env, get_logger, MongoHelper)
from util.model import (PipelineInfo, RepoConfig, SessionDetail)

env = get_env()
logger = get_logger("util.db_mongo")
MONGO_DB_NAME = "CICDControllerDB"
MONGO_PIPELINES_TABLE = "repo_configs"
MONGO_JOBS_TABLE = "jobs_history"
MONGO_REPOS_TABLE = "sessions"
# pylint: disable=logging-fstring-interpolation
# pylint: disable=fixme

class MongoAdapter:
    """ Adapter class to provide standardize queries to mongo db
    """

    def __init__(self):
        """ Default Constructor
        """
        # store the mongoDB url in bash rc file. Using atlas for this.
        # self.mongo_uri = os.getenv('MONGO_DB_URL')
        self.mongo_uri = env['MONGO_DB_URL'] if 'MONGO_DB_URL' in env else ""

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
        """ Generic Helper method to update the data. Assume Mongo object
        _id present in the data

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

    def _update_by_query(self, query:dict, data:dict, db_name: str, collection_name: str)-> bool:
        """ Generic Helper method to update the selected record based on query, 
        will also insert the new document if no document is present. Do not 
        require mongo object id to be present in the data

        Args:
            query (dict): field name and value for primary key(s).
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
        # try pop the _id field if present
        if '_id' in updated_data:
            updated_data.pop('_id')
        update_operation = {'$set': updated_data}
        result = collection.update_one(
            query, update_operation, upsert=True)
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

    def _retrieve_by_query(self, query:dict, db_name: str,
            collection_name: str) -> dict:
        """ Retrieve the first found record based on given query dictionary

        Args:
            query (dict): query filter parameters (key=value pair). Empty dict
            will retrieve all documents
            db_name (str): database to be searched into
            collection_name (str): collection(table) to be searched into

        Returns:
            dict: target record in dict form
        """
        mongo_client = MongoClient(self.mongo_uri)
        database = mongo_client[db_name]
        collection = database[collection_name]
        result = collection.find_one(query)
        # Follow best practise to close connection to db immediately
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

    def insert_repo_pipelines(
            self,
            repo_config:RepoConfig,
            db_name: str = MONGO_DB_NAME,
            collection_name: str = MONGO_PIPELINES_TABLE) -> bool:
        """ Insert a new repository record with corresponding pipelines configuration info. 
        into the repo_configs table. 
        If the repository with the primary keys (repo_name, url, branch) already exists, 
        will update instead

        Args:
            pipeline_history (dict): dictionary of the history record in key=value pairs
            db_name (str, optional): database to be inserted into. Defaults to MONGO_DB_NAME.
            collection_name (str, optional): collection(table) to be inserted into.
                Defaults to MONGO_PIPELINES_TABLE.

        Returns:
            bool: indicator if successful
        """
        try:
            query_filter = {
                'repo_name':repo_config.repo_name,
                'repo_url': repo_config.repo_url,
                'branch': repo_config.branch
            }
            updates = repo_config.model_dump()
            if '_id' in updates:
                updates.pop('_id')
            acknowledge = self._update_by_query(query_filter, updates, db_name, collection_name)
            return acknowledge
        except errors.PyMongoError as e:
            logger.warning(
                f"Error inserting new pipeline, exception is {e}")
            return False

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

    def insert_job(self,
                   pipeline_info:PipelineInfo,
                   pipeline_config: dict, stages_to_run: list = None) -> str:
        """
        Inserts a new job with initialized stages into the jobs table.

        Args:
            pipeline_info (PipelineInfo): Information data for target pipeline
            pipeline_config (dict): Configuration of pipeline stages.
            stages_to_run (list, optional): Stages to initialize; defaults to all.

        Returns:
            str: ID of the inserted job document.
        """
        try:
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
                "pipeline_name": pipeline_info.pipeline_name,
                "run_number": len(pipeline_info.job_run_history) + 1,
                "git_commit_hash": pipeline_info.last_commit_hash,
                "pipeline_config_used": pipeline_config,
                "status": None,
                "start_time": time.asctime(),
                "completion_time": "",
                "logs": stage_logs
            }
            return self._insert(job_data, MONGO_DB_NAME, MONGO_JOBS_TABLE)
        except errors.PyMongoError as e:
            logger.warning(f"Error inserting new job: {e}")
            return None

    def update_job(self, jobs_id: str, updates: dict) -> bool:
        """
        Updates specified fields in a job document.

        Args:
            jobs_id (str): ID of the job to update.
            updates (dict): A dictionary of fields and their new values to update.

        Returns:
            bool: True if the update succeeded, False otherwise.
        """
        try:
            job = self._retrieve(jobs_id, MONGO_DB_NAME, MONGO_JOBS_TABLE)
            if not job:
                logger.warning(f"Job with ID {jobs_id} not found.")
                return False
            job.update(updates)
            return self._update(job, MONGO_DB_NAME, MONGO_JOBS_TABLE)
        except errors.PyMongoError as e:
            logger.warning(f"Error updating job: {e}")
            return False

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
        except errors.PyMongoError as e:
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
        """ Insert a new repository session record into repos_collection

        Args:
            repo_data (dict): dictionary of the repository data
            db_name (str, optional): database to be inserted into. Defaults to MONGO_DB_NAME.
            collection_name (str, optional): collection(table) to be inserted into. 
                Defaults to MONGO_REPOS_TABLE.

        Returns:
            str: the inserted_id (converted to str) if successful
        """
        try:
            return self._insert(repo_data, db_name, collection_name)
        except errors.PyMongoError as e:
            logger.warning(f"Error inserting new repository, exception is {e}")
            return None

    def get_session(
            self,
            user_id: str,
            db_name: str = MONGO_DB_NAME,
            collection_name: str = MONGO_REPOS_TABLE) -> dict:
        """
        Retrieve the last set repository for a specific user.

        Args:
            user_id (str): The ID of the user whose last set repository to retrieve.
            db_name (str, optional): Target database. Defaults to MONGO_DB_NAME.
            collection_name (str, optional): Collection (table) to retrieve from.
                Defaults to MONGO_REPOS_TABLE.

        Returns:
            dict: The last repository entry in dictionary form for the user, or None if not found.
        """
        try:
            query_filter = {"user_id": user_id}

            result = self._retrieve_by_query(
                query=query_filter,
                db_name=db_name,
                collection_name=collection_name
            )

            return result if result else {}

        except errors.PyMongoError as e:
            logger.warning(f"Error retrieving last set repository for user {user_id}: {e}")
            return {}

    def update_session(
            self,
            session_data: dict,
            db_name: str = MONGO_DB_NAME,
            collection_name: str = MONGO_REPOS_TABLE) -> bool:
        """
        Upsert a session record in the database based on user ID. If a record with the same user_id exists,
        it will update the record; otherwise, a new record will be inserted.

        Args:
            session_data (dict): The session data to upsert, including the "user_id" field.
            db_name (str, optional): The database name. Defaults to MONGO_DB_NAME.
            collection_name (str, optional): The collection name. Defaults to MONGO_REPOS_TABLE.

        Returns:
            bool: True if the upsert operation was successful, False otherwise.

        Example:
            session_data = {
                "user_id": "12345",
                "repo_url": "https://github.com/example/repo",
                "repo_name": "repo",
                "branch": "main",
                "commit_hash": "abc123",
                "is_remote": True,
                "time": "2024-11-15 12:34:56"
            }

            result = update_session(session_data)
            if result:
                print("Session updated successfully.")
            else:
                print("Failed to update session.")
        """
        try:
            # Define the query filter based on user_id
            query_filter = {"user_id": session_data.get("user_id")}

            if not query_filter["user_id"]:
                logger.warning("Upsert failed: 'user_id' not found in session_data.")
                return False

            # Prepare the data for the update
            updates = session_data.copy()
            if '_id' in updates:
                updates.pop('_id')

            # Use the generic helper method for the upsert operation
            acknowledge = self._update_by_query(query_filter, updates, db_name, collection_name)
            return acknowledge

        except errors.PyMongoError as e:
            logger.warning(f"Error in update_session, exception is {e}")
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
            }
            projection = {
                "_id": 1,
                f"pipelines.{pipeline_name}.pipeline_config": 1
            }
            mongo_client = MongoClient(self.mongo_uri)
            database = mongo_client[MONGO_DB_NAME]
            collection = database[MONGO_PIPELINES_TABLE]
            pipeline_document = collection.find_one(query_filter, projection)
            mongo_client.close()
            if pipeline_document:
                pipeline_config = pipeline_document["pipelines"][pipeline_name]["pipeline_config"]
                return {"_id": pipeline_document["_id"], "pipeline_config": pipeline_config}
            return {}
        except errors.PyMongoError as e:
            logger.warning(f"Error retrieving pipeline config: {str(e)}")
            return {}

    def get_pipeline_history(self, repo_name: str, repo_url: str,
                            branch: str, pipeline_name: str) -> dict:
        """Retrieve a specific pipeline's history in a flat structure.

        Args:
            repo_name (str): Repository name.
            repo_url (str): Repository URL.
            branch (str): Repository branch.
            pipeline_name (str): Name of the pipeline.

        Returns:
            dict: Pipeline history data. Empty dict if not found.
        """
        try:
            query_filter = {
                'repo_name': repo_name,
                'repo_url': repo_url,
                'branch': branch,
            }
            projection = {
                "_id": 1,
                f"pipelines.{pipeline_name}": 1
            }
            mongo_client = MongoClient(self.mongo_uri)
            database = mongo_client[MONGO_DB_NAME]
            collection = database[MONGO_PIPELINES_TABLE]
            pipeline_document = collection.find_one(query_filter, projection)
            mongo_client.close()
            if pipeline_document:
                pipeline_data = pipeline_document["pipelines"].get(pipeline_name, {})
                pipeline_data["pipeline_name"] = pipeline_name
                return pipeline_data
            logger.warning(
                f"No pipeline config found for '{pipeline_name}' "
                f"in '{repo_name}' for url {repo_url} on branch '{branch}'."
            )
            return {}
        except errors.PyMongoError as e:
            logger.warning(f"Error retrieving pipeline config: {str(e)}")
            return {}
        except AttributeError as attr:
            logger.warning(f"pipelines: {pipeline_document} is empty. Error: {str(attr)}")
            print(f"pipelines: {pipeline_document} is empty.\nError: {str(attr)}")
            return {}

    def update_pipeline_info(
            self,
            repo_name: str,
            repo_url: str,
            branch: str,
            pipeline_name: str,
            updates: dict) -> bool:
        """ Update the fields in the repo_configs collection for a specific pipeline.
        Will catch PyMongoError

        Args:
            repo_name (str): The repository name.
            repo_url (str): The URL of the repository.
            branch (str): The branch of the repository.
            pipeline_name (str): The name of the pipeline to update.
            updates (dict): key:value pair of new pipeline configuration to be updated

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            query_filter = {
                'repo_name': repo_name,
                'repo_url': repo_url,
                'branch': branch,
                #'pipelines': pipeline_name
            }

            # Check if the specific repository and pipeline exists
            exist = self._retrieve_by_query(query_filter, MONGO_DB_NAME, MONGO_PIPELINES_TABLE)
            if not exist or pipeline_name not in exist['pipelines']:
                # We need to initialize PipelineInfo data for a new pipeline
                # Try convert the update to a PipelineInfo object matching the
                # db schema
                pipeline_info = PipelineInfo.model_validate(updates)
                # Convert it back for later usage
                updates = pipeline_info.model_dump()
            update_dict = {f'pipelines.{pipeline_name}.{k}': v for k, v in updates.items()}
            status = self._update_by_query(
                query_filter,update_dict,MONGO_DB_NAME,MONGO_PIPELINES_TABLE
                )
            return status
        except (errors.PyMongoError, ValidationError) as e:
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

    #TODO - Discuss - this method can be replaced
    def create_pipeline_document(self, file_name: str, pipeline_config: dict) -> dict:
        """Generate a new pipeline document for insertion into pipelines.

        Args:
            file_name (str): The name of the YAML file for the pipeline.
            pipeline_config (dict): The pipeline configuration details.

        Returns:
            dict: A dictionary representing the new pipeline document.
        """
        return {
            "pipeline_file_name": file_name,
            "pipeline_config": pipeline_config,
            "job_run_history": [],
            "active": False,
            "running": False,
            "last_commit_hash": ""
        }

    def get_pipeline_run_summary(
        self, repo_url: str, pipeline_name: str = None, stage_name: str = None,
        job_name: str = None, run_number: int = None) -> list:
        """
        Retrieves pipeline run data with optional filters for pipelines, stages, jobs, 
        and run numbers.

        Args:
            repo_url (str): Repository URL.
            pipeline_name (str, optional): Pipeline name filter.
            stage_name (str, optional): Stage name filter.
            job_name (str, optional): Job name filter.
            run_number (int, optional): Run number filter.

        Returns:
            list: A list of dictionaries, where each dictionary contains data for a 
                    pipeline run that matches the filters.
        """
        match_filter = MongoHelper.build_match_filter(repo_url, pipeline_name)
        aggregation_pipeline = MongoHelper.build_aggregation_pipeline(
            match_filter, pipeline_name=pipeline_name, stage_name=stage_name,
            job_name=job_name, run_number=run_number
        )
        projection_fields = MongoHelper.build_projection(stage_name, job_name)
        aggregation_pipeline.append({"$project": projection_fields})
        aggregation_pipeline.append({"$sort": {"job_details.run_number": -1}})

        try:
            mongo_client = MongoClient(self.mongo_uri)
            database = mongo_client[MONGO_DB_NAME]
            repo_collection = database[MONGO_PIPELINES_TABLE]
            result = list(repo_collection.aggregate(aggregation_pipeline))
            mongo_client.close()
            return result

        except errors.PyMongoError as e:
            logger.error(f"Error retrieving pipeline runs with job details for \
                         repo {repo_url}: {e}")
            return []
