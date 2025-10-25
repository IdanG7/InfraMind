/**
 * Wrap a build stage with InfraMind telemetry
 *
 * Usage:
 *   inframindStage(name: 'compile') {
 *     sh 'make build'
 *   }
 */
def call(Map config = [:], Closure body) {
    def apiUrl = env.INFRA_API ?: 'http://inframind-api.infra.svc.cluster.local:8080'
    def pipeline = env.INFRA_PIPELINE ?: "${env.JOB_NAME}/${env.BUILD_NUMBER}"
    def apiKey = env.INFRA_API_KEY ?: 'dev-key-change-in-production'
    def stageName = config.name ?: config.stage ?: 'unknown'
    def spanId = "${env.BUILD_ID}-${stageName}-${System.currentTimeMillis()}"

    echo "[InfraMind] Starting stage: ${stageName}"

    // Notify start
    def startTime = System.currentTimeMillis()
    notifyStepEvent(apiUrl, apiKey, env.BUILD_ID, stageName, spanId, 'start', [:])

    def result = null
    def counters = [:]

    try {
        // Execute stage body
        result = body()

        // Collect basic counters (extend with real metrics in production)
        counters = [
            cpu_time_s: (System.currentTimeMillis() - startTime) / 1000.0,
            rss_max_bytes: 0, // Would come from C++ agent
            io_r_bytes: 0,
            io_w_bytes: 0,
            cache_hits: 0,
            cache_misses: 0
        ]

    } catch (Exception e) {
        counters = [error: e.message]
        throw e

    } finally {
        // Notify stop
        notifyStepEvent(apiUrl, apiKey, env.BUILD_ID, stageName, spanId, 'stop', counters)

        def duration = (System.currentTimeMillis() - startTime) / 1000.0
        echo "[InfraMind] Stage ${stageName} completed in ${duration}s"
    }

    return result
}

def notifyStepEvent(apiUrl, apiKey, runId, stage, spanId, event, counters) {
    def payload = [
        run_id: runId,
        stage: stage,
        step: stage,
        span_id: spanId,
        event: event,
        timestamp: new Date().format("yyyy-MM-dd'T'HH:mm:ss.SSS'Z'"),
        counters: counters
    ]

    try {
        httpRequest(
            url: "${apiUrl}/builds/step",
            httpMode: 'POST',
            contentType: 'APPLICATION_JSON',
            customHeaders: [[name: 'X-IM-Token', value: apiKey]],
            requestBody: groovy.json.JsonOutput.toJson(payload),
            validResponseCodes: '200',
            quiet: true
        )
    } catch (Exception e) {
        echo "[InfraMind] WARNING: Failed to notify ${event}: ${e.message}"
    }
}
