from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.metrics import get_meter_provider
from datetime import datetime

class LLMTelemetry:
    def __init__(self, service_name="llm-service"):
        self.tracer = trace.get_tracer(service_name)
        self.meter = get_meter_provider().get_meter(service_name)
        
        # Create metrics
        self.llm_request_counter = self.meter.create_counter(
            "llm.requests",
            description="Number of LLM requests",
            unit="1"
        )
        
        self.llm_latency = self.meter.create_histogram(
            "llm.latency",
            description="Latency of LLM requests",
            unit="ms"
        )
    
    def instrument_llm_call(self, prompt, model="gpt-3.5-turbo"):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                start_time = datetime.now()
                
                with self.tracer.start_as_current_span(
                    "llm_request",
                    attributes={
                        "llm.prompt": prompt,
                        "llm.model": model,
                    }
                ) as span:
                    try:
                        # Execute the LLM call
                        result = await func(*args, **kwargs)
                        
                        # Record successful completion
                        span.set_status(Status(StatusCode.OK))
                        
                        # Add response to span
                        span.set_attribute("llm.response", str(result))
                        
                        return result
                    
                    except Exception as e:
                        # Record error
                        span.set_status(
                            Status(StatusCode.ERROR, str(e))
                        )
                        span.record_exception(e)
                        raise
                    finally:
                        # Record metrics
                        end_time = datetime.now()
                        duration = (end_time - start_time).total_seconds() * 1000
                        
                        self.llm_request_counter.add(
                            1,
                            {
                                "model": model,
                                "status": "success" if span.status.status_code == StatusCode.OK else "error"
                            }
                        )
                        
                        self.llm_latency.record(
                            duration,
                            {"model": model}
                        )
            
            return wrapper
        return decorator