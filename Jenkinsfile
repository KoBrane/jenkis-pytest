pipeline {
    agent any
    
    triggers {
        pollSCM('*/5 * * * *')
    }
    
    stages {
        stage('Checkout') {
            steps {
                // Checkout the repository
                checkout scm
            }
        }
        
        stage('Create Virtual Environment') {
            steps {
                // Create a virtual environment
                sh 'python3 -m venv venv'
            }
        }
        
        stage('Install Dependencies') {
            steps {
                // Activate the virtual environment and install requests module
                sh '. venv/bin/activate && pip install requests'
            }
        }
        
        stage('Run Python Script') {
            steps {
                // Activate the virtual environment and run Python script
                sh '. venv/bin/activate && python3 trigger_jenkins.py'
            }
        }
    }
}
