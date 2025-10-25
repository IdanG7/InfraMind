/**
 * Notify build completion to InfraMind
 *
 * Usage:
 *   post {
 *     always { inframindNotify() }
 *   }
 */
def call(Map config = [:]) {
    def apiUrl = env.INFRA_API ?: 'http://inframind-api.infra.svc.cluster.local:8080'
    def apiKey = env.INFRA_API_KEY ?: 'dev-key-change-in-production'
    def pipeline = env.INFRA_PIPELINE ?: "${env.JOB_NAME}/${env.BUILD_NUMBER}"

    echo "[InfraMind] Notifying build completion"

    // Determine build status
    def status = currentBuild.result ?: 'SUCCESS'
    def statusMap = [
        'SUCCESS': 'success',
        'FAILURE': 'failure',
        'ABORTED': 'aborted',
        'UNSTABLE': 'failure'
    ]

    // Calculate duration
    def durationMs = currentBuild.duration ?: 0
    def durationS = durationMs / 1000.0

    // Collect artifacts info (if any)
    def artifacts = []
    try {
        def artifactFiles = currentBuild.rawBuild.getArtifacts()
        artifactFiles.each { artifact ->
            artifacts << [
                name: artifact.getFileName(),
                size: artifact.getFileSize()
            ]
        }
    } catch (Exception e) {
        echo "[InfraMind] Could not collect artifacts: ${e.message}"
    }

    // Build cache stats (placeholder)
    def cache = [
        ccache_enabled: env.IM_CACHE_ENABLED == 'true',
        size_gb: env.IM_CACHE_SIZE_GB?.toInteger() ?: 0
    ]

    def payload = [
        run_id: env.BUILD_ID,
        status: statusMap[status] ?: 'failure',
        duration_s: durationS,
        artifacts: artifacts,
        cache: cache
    ]

    try {
        httpRequest(
            url: "${apiUrl}/builds/complete",
            httpMode: 'POST',
            contentType: 'APPLICATION_JSON',
            customHeaders: [[name: 'X-IM-Token', value: apiKey]],
            requestBody: groovy.json.JsonOutput.toJson(payload),
            validResponseCodes: '200'
        )

        echo "[InfraMind] Build completion reported: ${status} in ${durationS}s"

    } catch (Exception e) {
        echo "[InfraMind] WARNING: Failed to notify completion: ${e.message}"
    }
}
