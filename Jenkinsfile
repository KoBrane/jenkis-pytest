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
        
        stage('Run Python Script') {
            steps {
                // Run Python script directly
                sh 'python3 trigger_jenkins.py'
            }
        }
    }
}
