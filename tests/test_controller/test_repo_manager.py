import pytest
from unittest.mock import MagicMock, patch, mock_open
import git
from controller.repo_manager import RepoManager
import yaml

# Constants
PUBLIC_REPO_URL = "https://github.com/bkeepers/dotenv.git"
LOCAL_REPO_PATH = "/Users/lin99nn/Desktop/hw3-peihsuan-lin"
NONEXISTENT_REMOTE_URL = "https://github.com/test/nonexistent_repo.git"
NONEXISTENT_LOCAL_PATH = "/Users/lin99nn/Desktop/hw3"
YAML_FILE_PATH = "/Users/lin99nn/Desktop/hw3-peihsuan-lin/.github/workflows/ci.yml"

def test_is_remote():
    # Test for a remote repository URL
    repo = RepoManager(repo_url=PUBLIC_REPO_URL)
    assert repo.is_remote_repo() is True

    # Test for a local repository path
    repo = RepoManager(repo_url=LOCAL_REPO_PATH)
    assert repo.is_remote_repo() is False

@patch('os.path.exists')
@patch('git.Repo.clone_from')
def test_setup_remote_new(mock_clone, mock_exists):
    # clone a new remote repo
    mock_exists.return_value = False 
    mock_clone.return_value = MagicMock()

    repo = RepoManager(repo_url=PUBLIC_REPO_URL)
    repo.setup_repo()

    mock_clone.assert_called_with(PUBLIC_REPO_URL, repo.local_dir, branch='main')

@patch('os.path.exists')
@patch('git.Repo')
def test_setup_remote_existing(mock_repo, mock_exists):
    # remote repo exists locally
    mock_exists.return_value = True
    mock_repo.return_value = MagicMock()

    repo = RepoManager(repo_url=PUBLIC_REPO_URL)
    repo.setup_repo()

    mock_repo.assert_not_called()  # Since the repository already exists, cloning should not occur.

@patch('os.path.exists')
@patch('git.Repo.clone_from')
def test_setup_remote_not_found(mock_clone, mock_exists):
    # Simulate that the local directory does not exist
    mock_exists.return_value = False
    # Simulate GitCommandError when cloning
    mock_clone.side_effect = git.exc.GitCommandError('git clone', 'error')

    repo = RepoManager(repo_url=NONEXISTENT_REMOTE_URL)
    with pytest.raises(git.exc.GitCommandError):
        repo.setup_repo()

@patch('os.path.exists')
def test_setup_local_not_found(mock_exists):
    # Simulate that the local path does not exist
    mock_exists.return_value = False

    repo = RepoManager(repo_url=NONEXISTENT_LOCAL_PATH)
    with pytest.raises(FileNotFoundError):
        repo.setup_repo()

@patch('os.path.exists')
@patch('git.Repo')
def test_setup_local_existing(mock_repo, mock_exists):
    mock_exists.return_value = True
    mock_repo.return_value = MagicMock()

    repo = RepoManager(repo_url=LOCAL_REPO_PATH)
    repo.setup_repo()

    mock_repo.assert_not_called()  # Since the repository exists, cloning should not happen.

def test_parse_yaml_auto():
    with patch('os.walk', return_value=[(LOCAL_REPO_PATH, [], ['config.yaml'])]):
        with patch('builtins.open', mock_open(read_data='key: value')) as mock_file:
            with patch('yaml.safe_load', return_value={'key': 'value'}):
                repo_manager = RepoManager(repo_url=LOCAL_REPO_PATH)
                repo_manager.get_yaml_path()
                result = repo_manager.parse_yaml()
                
                assert result == {'key': 'value'}
                mock_file.assert_called_with(f'{LOCAL_REPO_PATH}/config.yaml', 'r', encoding='utf-8')

def test_parse_yaml_specific_file():
    # Mock open
    with patch('builtins.open', mock_open(read_data='key: value')) as mock_file:
        # Mock yaml.safe_load
        with patch('yaml.safe_load', return_value={'key': 'value'}):
            repo_manager = RepoManager(repo_url=LOCAL_REPO_PATH)
            repo_manager.get_yaml_path(yaml_file_path=YAML_FILE_PATH)  # Set the specific YAML file path
            result = repo_manager.parse_yaml()

            assert result == {'key': 'value'}
            mock_file.assert_called_with(YAML_FILE_PATH, 'r', encoding='utf-8')
