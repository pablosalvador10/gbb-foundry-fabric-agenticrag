# pip install azure-identity openai==1.70.0

# ---- REQUIRED: paste your Published URL here ----
PUBLISHED_URL = "https://msitapi.fabric.microsoft.com/v1/workspaces/409e30ce-b2ad-4c80-a54d-d645227322e4/aiskills/672fba68-a7d0-4c85-99e9-9ed6fe8ef1d1/aiassistant/openai"

import typing as t
import time, uuid

from azure.identity import InteractiveBrowserCredential
from openai import OpenAI
from openai._models import FinalRequestOptions
from openai._types import Omit
from openai._utils import is_given

# ---------- Dev sign-in ----------
# Opens a browser once; caches token locally
SCOPE = "https://api.fabric.microsoft.com/.default"
# If you see 401/403, swap to:
# SCOPE = "https://analysis.windows.net/powerbi/api/.default"

_cred = InteractiveBrowserCredential()


def _get_bearer() -> str:
    return _cred.get_token(SCOPE).token


class FabricOpenAI(OpenAI):
    """
    OpenAI client wrapper that:
      - Uses your Fabric Data Agent Published URL as base_url
      - Injects AAD Bearer token and correlation id
      - Pins 'api-version' as query param
    """

    def __init__(
        self, api_version: str = "2024-05-01-preview", **kwargs: t.Any
    ) -> None:
        self.api_version = api_version
        default_query = kwargs.pop("default_query", {})
        default_query["api-version"] = self.api_version
        super().__init__(
            api_key="",  # not used
            base_url=PUBLISHED_URL,  # IMPORTANT: your agent endpoint
            default_query=default_query,
            **kwargs,
        )

    def _prepare_options(self, options: FinalRequestOptions) -> None:
        headers: dict[str, str | Omit] = (
            {**options.headers} if is_given(options.headers) else {}
        )
        headers["Authorization"] = f"Bearer {_get_bearer()}"
        headers.setdefault("Accept", "application/json")
        headers.setdefault("ActivityId", str(uuid.uuid4()))
        options.headers = headers
        return super()._prepare_options(options)


client = FabricOpenAI()
print("Client configured. You're signed in with InteractiveBrowserCredential().")


def ask_data_agent(
    question: str, poll_interval_sec: int = 2, timeout_sec: int = 300
) -> str:
    """
    Sends a question to the published Fabric Data Agent and returns the text reply.
    Cleans up the thread after completion.
    """
    # Create "assistant" placeholder (model is ignored by Fabric agent)
    assistant = client.beta.assistants.create(model="not-used")

    # Create a new thread for this Q&A
    thread = client.beta.threads.create()

    try:
        # Post the user message
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=question,
        )

        # Start a run (the data agent actually does the work)
        run = client.beta.threads.runs.create(
            thread_id=thread.id, assistant_id=assistant.id
        )

        # Poll until terminal state or timeout
        terminal = {"completed", "failed", "cancelled", "requires_action"}
        start = time.time()
        while run.status not in terminal:
            if time.time() - start > timeout_sec:
                raise TimeoutError(
                    f"Run polling exceeded {timeout_sec}s (last status={run.status})"
                )
            time.sleep(poll_interval_sec)
            run = client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

        if run.status != "completed":
            return f"[Run ended: {run.status}]"

        # Collect messages in ascending order and concatenate text parts
        msgs = client.beta.threads.messages.list(thread_id=thread.id, order="asc")
        out_chunks = []
        for m in msgs.data:
            if m.role == "assistant":
                for c in m.content:
                    if getattr(c, "type", None) == "text":
                        out_chunks.append(c.text.value)
        return "\n".join(out_chunks).strip() or "[No text content returned]"

    finally:
        # Always attempt cleanup
        try:
            client.beta.threads.delete(thread_id=thread.id)
        except Exception:
            pass


print("Helper ready: call ask_data_agent('your question')")
