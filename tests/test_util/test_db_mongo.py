""" All testing method for db_mongo 
"""
import copy
import mongomock
import pytest
from pymongo import (errors)
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from collections import OrderedDict
from util.db_mongo import MongoAdapter
from util.common_utils import get_logger
logger = get_logger("tests.test_util.test_db_mongo")
MONGO_DB_NAME = "CICDControllerDB"
MONGO_PIPELINES_TABLE = "repo_configs"

# def test_insert_pipeline():
#     """ Test the insert pipeline function
#     """
#     mongo_adapter = MongoAdapter()
#     pipeline_history = {
#         "pipeline_name": "test_pipeline",
#         "jobs": {}
#     }
#     result_id = mongo_adapter.insert_pipeline(pipeline_history)
#     print(result_id)
#     logger.info(result_id)


# def test_get_controller_history():
#     """ Test the get controller history function
#     """
#     mongo_adapter = MongoAdapter()
#     histories = mongo_adapter.get_controller_history()


# def test_update_pipeline():
#     """ Test update
#     """
#     mongo_adapter = MongoAdapter()
#     pipeline_history = {
#         "_id": "66ffda5ae12f948609e0c7d6",
#         "pipeline_name": "test_pipeline_2",
#         "jobs": {}
#     }
#     mongo_adapter.update_pipeline(pipeline_history)
#     pass


# def test_get_pipeline():
#     """ Test retrieve
#     """
#     mongo_adapter = MongoAdapter()
#     mongo_adapter.get_pipeline("66ffda5ae12f948609e0c7d6")


# # def test_del_pipeline():
# #     """ Test Delete
# #     """
# #     mongo_adapter = MongoAdapter()
# #     mongo_adapter.del_pipeline("66ffe21316f6b425edcb9715")


# def test_insert_job():
#     """ Test insert new job
#     """
#     mongo_adapter = MongoAdapter()
#     job_log = {
#         'pipeline_name': 'test_pipeline',
#         'job_run': 1,
#         'job_log': {}
#     }
#     mongo_adapter.insert_job(job_log)


# def test_update_job():
#     """ Test update new job
#     """
#     mongo_adapter = MongoAdapter()
#     updated_job_log = {
#         '_id': '66ffda5ce12f948609e0c7da',
#         'pipeline_name': 'test_pipeline',
#         'job_run': 1,
#         'job_log': {},
#         'success': True
#     }
#     mongo_adapter.update_job(updated_job_log)


class TestMongoDB:

    _mock_mongo = mongomock.MongoClient()

    @patch("util.db_mongo.MongoClient", return_value=_mock_mongo)
    def test_get_controller(self, mock_client):
        mongo_adapter = MongoAdapter()
        search_result = mongo_adapter.get_controller_history()
        assert search_result == {}

    @patch("util.db_mongo.MongoClient", side_effect=errors.PyMongoError())
    def test_get_controller_exception(self, mock_client):
        mongo_adapter = MongoAdapter()
        try:
            search_result = mongo_adapter.get_controller_history()
        except errors.PyMongoError as e:
            pass

    @patch("util.db_mongo.MongoClient", return_value=_mock_mongo)
    def test_pipeline_crud(self, mock_client):
        mongo_adapter = MongoAdapter()
        pipeline_history = {
            "pipeline_name": "test_pipeline",
            "jobs": {}
        }
        # Test insert and get
        result_id = mongo_adapter.insert_pipeline(
            pipeline_history)
        logger.info(f"log from test mongo adapter:{result_id}")
        search_result = mongo_adapter.get_pipeline(result_id)
        assert search_result == pipeline_history

        # Test update
        updated_history = copy.deepcopy(search_result)
        updated_history['jobs'] = {'1': 'random_id'}
        mongo_adapter.update_pipeline(updated_history)
        new_search_result = mongo_adapter.get_pipeline(result_id)
        assert new_search_result == updated_history

        # Test delete
        mongo_adapter.del_pipeline(result_id)
        new_search_result = mongo_adapter.get_pipeline(result_id)
        assert new_search_result is None

    @patch("util.db_mongo.MongoAdapter._delete", side_effect=errors.PyMongoError())
    @patch("util.db_mongo.MongoAdapter._update", side_effect=errors.PyMongoError())
    @patch("util.db_mongo.MongoAdapter._retrieve", side_effect=errors.PyMongoError())
    @patch("util.db_mongo.MongoAdapter._insert", side_effect=errors.PyMongoError())
    @patch("util.db_mongo.MongoClient", return_value=_mock_mongo)
    def test_pipeline_crud_exception(self, mock_client, insert, get, update, delete):
        mongo_adapter = MongoAdapter()
        pipeline_history = {
            "pipeline_name": "test_pipeline",
            "jobs": {}
        }
        result_id = mongo_adapter.insert_pipeline(
            pipeline_history)
        assert result_id is None
        search_result = mongo_adapter.get_pipeline("")
        assert search_result == {}
        update_result = mongo_adapter.update_pipeline(pipeline_history)
        assert update_result == False
        del_result = mongo_adapter.del_pipeline("")
        assert del_result == False
        pass

    @patch("util.db_mongo.MongoClient", return_value=_mock_mongo)
    def test_job_crud(self, mock_client):
        mongo_adapter = MongoAdapter()
        job_log = {
            'pipeline_name': 'test_pipeline',
            'job_run': 1,
            'job_log': {}
        }
        pipeline_config = {
            'global': {
                'stages': OrderedDict([
                    ('build', {})
                ])
            }
        }

        # Test insert and get
        result_id = mongo_adapter.insert_job("672817cdabdfc031a3ff26f4", pipeline_config)
        search_result = mongo_adapter.get_job(result_id)
        assert search_result['pipeline_config_used'] == pipeline_config

        # Test update
        updated_history = copy.deepcopy(search_result)
        updated_history['success'] = True
        mongo_adapter.update_job(result_id, updated_history)
        new_search_result = mongo_adapter.get_job(result_id)
        assert new_search_result == updated_history

        # Test delete
        mongo_adapter.del_job(result_id)
        new_search_result = mongo_adapter.get_job(result_id)
        assert new_search_result is None

    @patch("util.db_mongo.MongoAdapter._delete", side_effect=errors.PyMongoError())
    @patch("util.db_mongo.MongoAdapter._update", side_effect=errors.PyMongoError())
    @patch("util.db_mongo.MongoAdapter._retrieve", side_effect=errors.PyMongoError())
    @patch("util.db_mongo.MongoAdapter._insert", side_effect=errors.PyMongoError())
    @patch("util.db_mongo.MongoClient", return_value=_mock_mongo)
    def test_job_crud_exception(self, mock_client, insert, get, update, delete):
        mongo_adapter = MongoAdapter()
        job_log = {
            'pipeline_name': 'test_pipeline',
            'job_run': 1,
            'job_log': {}
        }
        pipeline_config = {
            'global': {
                'stages': OrderedDict([
                    ('build', {})
                ])
            }
        }
        result_id = mongo_adapter.insert_job(
            "672817cdabdfc031a3ff26f4", pipeline_config)
        assert result_id is None
        search_result = mongo_adapter.get_job("")
        assert search_result == {}
        update_result = mongo_adapter.update_job(job_log, pipeline_config)
        assert update_result == False
        del_result = mongo_adapter.del_job("")
        assert del_result == False
        pass

    @patch("util.db_mongo.MongoClient")
    def test_get_pipeline_config(self, mock_client):
        """Test retrieving pipeline config with success, not found, and exception cases."""
        mongo_adapter = MongoAdapter()
        collection = mock_client.return_value[MONGO_DB_NAME]['repo_configs']

        # Success case
        collection.find_one.return_value = {
            "_id": "12345",
            "pipelines": [{"pipeline_name": "test_pipeline", "pipeline_config": {"key": "value"}}]
        }
        result = mongo_adapter.get_pipeline_config(
            repo_name="test_repo",
            repo_url="https://github.com/test/test_repo",
            branch="main",
            pipeline_name="test_pipeline"
        )
        assert result == {"_id": "12345", "pipeline_config": {"key": "value"}}

        # Not found case
        collection.find_one.return_value = None
        result = mongo_adapter.get_pipeline_config(
            repo_name="test_repo",
            repo_url="https://github.com/test/test_repo",
            branch="main",
            pipeline_name="nonexistent_pipeline"
        )
        assert result == {}

        # Exception case
        collection.find_one.side_effect = errors.PyMongoError("Database error")
        result = mongo_adapter.get_pipeline_config(
            repo_name="test_repo",
            repo_url="https://github.com/test/test_repo",
            branch="main",
            pipeline_name="test_pipeline"
        )
        assert result == {}

    @patch("util.db_mongo.MongoClient")
    def test_update_pipeline_config(self, mock_client):
        """Test updating pipeline config with success, failure, and exception cases."""
        mongo_adapter = MongoAdapter()
        collection = mock_client.return_value[MONGO_DB_NAME]['repo_configs']

        # Success case
        mock_update_result = MagicMock(acknowledged=True)
        collection.update_one.return_value = mock_update_result
        result = mongo_adapter.update_pipeline_config(
            repo_name="test_repo",
            repo_url="https://github.com/test/test_repo",
            branch="main",
            pipeline_name="test_pipeline",
            pipeline_config={"key": "new_value"}
        )
        assert result is True

        # Failure case
        mock_update_result.acknowledged = False
        result = mongo_adapter.update_pipeline_config(
            repo_name="test_repo",
            repo_url="https://github.com/test/test_repo",
            branch="main",
            pipeline_name="test_pipeline",
            pipeline_config={"key": "new_value"}
        )
        assert result is False

        # Exception case
        collection.update_one.side_effect = errors.PyMongoError("Database error")
        result = mongo_adapter.update_pipeline_config(
            repo_name="test_repo",
            repo_url="https://github.com/test/test_repo",
            branch="main",
            pipeline_name="test_pipeline",
            pipeline_config={"key": "new_value"}
        )
        assert result is False

    @patch.object(MongoAdapter, 'get_repo')
    def test_get_repo_success(self, mock_get_repo):
        """Test successfully retrieving a repository document."""
        expected_repo = {
            "repo_name": "sample-repo",
            "repo_url": "https://github.com/sample-user/sample-repo",
            "branch": "main",
            "pipelines": []
        }
        mock_get_repo.return_value = expected_repo
        mongo_adapter = MongoAdapter()
        result = mongo_adapter.get_repo(
            "sample-repo",
            "https://github.com/sample-user/sample-repo",
            "main"
        )
        assert result == expected_repo

    @patch(
        "pymongo.collection.Collection.find_one",
        side_effect=errors.PyMongoError("Database error")
    )
    def test_get_repo_exception(self, mock_find_one):
        """Test get_repo to ensure it handles a PyMongoError and returns an empty dictionary."""
        mongo_adapter = MongoAdapter()
        result = mongo_adapter.get_repo(
            "sample-repo",
            "https://github.com/sample-user/sample-repo",
            "main"
        )
        assert result == {}

    def test_create_pipeline_document(self):
        """Test generating a new pipeline document."""
        mongo_adapter = MongoAdapter()
        pipeline_name = "test_pipeline"
        file_name = "test_pipeline.yml"
        pipeline_config = {"global": {"pipeline_name": "test_pipeline"}}

        result = mongo_adapter.create_pipeline_document(pipeline_name, file_name, pipeline_config)

        # Check the structure of the created document
        expected_document = {
            "pipeline_name": pipeline_name,
            "pipeline_file_name": file_name,
            "pipeline_config": pipeline_config,
            "job_run_history": [],
            "active": False,
            "running": False,
            "last_commit_hash": ""
        }
        assert result == expected_document
