package aship.policy

default allow_remediation = false

# Allow remediation ONLY if:
# 1. Action is approved in the known catalog
# 2. Confidence score from the Bayesian model is >= 0.90
# 3. Environment is explicitly targeted and allowed
allow_remediation {
    valid_remediation_action
    high_confidence
    authorized_namespace
}

valid_remediation_action {
    allowed_actions := {"kubectl_restart_pod", "istio_traffic_shift", "postgres_kill_idle_connections", "iam_policy_sync", "auto_remediation_workflow"}
    input.proposed_action.tool_name == allowed_actions[_]
}

high_confidence {
    input.confidence >= 0.90
}

authorized_namespace {
    allowed_namespaces := {"prod", "staging", "aship-sandbox"}
    input.proposed_action.arguments.namespace == allowed_namespaces[_]
}

# Explicitly deny destructive actions
deny_destructive_action {
    destructive_actions := {"delete_cluster", "drop_database", "remove_iam_role"}
    input.proposed_action.tool_name == destructive_actions[_]
}
