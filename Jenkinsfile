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
        
        stage('Install Dependencies') {
            steps {
                // Install requests module
                sh 'pip install requests'
            }
        }
        
        stage('Run Python Script') {
            steps {
                // Run Python script directly
                sh 'python3 trigger_jenkins.py'
            }
        }
    }
}
