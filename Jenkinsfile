pipeline {
    agent { label 'windows-dotnet-framework-samples' }
    options {
        disableConcurrentBuilds()
        timeout(time: 1, unit: 'HOURS')
    }
    stages {
        stage('Verify agent') {
            steps {
                echo "Running .NET Framework samples CI on ${NODE_NAME}"
                bat 'msbuild -version'
                bat 'nuget help | findstr /B /C:"NuGet Version:"'
            }
        }
    }
}
