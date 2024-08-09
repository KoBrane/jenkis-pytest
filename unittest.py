import pytest
from unittest.mock import MagicMock
import os
import sys

# Mock imports
mock_github_util = MagicMock()
mock_gocd_util = MagicMock()
mock_jenkins_util = MagicMock()
mock_jira_util = MagicMock()
mock_metrics_util = MagicMock()
mock_branch_merge = MagicMock()
mock_gocd_monitor = MagicMock()
mock_metadata = MagicMock()
mock_migration_rules_update = MagicMock()
mock_slack = MagicMock()
mock_ArtifactoryPath = MagicMock()
mock_requests = MagicMock()

# Replace with actual imports where the functions are used
sys.modules['github_util'] = mock_github_util
sys.modules['gocd_util'] = mock_gocd_util
sys.modules['jenkins_util'] = mock_jenkins_util
sys.modules['jira_util'] = mock_jira_util
sys.modules['metrics_util'] = mock_metrics_util
sys.modules['branch_merge'] = mock_branch_merge
sys.modules['gocd_monitor'] = mock_gocd_monitor
sys.modules['metadata'] = mock_metadata
sys.modules['migration_rules_update'] = mock_migration_rules_update
sys.modules['slack'] = mock_slack
sys.modules['artifactory'] = mock_ArtifactoryPath
sys.modules['requests'] = mock_requests

# Mock environment variables
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    monkeypatch.setenv('JENKINS_PIPELINE', 'jenkins_pipeline')
    monkeypatch.setenv('ART_USER', 'art_user')
    monkeypatch.setenv('ART_PASSWORD', 'art_pass')
    monkeypatch.setenv('JIRA_PROJECT', 'jira_project')
    monkeypatch.setenv('JIRA', 'jira_url')
    monkeypatch.setenv('MONO_URL', 'mono_url')
    monkeypatch.setenv('MONO_GIT', 'mono_git')
    monkeypatch.setenv('MILESTONE', 'ms_approved')
    monkeypatch.setenv('BASE_BRANCH', 'mono_branch')
    monkeypatch.setenv('MONO_PIPELINE', 'mono_pipeline')
    monkeypatch.setenv('VM_PIPELINE', 'vm_pipeline')
    monkeypatch.setenv('AWS_PIPELINE', 'aws_pipeline')
    monkeypatch.setenv('REPO', 'repo')
    monkeypatch.setenv('ORGANIZATION', 'organization')
    monkeypatch.setenv('OVA_REPO', 'ova_repo')
    monkeypatch.setenv('AP_BASE_URL', 'ap_base_url')
    monkeypatch.setenv('REMOTEBUILD_USER', 'rb_user')
    monkeypatch.setenv('REMOTEBUILD_TOKEN', 'rb_token')

def test_show_output(mocker):
    mock_open = mocker.patch('builtins.open', mocker.mock_open())
    mock_makedirs = mocker.patch('os.makedirs')
    mock_popen = mocker.patch('subprocess.Popen')
    from your_script import show_output  # Replace with the actual import
    show_output('Test question', 'Test name', 'Test version')
    # Add assertions here

def test_notify(mocker):
    mock_platform = mocker.patch('platform.system', return_value='Linux')
    mock_popen = mocker.patch('subprocess.Popen')
    from your_script import notify  # Replace with the actual import
    notify('Test message')
    # Add assertions here

def test_get_value(mocker):
    mock_input = mocker.patch('builtins.input', return_value='y')
    from your_script import get_value  # Replace with the actual import
    result = get_value('Enter value: ', values=['y', 'n'])
    assert result == 'y'

def test_check_pr(mocker):
    mock_get_pr = mocker.patch('git_server.get_pr')
    mock_check_prs = mocker.patch('git_server.check_prs', return_value={'ready': [], 'errors': {}})
    from your_script import check_pr  # Replace with the actual import
    ready_prs = check_pr()
    assert ready_prs == []

def test_milestone(mocker):
    mock_create_milestone = mocker.patch('git_server.create_milestone')
    mock_get_milestone = mocker.patch('git_server.get_milestone', side_effect=Exception('unable to find milestone'))
    from your_script import milestone  # Replace with the actual import
    milestone('1.0.0', {})
    mock_create_milestone.assert_called_once_with('1.0.0 CAB Approved')

def test_add_pr_label(mocker):
    mock_add_pr_label = mocker.patch('git_server.add_pr_label')
    from your_script import add_pr_label  # Replace with the actual import
    state = {'select PRs to include': [1, 2, 3]}
    add_pr_label('1.0.0', state)
    mock_add_pr_label.assert_called_with(3, 'skip-jenkins')

def test_move_pr(mocker):
    mock_set_pr_milestone = mocker.patch('git_server.set_pr_milestone')
    mock_get_pr = mocker.patch('git_server.get_pr')
    from your_script import move_pr  # Replace with the actual import
    state = {'select PRs to include': [1, 2]}
    move_pr('1.0.0', state)
    mock_set_pr_milestone.assert_called_with(2, '1.0.0 CAB Approved')

def test_final_pr(mocker):
    mock_new_pr = mocker.patch('git_server.new_pr', return_value=MagicMock(number=10))
    mock_add_pr_label = mocker.patch('git_server.add_pr_label')
    from your_script import final_pr  # Replace with the actual import
    result = final_pr('1.0.0', {})
    assert result == 10
    mock_add_pr_label.assert_called_once_with(10, 'skip-jenkins')

def test_get_ova_details(mocker):
    mock_get = mocker.patch('requests.get')
    mock_get.return_value.json.return_value = {'size': 5000000000}
    from your_script import get_ova_details  # Replace with the actual import
    result = get_ova_details('1.0.0', {})
    assert result['ova_size'] == '5.0'

def test_upload_to_artifactory(mocker):
    mock_deploy_file = mocker.patch('artifactory.ArtifactoryPath.deploy_file')
    from your_script import upload_to_artifactory  # Replace with the actual import
    state = {'run remotebuild': {'result': {'build_info': {'build_num': 123}}}}
    upload_to_artifactory('1.0.0', state)
    mock_deploy_file.assert_called_with('allure-report.zip')

def test_release(mocker):
    mock_create_dev_release = mocker.patch('git_server.create_dev_release')
    from your_script import release  # Replace with the actual import
    state = {'select PRs to include': [1, 2]}
    release('1.0.0', state)
    mock_create_dev_release.assert_called_once_with('1.0.0', ANY, 'mono_branch')

def test_delete_branches(mocker):
    mock_delete_branch = mocker.patch('git_server.delete_branch')
    mock_prune_milestone = mocker.patch('git_server.prune_milestone')
    from your_script import delete_branches  # Replace with the actual import
    state = {'run branch-merge': {'result': 'branch'}}
    delete_branches('1.0.0', state)
    mock_delete_branch.assert_called_once_with('branch')

def test_delete_oldest_milestone(mocker):
    mock_delete_n_oldest_milestones = mocker.patch('git_server.delete_n_oldest_milestones')
    from your_script import delete_oldest_milestone  # Replace with the actual import
    delete_oldest_milestone('1.0.0', {})
    mock_delete_n_oldest_milestones.assert_called_once_with(1)

def test_set_major_version_milestone(mocker):
    mock_set_pr_milestone = mocker.patch('git_server.set_pr_milestone')
    from your_script import set_major_version_milestone  # Replace with the actual import
    state = {'select PRs to include': [1]}
    set_major_version_milestone('1.0.0', state)
    mock_set_pr_milestone.assert_called_once_with(1, '1.0')

def test_add_patch_label(mocker):
    mock_add_pr_label = mocker.patch('git_server.add_pr_label')
    from your_script import add_patch_label  # Replace with the actual import
    state = {'select PRs to include': [1]}
    add_patch_label('1.0.0', state)
    mock_add_pr_label.assert_called_once_with(1, 'PATCH')

def test_calculate_metrics(mocker):
    mock_get_pr = mocker.patch('git_server.get_pr')
    mock_get_user_real_name = mocker.patch('git_server.get_user_real_name')
    mock_commit_dev_stats = mocker.patch('metrics_util.Elk().commit_dev_stats', return_value=None)
    from your_script import calculate_metrics  # Replace with the actual import
    state = {
        'run remotebuild': {'result': {'build_info': {'build_num': '123'}, 'duration': 120}},
        'count pr queue': {'result': {'pr_count': 5}},
        'create & merge PR for the next release': {'result':
