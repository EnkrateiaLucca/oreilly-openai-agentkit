"""Managed, Responses, and SDK are alternative runtimes with distinct state."""

from course.runtimes.base import ResearchRuntime


def make_runtime(name, settings=None, toolbox=None, client=None) -> ResearchRuntime:
    from course.config import Settings
    from course.runtimes.managed import ManagedRuntime
    from course.runtimes.offline import OfflineRuntime
    from course.runtimes.responses import ResponsesRuntime
    from course.runtimes.sdk import SDKRuntime
    from course.tools import ToolBox

    settings = settings or Settings()
    toolbox = toolbox or ToolBox(max_calls=settings.max_tool_calls)
    cls = {
        "offline": OfflineRuntime,
        "responses": ResponsesRuntime,
        "sdk": SDKRuntime,
        "managed": ManagedRuntime,
    }[name]
    return cls(settings, toolbox, client=client)
