# browser-use Integration Patterns

## When to activate
When working with Agent, BrowserSession, Tools, BrowserProfile, or ChatLiteLLM from the browser-use library.

## Key Patterns

### Creating an LLM instance
```python
from browser_use.llm.litellm.chat import ChatLiteLLM

llm = ChatLiteLLM(
	model="openrouter/anthropic/claude-sonnet-4-20250514",
	api_key=api_key,
	api_base="https://openrouter.ai/api/v1",
)
```

### Registering custom tools
```python
from browser_use.tools import Tools

tools = Tools()

@tools.registry.action("Description of what this tool does")
async def my_tool(param: str) -> str:
	return "result"
```

### Configuring HAR recording
```python
from browser_use.browser.profile import BrowserProfile

profile = BrowserProfile(
	headless=True,
	record_har_path="/path/to/output.har",
)
```

### Creating an Agent
```python
from browser_use import Agent

agent = Agent(
	task="Your task description",
	llm=llm,
	browser_session=session,
	use_vision="auto",
	tools=tools,
)
result = await agent.run()
```

## Reference paths
- Agent API: `reference_repo/browser-use/browser_use/agent/service.py`
- BrowserProfile: `reference_repo/browser-use/browser_use/browser/profile.py`
- Tools: `reference_repo/browser-use/browser_use/tools/service.py`
- ChatLiteLLM: `reference_repo/browser-use/browser_use/llm/litellm/chat.py`
- HAR watchdog: `reference_repo/browser-use/browser_use/browser/watchdogs/har_recording_watchdog.py`
