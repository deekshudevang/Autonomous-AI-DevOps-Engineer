import logging

from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_telemetry(service_name: str = "aship-agent-core"):
    """Initialize OpenTelemetry tracer with Jaeger Exporter."""
    resource = Resource(attributes={SERVICE_NAME: service_name})

    trace_provider = TracerProvider(resource=resource)

    # For a real implementation, connect to Jaeger agent.
    # Mocking exporter here for standalone execution
    try:
        jaeger_exporter = JaegerExporter(
            agent_host_name="localhost",
            agent_port=6831,
        )
        processor = BatchSpanProcessor(jaeger_exporter)
        trace_provider.add_span_processor(processor)
    except Exception:
        logging.warning("Jaeger exporter failed to initialize, traces will be dropped.")

    trace.set_tracer_provider(trace_provider)
    return trace.get_tracer(__name__)


# Usage Example:
# tracer = setup_telemetry()
# with tracer.start_as_current_span("agent_reasoning"):
#     pass
