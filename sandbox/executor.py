import logging
import time
import uuid

logger = logging.getLogger(__name__)

try:
    from kubernetes import client, config
    from kubernetes.client.rest import ApiException

    K8S_AVAILABLE = True
except ImportError:
    K8S_AVAILABLE = False


class SandboxExecutor:
    """Manages ephemeral Kubernetes namespaces for safe script execution."""

    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode or not K8S_AVAILABLE
        if not self.mock_mode:
            try:
                # Attempt to load in-cluster config, fallback to local kubeconfig
                try:
                    config.load_incluster_config()
                except config.ConfigException:
                    config.load_kube_config()
                self.core_v1 = client.CoreV1Api()
                self.apps_v1 = client.AppsV1Api()
            except Exception as e:
                logger.error(f"Failed to initialize Kubernetes client: {e}")
                self.mock_mode = True

    def spin_up_namespace(self) -> str:
        """Create a temporary namespace in the real Kubernetes cluster."""
        ns_name = f"test-ns-{uuid.uuid4().hex[:8]}"
        if self.mock_mode:
            logger.info(f"[Sandbox] Mock Mode: Created mock namespace '{ns_name}'")
            return ns_name

        logger.info(f"Creating real Kubernetes namespace: {ns_name}")
        ns_metadata = client.V1ObjectMeta(
            name=ns_name, labels={"purpose": "aship-sandbox"}
        )
        ns_body = client.V1Namespace(metadata=ns_metadata)
        try:
            self.core_v1.create_namespace(body=ns_body)
            return ns_name
        except ApiException as e:
            logger.error(f"Failed to create namespace {ns_name}: {e}")
            raise

    def execute_tool(self, tool_name: str, args: dict, namespace: str) -> bool:
        """Execute the requested tool inside the sandbox."""
        logger.info(
            f"[Sandbox] Executing {tool_name} with args {args} in {namespace}..."
        )

        if self.mock_mode:
            time.sleep(1)  # simulate work
            logger.info(f"[Sandbox] Mock Mode: Tool {tool_name} executed successfully.")
            return True

        try:
            if tool_name == "kubectl_restart_pod":
                # Real implementation: delete pod to trigger replicaset recreation
                pod_name = args.get("pod")
                self.core_v1.delete_namespaced_pod(name=pod_name, namespace=namespace)
                return True

            elif tool_name == "kubectl_scale_deployment":
                # Real implementation: patch deployment replicas
                deploy_name = args.get("deployment")
                replicas = args.get("replicas", 2)
                body = {"spec": {"replicas": replicas}}
                self.apps_v1.patch_namespaced_deployment(
                    name=deploy_name, namespace=namespace, body=body
                )
                return True

            else:
                logger.error(f"Unknown tool requested: {tool_name}")
                return False

        except ApiException as e:
            logger.error(f"Kubernetes API Exception during tool execution: {e}")
            return False

    def teardown_namespace(self, namespace: str):
        """Destroy the temporary namespace from the cluster."""
        if self.mock_mode:
            logger.info(f"[Sandbox] Mock Mode: Terminating namespace '{namespace}'")
            return

        logger.info(f"Deleting real Kubernetes namespace: {namespace}")
        try:
            self.core_v1.delete_namespace(name=namespace)
        except ApiException as e:
            logger.error(f"Failed to delete namespace {namespace}: {e}")
