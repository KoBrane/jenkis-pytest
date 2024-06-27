// pipeline {
//     agent any
    
//     parameters {
//         string(name: 'repo_owner', defaultValue: 'KoBrane', description: 'GitHub repository owner')
//         string(name: 'repo_name', defaultValue: 'jenkis-pytest', description: 'GitHub repository name')
//         string(name: 'milestone_pattern', defaultValue: 'Release/.* Approved|CAB Approved', description: 'Regex pattern to match milestone titles')
//         string(name: 'TARGET_BRANCH', defaultValue: 'main', description: 'Target branch to clone')
//     }
    
//     environment {
//         GITHUB_REPO = "${params.repo_owner}/${params.repo_name}"
//         API_BASE_URL = 'https://api.github.com/repos/'
//     }
    
//     stages {
//         stage('Clone Repository') {
//             steps {
//                 script {
//                     def repoDir = "${params.repo_name}"
//                     if (fileExists(repoDir)) {
//                         echo "Removing existing directory: ${repoDir}"
//                         deleteDir()
//                     }
//                     withCredentials([
//                         usernamePassword(credentialsId: 'wils-new',
//                             usernameVariable: 'USERNAME',
//                             passwordVariable: 'GITHUB_TOKEN')
//                     ]) {
//                         sh "git clone --branch ${params.TARGET_BRANCH} --depth 1 https://${USERNAME}:${GITHUB_TOKEN}@github.com/${params.repo_owner}/${params.repo_name}.git"
//                     }
//                 }
//             }
//         }
        
//         stage('Fetch Milestones and PRs') {
//             steps {
//                 script {
//                     withCredentials([
//                         usernamePassword(credentialsId: 'wils-new',
//                             usernameVariable: 'USERNAME',
//                             passwordVariable: 'GITHUB_TOKEN')
//                     ]) {
//                         try {
//                             // Fetch milestones matching the combined pattern
//                             def milestones = fetchMilestones(params.milestone_pattern)
                        
//                             milestones.each { milestone ->
//                                 def milestoneTitle = milestone.title
//                                 def milestoneNumber = milestone.number
//                                 echo "Checking milestone: ${milestoneTitle} (Number: ${milestoneNumber})"
                            
//                                 def prs = fetchPRsForMilestone(milestoneNumber)
                            
//                                 if (prs.isEmpty()) {
//                                   echo "Milestone '${milestoneTitle}' has no associated PRs."
//                                 } else {
//                                     echo "Milestone '${milestoneTitle}' PRs:"
//                                     prs.each { pr ->
//                                         echo "- ${pr.title} (${pr.html_url})"
//                                     }
//                                 }
//                             }
//                         } catch (Exception e) {
//                             error "Error fetching milestones and PRs: ${e.message}"
//                         }
//                     }
//                 }
//             }
//         }
//     }
// }

// def fetchMilestones(milestonePattern) {
//     def milestones = []
//     def pageNumber = 1
    
//     while (true) {
//         def milestonesUrl = "${env.API_BASE_URL}${env.GITHUB_REPO}/milestones?page=${pageNumber}&per_page=100"
//         def response = sh(
//             script: "curl -s -H 'Authorization: Bearer ${env.GITHUB_TOKEN}' '${milestonesUrl}'",
//             returnStdout: true
//         )
        
//         def pageData = readJSON(text: response)
//         def matchingMilestones = pageData.findAll { it.title =~ milestonePattern }
//         milestones.addAll(matchingMilestones)
        
//         if (pageData.size() < 100) {
//             break
//         } else {
//             pageNumber++
//         }
//     }
    
//     return milestones
// }

// def fetchPRsForMilestone(milestoneNumber) {
//     def prs = []
//     def pageNumber = 1
    
//     while (true) {
//         def prsUrl = "${env.API_BASE_URL}${env.GITHUB_REPO}/issues?page=${pageNumber}&per_page=100&state=all&milestone=${milestoneNumber}"
        
//         def response = sh(
//             script: "curl -s -H 'Authorization: Bearer ${env.GITHUB_TOKEN}' '${prsUrl}'",
//             returnStdout: true
//         )
        
//         def pageData = readJSON(text: response)
//         def filteredPRs = pageData.findAll { it.pull_request && it.milestone?.number == milestoneNumber }
//         prs.addAll(filteredPRs)
        
//         if (pageData.size() < 100) {
//             break
//         } else {
//             pageNumber++
//         }
//     }
    
//     return prs
// }


pipeline {
    agent any

    triggers {
        cron('H/10 * * * 1-5')
    }
    
    parameters {
        string(name: 'TRIES', defaultValue: '3', description: 'How many attempts are allowed')
    }
    
    stages {
        stage('Initialize') {
            steps {
                script {
                    echo 'Starting auto_release...'
                    env.MAX_TRIES = params.TRIES.toInteger()
                }
            }
        }
        
        stage('Check for PRs') {
            steps {
                script {
                    while (true) {
                        try {
                            env.AVAILABLE_PRS = sh(script: 'python3 -c "import milestone as rp; print(rp.check_pr())"', returnStdout: true).trim()
                            
                            if (env.AVAILABLE_PRS == '[]' || env.AVAILABLE_PRS == '') {
                                echo "No PRs found... sleeping"
                                sleep(time: 60, unit: 'SECONDS')
                                continue
                            }
                            break
                        } catch (Exception e) {
                            error("Error checking PRs: ${e.getMessage()}")
                        }
                    }
                }
            }
        }
        
        stage('Process PR') {
            steps {
                script {
                    sh 'git pull'
                    
                    env.PR = env.AVAILABLE_PRS.split(',')[0].replaceAll("[\\[\\]]", "").trim()
                    echo "Running PR: ${env.PR}"
                    
                    env.CMD = "python3 milestone.py ${env.PR} --auto --onlynew"
                }
            }
        }
        
        stage('Run Process') {
            steps {
                script {
                    for (int count = 0; count <= env.MAX_TRIES.toInteger(); count++) {
                        if (count == env.MAX_TRIES.toInteger()) {
                            error("Max retries reached. Exiting.")
                        }
                        
                        try {
                            sh env.CMD
                            echo "Process completed successfully"
                            break
                        } catch (Exception e) {
                            echo "Attempt ${count + 1} failed. Retrying..."
                            sleep(time: 60, unit: 'SECONDS')
                            env.CMD = "sleep 10 && echo 'y' | python3 milestone.py ${env.PR} --auto"
                        }
                    }
                }
            }
        }
    }
    
    // post {
    //     failure {
    //         script {
    //             sh "python3 -c 'import slack; slack.main([\"--prmilestone\", \"${env.PR}\", \"--fail\"])'"
    //         }
    //     }
    // }
}