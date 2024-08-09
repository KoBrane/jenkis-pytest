import unittest
from unittest.mock import patch, MagicMock
import os
import sys

# Mock external modules and functions
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

# Mock environment variables
mock_env = {
    'JENKINS_PIPELINE': 'mock_pipeline',
    'ART_USER': 'mock_user',
    'ART_PASSWORD': 'mock_pass',
    'JIRA_PROJECT': 'MOCK',
    'JIRA': 'https://mock-jira.com',
    'MONO_URL': 'https://mock-mono.com',
    'MONO_GIT': 'https://mock-git.com/mock-repo.git',
    'MILESTONE': 'Mock Milestone',
    'BASE_BRANCH': 'main',
    'MONO_PIPELINE': 'mock_mono_pipeline',
    'VM_PIPELINE': 'mock_vm_pipeline',
    'AWS_PIPELINE': 'mock_aws_pipeline',
    'REPO': 'mock-repo',
    'ORGANIZATION': 'mock-org',
    'OVA_REPO': 'mock-ova-repo',
    'AP_BASE_URL': 'https://mock-artifactory.com',
    'REMOTEBUILD_USER': 'mock_rb_user',
    'REMOTEBUILD_TOKEN': 'mock_rb_token'
}

# Mock FUNCTIONS list (replace with actual functions from your script)
FUNCTIONS = [
    {'name': 'select_prs', 'question': 'select PRs to include'},
    {'name': 'make_branch', 'question': 'make a new branch'},
    # ... add other functions here
]

class TestBuildProcess(unittest.TestCase):
    
    @patch.dict('os.environ', mock_env)
    @patch('github_util.GitHub', return_value=mock_github_util)
    @patch('jira_util.Jira', return_value=mock_jira_util)
    @patch('jenkins_util.Jenkins', return_value=mock_jenkins_util)
    def test_build_process(self, mock_jenkins, mock_jira, mock_github):
        # Mock get_version function
        with patch('__main__.get_version', return_value='1.0.0'):
            # Mock all the @ask decorated functions
            for func in FUNCTIONS:
                setattr(self, f'mock_{func["name"]}', MagicMock(return_value=f'mock_{func["name"]}_result'))
                
            # Mock the main function
            with patch('__main__.main') as mock_main:
                # Run the main function
                mock_main(['--auto', '123', '456'])
                
                # Assert that main was called with the correct arguments
                mock_main.assert_called_once_with(['--auto', '123', '456'])
            
            # Assert that each function was called
            for func in FUNCTIONS:
                getattr(self, f'mock_{func["name"]}').assert_called_once()
            
    # Add more specific tests for individual functions as needed

if __name__ == '__main__':
    unittest.main()