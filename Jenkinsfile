pipeline {
    agent any
    
    environment {
        REPO_OWNER = 'KoBrane'
        REPO_NAME = 'jenkis-pytest'
        BRANCH = 'main'
    }
    
    
    stages {
        stage('Clone Repository') {
            steps {
                script {
                    cleanWs()
                    checkout([$class: 'GitSCM', 
                        branches: [[name: "*/${BRANCH}"]], 
                        userRemoteConfigs: [[
                            url: "https://github.com/${REPO_OWNER}/${REPO_NAME}.git",
                            credentialsId: 'god-level-access'
                        ]]
                    ])
                }
            }
        }
        
        stage('Fetch Milestones') {
            steps {
                script {
                    withCredentials([usernamePassword(credentialsId: 'god-level-access', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')]) {
                        def allMilestones = fetchAllMilestones()
                        echo "Fetched Milestones: ${allMilestones}"
                        
                        def releaseMilestones = filterReleaseMilestones(allMilestones)
                        def cabMilestone = findCABMilestone(allMilestones)
                        
                        env.RELEASE_MILESTONES = writeJSON(json: releaseMilestones, returnText: true)
                        env.CAB_MILESTONE = writeJSON(json: cabMilestone ?: [:], returnText: true)
                        
                        echo "Release Milestones: ${releaseMilestones*.title.join(', ')}"
                        echo "CAB Milestone: ${cabMilestone?.title ?: 'Not found'}"
                    }
                }
            }
        }
        
        stage('Process Milestones') {
            steps {
                script {
                    def releaseMilestones = readJSON text: env.RELEASE_MILESTONES
                    def cabMilestone = readJSON text: env.CAB_MILESTONE
                    
                    processMilestones(releaseMilestones, 'Release')
                    
                    if (cabMilestone) {
                        processMilestones([cabMilestone], 'CAB')
                    } else {
                        echo "No CAB milestone found to process"
                    }
                }
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            build job: 'wils', wait: true
            build job: 'hercules', wait: true
            build job: 'atlas', wait: true
            build job: 'Ama'
        }
    }
}

def fetchAllMilestones() {
    def response = sh(script: """
        set -x
        curl -s -v -f -u ${env.USERNAME}:${env.PASSWORD} \
             "https://github.com/api/v3/repos/${REPO_OWNER}/${REPO_NAME}/milestones?per_page=100&state=all"
    """, returnStdout: true)
    
    return readJSON(text: response.trim())
}

def filterReleaseMilestones(allMilestones) {
    return allMilestones.findAll { milestone ->
        milestone.title ==~ /Release\/.*\sApproved/
    }
}

def findCABMilestone(allMilestones) {
    return allMilestones.find { milestone ->
        milestone.title == 'CAB Approved'
    }
}

def processMilestones(milestones, type) {
    milestones.each { milestone ->
        echo "Processing ${type} milestone: ${milestone.title} (Number: ${milestone.number})"
        def prs = fetchPRs(milestone.number)
        if (prs.isEmpty()) {
            echo "No PRs found for this milestone."
        } else {
            prs.each { pr ->
                echo "PR #${pr.number}: ${pr.title}"
            }
        }
    }
}

def fetchPRs(milestoneNumber) {
    def response = sh(script: """
        set -x
        curl -v -f -s -u ${env.USERNAME}:${env.PASSWORD} \
             "https://github.com/api/v3/repos/${REPO_OWNER}/${REPO_NAME}/issues?milestone=${milestoneNumber}&per_page=100&state=all"
    """, returnStdout: true)
    
    def issues = readJSON(text: response.trim())
    return issues.findAll { it.pull_request }
}
