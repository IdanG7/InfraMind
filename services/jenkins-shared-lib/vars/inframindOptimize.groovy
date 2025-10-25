/**
 * Get optimization suggestions from InfraMind API
 *
 * Usage:
 *   inframindOptimize(params: [tool: 'cmake', repo: 'org/app'])
 */
def call(Map config = [:]) {
    def apiUrl = env.INFRA_API ?: 'http://inframind-api.infra.svc.cluster.local:8080'
    def pipeline = env.INFRA_PIPELINE ?: "${env.JOB_NAME}/${env.BUILD_NUMBER}"
    def apiKey = env.INFRA_API_KEY ?: 'dev-key-change-in-production'

    echo "[InfraMind] Requesting optimizations for ${pipeline}"

    def payload = [
        pipeline: pipeline,
        run_id: env.BUILD_ID,
        context: [
            tool: config.tool ?: 'unknown',
            repo: config.repo ?: env.GIT_URL ?: 'unknown',
            branch: env.BRANCH_NAME ?: env.GIT_BRANCH ?: 'main',
            image: config.image ?: 'default',
            last_success: config.last_success ?: [:]
        ],
        constraints: config.constraints ?: [:]
    ]

    try {
        def response = httpRequest(
            url: "${apiUrl}/optimize",
            httpMode: 'POST',
            contentType: 'APPLICATION_JSON',
            customHeaders: [[name: 'X-IM-Token', value: apiKey]],
            requestBody: groovy.json.JsonOutput.toJson(payload),
            validResponseCodes: '200'
        )

        def result = new groovy.json.JsonSlurper().parseText(response.content)

        echo "[InfraMind] Suggestions received (confidence: ${result.confidence})"
        echo "[InfraMind] ${result.rationale}"

        // Apply suggestions as environment variables
        def suggestions = result.suggestions
        env.IM_CONCURRENCY = suggestions.concurrency?.toString() ?: '4'
        env.IM_CPU_REQUEST = suggestions.cpu_req?.toString() ?: '4'
        env.IM_MEM_REQUEST_GB = suggestions.mem_req_gb?.toString() ?: '8'
        env.IM_CACHE_ENABLED = suggestions.cache?.ccache?.toString() ?: 'true'
        env.IM_CACHE_SIZE_GB = suggestions.cache?.size_gb?.toString() ?: '10'

        echo "[InfraMind] Applied: concurrency=${env.IM_CONCURRENCY}, " +
             "cpu=${env.IM_CPU_REQUEST}, mem=${env.IM_MEM_REQUEST_GB}GB, " +
             "cache=${env.IM_CACHE_ENABLED}"

        return result

    } catch (Exception e) {
        echo "[InfraMind] WARNING: Failed to get optimizations: ${e.message}"
        echo "[InfraMind] Continuing with defaults"

        // Set defaults
        env.IM_CONCURRENCY = '4'
        env.IM_CPU_REQUEST = '4'
        env.IM_MEM_REQUEST_GB = '8'
        env.IM_CACHE_ENABLED = 'true'
        env.IM_CACHE_SIZE_GB = '10'

        return null
    }
}
