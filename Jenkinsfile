@Library('jenkins-shared-libraries') _
def ENV_LOC=[:]
pipeline {
    parameters {
        choice(name: 'PLATFORM_FILTER', choices: ['all', 'windows-dotnet-framework-samples'], description: 'Run on specific platform')
        booleanParam defaultValue: false, description: 'Completely clean the workspace before building', name: 'CLEAN_WORKSPACE'
        booleanParam defaultValue: false, description: 'Run clean-samples', name: 'DISTCLEAN'
        booleanParam defaultValue: true, description: 'Run clean-nuget-cache', name: 'NUGETCLEAN'
    }
    options{
        buildDiscarder logRotator(artifactDaysToKeepStr: '4', artifactNumToKeepStr: '10', daysToKeepStr: '7', numToKeepStr: '10')
        disableConcurrentBuilds()
        timeout(time: 4, unit: "HOURS")
    }
    agent none
    triggers {
        // .NET Framework samples are Windows-only. Run after the nuget-builder
        // nightly (~05:00, ~20 min) has uploaded packages to the raid.
        cron(env.BRANCH_NAME == "develop-21" ? 'H(0-30) 8 * * *' : '')
    }
    stages {
        stage('Matrix stage') {
            matrix {
                agent {
                    label "${NODE}"
                }
                when { anyOf {
                    expression { params.PLATFORM_FILTER == 'all' }
                    expression { params.PLATFORM_FILTER == env.NODE }
                } }
                axes {
                    axis {
                        name 'NODE'
                        values 'windows-dotnet-framework-samples'
                    }
                }
                stages {
                    stage('Axis'){
                        steps {
                            printPlatformNameInStep()
                        }
                    }
                    stage('Clean/reset Git checkout for release') {
                        when {
                            expression {
                                params.CLEAN_WORKSPACE
                            }
                        }
                        steps {
                            echo "Clean ${NODE}"
                            bat """
                                  git rm -q -r .
                                  git reset --hard HEAD
                                  git clean -fdx
                            """
                        }
                    }
                    stage('Set-Up Environment') {
                        steps {
                            echo "Set-Up Environment ${NODE}"
                            script {
                                // Assumes the Python Launcher is installed on the Windows host.
                                bat '.\\mkenv.py --verbose'
                                ENV_LOC[NODE] = bat (
                                    // The @ prevents Windows from echoing the command itself,
                                    // which would corrupt the returned value.
                                    script: '@.\\mkenv.py --env-name',
                                    returnStdout: true
                                ).trim()
                            }
                        }
                    }
                    stage('Clean Samples') {
                        steps {
                            echo "Clean ${NODE}"
                            bat """CALL ${ENV_LOC[NODE]}\\Scripts\\activate
                                  invoke clean-samples
                            """
                        }
                    }
                    stage('Clean Nuget Cache') {
                        when {
                            expression {
                                params.NUGETCLEAN
                            }
                        }
                        steps {
                            echo "Clean ${NODE}"
                            bat """CALL ${ENV_LOC[NODE]}\\Scripts\\activate
                                  invoke clean-nuget-cache
                            """
                        }
                    }
                    stage('Build Samples') {
                        steps {
                            echo "Build the samples ${NODE}"
                            bat """CALL ${ENV_LOC[NODE]}\\Scripts\\activate
                                  invoke build-samples
                            """
                        }
                    }
                    stage('Run Samples') {
                        steps {
                            echo "Run the samples ${NODE}"
                            bat """CALL ${ENV_LOC[NODE]}\\Scripts\\activate
                                  invoke run-samples
                            """
                        }
                    }
                    stage('Clean Samples After Run') {
                        steps {
                            echo "Clean ${NODE}"
                            bat """CALL ${ENV_LOC[NODE]}\\Scripts\\activate
                                  invoke clean-samples
                            """
                        }
                    }
                }
            }
        }
    }
}
