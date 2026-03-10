package aship.safety

import future.keywords.in

# Default deny
default allow = false

# Allow if the action is in the permitted lists and passes all constraints
allow {
    valid_tool
    safe_namespace
    valid_justification
}

# The agent is only allowed to execute predefined sandboxed tools. Direct arbitrary execution is forbidden.
permitted_tools = {
    "kubectl_restart_pod",
    "kubectl_scale_deployment",
    "helm_rollback",
    "drain_node"
}

valid_tool {
    input.tool_name in permitted_tools
}

# ----------------------------------------------------
# Namespaces:
# AI cannot modify certain critical namespaces directly.
# ----------------------------------------------------
protected_namespaces = {
    "kube-system",
    "vault",
    "opa"
}

safe_namespace {
    # If a namespace is provided in arguments, it must not be in the protected list
    not protected_namespaces[input.arguments.namespace]
}

# ----------------------------------------------------
# Hallucination Guardrails
# ----------------------------------------------------
# Agent must provide a justification that is non-empty and cites a log
valid_justification {
    input.justification != ""
    contains(input.justification, "Log line")
}

# ----------------------------------------------------
# Confidence Threshold (redundant check on top of Python)
# ----------------------------------------------------
allow {
    valid_tool
    safe_namespace
    valid_justification
    input.confidence >= 0.90
}
