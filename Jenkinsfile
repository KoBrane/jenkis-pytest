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
// pipeline {
//     agent any

//     triggers {
//         // Schedule the job to run every 5 minutes
//         cron('H/5 * * * *')
//     }

//     environment {
//         // Define the repository URL
//         REPO_URL = 'https://github.com/KoBrane/jenkis-pytest.git'
//         // Define the branch to check
//         BRANCH = 'main'
//     }

//     stages {
//         stage('Check and Pull Changes') {
//             steps {
//                 script {
//                     // Clone the repository if it doesn't exist, otherwise fetch the latest changes
//                     if (!fileExists('jenkis-pytest')) {
//                         git branch: env.BRANCH, url: env.REPO_URL
//                     } else {
//                         dir('jenkis-pytest') {
//                             sh 'git fetch --all'
//                             def changes = sh(script: "git diff --name-only origin/${env.BRANCH}", returnStdout: true).trim()
//                             if (changes) {
//                                 echo 'Changes detected, pulling the latest changes'
//                                 sh 'git pull origin ${env.BRANCH}'
//                             } else {
//                                 echo 'No changes detected'
//                             }
//                         }
//                     }
//                 }
//             }
//         }

//         stage('Set Up Python Environment') {
//             steps {
//                 script {
//                     // Ensure necessary Python packages are installed
//                     sh '''
//                         python3 -m venv venv
//                         . venv/bin/activate
//                         pip install requests
//                     '''
//                 }
//             }
//         }

//         stage('Run Python Script') {
//             steps {
//                 script {
//                     dir('jenkis-pytest') {
//                         sh '''
//                             . ../venv/bin/activate
//                             python3 trigger_jenkins.py
//                         '''
//                     }
//                 }
//             }
//         }
//     }
// }
