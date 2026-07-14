@Library('jenkins-shared-libraries') _
def ENV_LOC=[:]

// Per-job NuGet cache root, so concurrent jobs on a node don't contend for
// the shared per-user cache. Rooted at the drive root (like setConanHome)
// to keep restored package paths under the Windows long-path limit.
def setNugetRoot() {
    def jobDirectory = "DL\\" + env.JOB_NAME.tokenize('/')[-2] + "_" + env.JOB_BASE_NAME
    return getWindowsRootDrive() + jobDirectory + "\\.nuget"
}

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
        cron(env.BRANCH_NAME == "develop-21" ? '30 5 * * *' : '')
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
                environment {
                    APDFL_KEY = credentials('apdfl-rlm-key')
                    // NuGet honors these for restore, msbuild, and
                    // 'nuget locals all -clear' alike.
                    NUGET_ROOT = setNugetRoot()
                    NUGET_PACKAGES = "${NUGET_ROOT}\\packages"
                    NUGET_HTTP_CACHE_PATH = "${NUGET_ROOT}\\http-cache"
                    NUGET_PLUGINS_CACHE_PATH = "${NUGET_ROOT}\\plugins-cache"
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
                            // The NuGet cache root lives outside the workspace,
                            // so git clean can't remove it.
                            bat """
                                  if exist "%NUGET_ROOT%" rmdir /s /q "%NUGET_ROOT%"
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
