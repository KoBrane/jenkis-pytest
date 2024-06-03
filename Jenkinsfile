pipeline {
    agent any

    stages {
        stage('Setup Python Environment') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            # Create a virtual environment
                            python3 -m venv venv
                            # Activate the virtual environment
                            . venv/bin/activate
                            # Upgrade pip
                            pip install --upgrade pip
                            # Install requests
                            pip install requests
                        '''
                    } else {
                        error "Unsupported operating system"
                    }
                }
            }
        }

        stage('Trigger Jenkins Job') {
            steps {
                script {
                    if (isUnix()) {
                        sh '''
                            # Activate the virtual environment
                            . venv/bin/activate
                            # Run the Python script to trigger the Jenkins job
                            python trigger_jenkins.py
                        '''
                    } else {
                        error "Unsupported operating system"
                    }
                }
            }
        }
    }
}
