""" All testing method for db_mongo 
"""
import copy
import mongomock
import pytest
from pymongo import (errors)
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from util.db_mongo import MongoAdapter
from util.common_utils import get_logger
logger = get_logger("tests.test_util.test_db_mongo")


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

        # Test insert and get
        result_id = mongo_adapter.insert_job(
            job_log)
        logger.info(f"log from test mongo adapter:{result_id}")
        search_result = mongo_adapter.get_job(result_id)

        # Test update
        assert search_result == job_log
        updated_history = copy.deepcopy(search_result)
        updated_history['success'] = True
        mongo_adapter.update_job(updated_history)
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
        result_id = mongo_adapter.insert_job(
            job_log)
        assert result_id is None
        search_result = mongo_adapter.get_job("")
        assert search_result == {}
        update_result = mongo_adapter.update_job(job_log)
        assert update_result == False
        del_result = mongo_adapter.del_job("")
        assert del_result == False
        pass
