// pipeline {
//     agent any
    
//     environment {
//         REPO_OWNER = 'KoBrane'
//         REPO_NAME = 'jenkis-pytest'
//         BRANCH = 'main'
//     }
    
    
//     stages {
//         stage('Clone Repository') {
//             steps {
//                 script {
//                     cleanWs()
//                     checkout([$class: 'GitSCM', 
//                         branches: [[name: "*/${BRANCH}"]], 
//                         userRemoteConfigs: [[
//                             url: "https://github.com/${REPO_OWNER}/${REPO_NAME}.git",
//                             credentialsId: 'god-level-token'
//                         ]]
//                     ])
//                 }
//             }
//         }
        
//         stage('Fetch Milestones') {
//             steps {
//                 script {
//                     withCredentials([usernamePassword(credentialsId: 'god-level-token', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')]) {
//                         def allMilestones = fetchAllMilestones()
//                         echo "Fetched Milestones: ${allMilestones}"
                        
//                         def releaseMilestones = filterReleaseMilestones(allMilestones)
//                         def cabMilestone = findCABMilestone(allMilestones)
                        
//                         env.RELEASE_MILESTONES = writeJSON(json: releaseMilestones, returnText: true)
//                         env.CAB_MILESTONE = writeJSON(json: cabMilestone ?: [:], returnText: true)
                        
//                         echo "Release Milestones: ${releaseMilestones*.title.join(', ')}"
//                         echo "CAB Milestone: ${cabMilestone?.title ?: 'Not found'}"
//                     }
//                 }
//             }
//         }
        
//         stage('Process Milestones') {
//             steps {
//                 script {
//                     def releaseMilestones = readJSON text: env.RELEASE_MILESTONES
//                     def cabMilestone = readJSON text: env.CAB_MILESTONE
                    
//                     processMilestones(releaseMilestones, 'Release')
                    
//                     if (cabMilestone) {
//                         processMilestones([cabMilestone], 'CAB')
//                     } else {
//                         echo "No CAB milestone found to process"
//                     }
//                 }
//             }
//         }
//     }
    
//     post {
//         always {
//             cleanWs()
//         }
//         success {
//             build job: 'wils', wait: true
//             build job: 'hercules', wait: true
//             build job: 'atlas', wait: true
//             build job: 'Ama'
//         }
//     }
// }

// def fetchAllMilestones() {
//     def response = sh(script: """
//         set -x
//         curl -s -v -f -u ${env.USERNAME}:${env.PASSWORD} \
//              "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/milestones?per_page=100&state=all"
//     """, returnStdout: true)
//     def (content, statusCode) = response.trim().split('\n')
    
//     echo "HTTP Status Code: ${statusCode}"
//     echo "Response content: ${content}"
    
//     if (statusCode != "200" || content.trim().startsWith('<!DOCTYPE html>')) {
//         error "Received unexpected response. Status code: ${statusCode}"
//     }
    
//     return readJSON(text: content)
// }

// def filterReleaseMilestones(allMilestones) {
//     return allMilestones.findAll { milestone ->
//         milestone.title ==~ /Release\/.*\sApproved/
//     }
// }

// def findCABMilestone(allMilestones) {
//     return allMilestones.find { milestone ->
//         milestone.title == 'CAB Approved'
//     }
// }

// def processMilestones(milestones, type) {
//     milestones.each { milestone ->
//         echo "Processing ${type} milestone: ${milestone.title} (Number: ${milestone.number})"
//         def prs = fetchPRs(milestone.number)
//         if (prs.isEmpty()) {
//             echo "No PRs found for this milestone."
//         } else {
//             prs.each { pr ->
//                 echo "PR #${pr.number}: ${pr.title}"
//             }
//         }
//     }
// }

// def fetchPRs(milestoneNumber) {
//     def response = sh(script: """
//         set -x
//         curl -v -f -s -u ${env.USERNAME}:${env.PASSWORD} \
//              "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/issues?milestone=${milestoneNumber}&per_page=100&state=all"
//     """, returnStdout: true)

    
//     def issues = readJSON(text: response.trim())
//     return issues.findAll { it.pull_request }
// }


import groovy.json.JsonSlurper

def REPO_OWNER = 'KoBrane'
def REPO_NAME = 'jenkis-pytest'
def BRANCH = 'main'

node {
    try {
        stage('Clone Repository') {
            cleanWs()
            checkout([$class: 'GitSCM', 
                branches: [[name: "*/${BRANCH}"]], 
                userRemoteConfigs: [[
                    url: "https://github.com/${REPO_OWNER}/${REPO_NAME}.git",
                    credentialsId: 'god-level-access'
                ]]
            ])
        }
        
        stage('Fetch Milestones') {
            withCredentials([usernamePassword(credentialsId: 'god-level-access', usernameVariable: 'USERNAME', passwordVariable: 'PASSWORD')]) {
                def allMilestones = fetchAllMilestones()
                echo "Fetched Milestones: ${allMilestones}"
                
                def releaseMilestones = filterReleaseMilestones(allMilestones)
                def cabMilestone = findCABMilestone(allMilestones)
                
                env.RELEASE_MILESTONES = groovy.json.JsonOutput.toJson(releaseMilestones)
                env.CAB_MILESTONE = groovy.json.JsonOutput.toJson(cabMilestone ?: [:])
                
                echo "Release Milestones: ${releaseMilestones*.title.join(', ')}"
                echo "CAB Milestone: ${cabMilestone?.title ?: 'Not found'}"
            }
        }
        
        stage('Process Milestones') {
            def releaseMilestones = new JsonSlurper().parseText(env.RELEASE_MILESTONES)
            def cabMilestone = new JsonSlurper().parseText(env.CAB_MILESTONE)
            
            processMilestones(releaseMilestones, 'Release')
            
            if (cabMilestone) {
                processMilestones([cabMilestone], 'CAB')
            } else {
                echo "No CAB milestone found to process"
            }
        }
    } catch (Exception e) {
        currentBuild.result = 'FAILURE'
        throw e
    } finally {
        cleanWs()
    }
}

def fetchAllMilestones() {
    def response = sh(script: """
        curl -s -f -w "\\n%{http_code}" -u ${env.USERNAME}:${env.PASSWORD} \
             "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/milestones?per_page=100&state=all"
    """, returnStdout: true).trim()

    def (content, statusCode) = response.split('\n')
    
    echo "HTTP Status Code: ${statusCode}"
    
    if (statusCode != "200" || content.trim().startsWith('<!DOCTYPE html>')) {
        error "Received unexpected response. Status code: ${statusCode}"
    }
    
    return new JsonSlurper().parseText(content)
}

def filterReleaseMilestones(allMilestones) {
    return allMilestones.findAll { milestone ->
        milestone.title =~ /Release\/.*\sApproved/
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
        curl -s -f -w "\\n%{http_code}" -u ${env.USERNAME}:${env.PASSWORD} \
             "https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/issues?milestone=${milestoneNumber}&per_page=100&state=all"
    """, returnStdout: true).trim()

    def (content, statusCode) = response.split('\n')
    
    echo "HTTP Status Code: ${statusCode}"
    
    if (statusCode != "200" || content.trim().startsWith('<!DOCTYPE html>')) {
        error "Received unexpected response. Status code: ${statusCode}"
    }
    
    def issues = new JsonSlurper().parseText(content)
    return issues.findAll { it.pull_request }
}

// Post-build actions
if (currentBuild.result == 'SUCCESS') {
    build job: 'wils', wait: true
    build job: 'hercules', wait: true
    build job: 'atlas', wait: true
    build job: 'Ama'
}