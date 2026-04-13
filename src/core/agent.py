import json
import os
from dataclasses import dataclass

from openai import OpenAI

from src.core.tool import Tool


@dataclass
class AgentResult:
    content: str
    messages: list[dict]


class Agent:
    def __init__(
        self,
        name: str,
        system_prompt: str,
        tools: list[Tool],
        model: str = "hermes3:8b",
        max_iterations: int = 20,
        terminal_tool: str | None = None,
        forced_tool_calls: list[dict] | None = None,
    ):
        """
        forced_tool_calls: if provided, these tool calls are executed upfront before
        asking the LLM to synthesize. Each entry: {"name": "tool_name", "args": {...}}.
        Use this with smaller models that don't reliably self-direct multi-step tool sequences.
        """
        self.name = name
        self.tools = tools
        self.model = model
        self.max_iterations = max_iterations
        self.tool_map: dict[str, Tool] = {t.name: t for t in tools}
        self.terminal_tool = terminal_tool
        self.forced_tool_calls = forced_tool_calls or []
        self.system_prompt = system_prompt

        llm_url = os.environ.get("LLM_URL", "http://localhost:11434")
        api_key = os.environ.get("LLM_API_KEY", "ollama")
        self.client = OpenAI(base_url=f"{llm_url}/v1", api_key=api_key)

        self._tool_defs = [t.to_openai_schema() for t in tools] if tools else []

    def _execute_forced_calls(self) -> tuple[list[dict], list[dict]]:
        """Run forced_tool_calls upfront. Returns (assistant_msgs, tool_result_msgs)."""
        tool_calls_payload = []
        tool_result_msgs = []

        for i, call in enumerate(self.forced_tool_calls):
            fn_name = call["name"]
            fn_args = call.get("args", {})
            tc_id = f"forced_{i}"

            print(f"[{self.name}] Calling {fn_name}({fn_args})")

            tool = self.tool_map.get(fn_name)
            if tool is None:
                result_str = f"Error: tool '{fn_name}' not found."
            else:
                try:
                    raw = tool.fn(**fn_args)
                    result_str = raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False)
                except Exception as e:
                    result_str = f"Error executing {fn_name}: {e}"

            tool_calls_payload.append({
                "id": tc_id,
                "type": "function",
                "function": {"name": fn_name, "arguments": json.dumps(fn_args)},
            })
            tool_result_msgs.append({
                "role": "tool",
                "tool_call_id": tc_id,
                "content": result_str,
            })

        assistant_msg = {"role": "assistant", "content": "", "tool_calls": tool_calls_payload}
        return [assistant_msg], tool_result_msgs

    def run(self, context: str) -> AgentResult:
        print(f"[{self.name}] Starting run...")

        messages: list[dict] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": context},
        ]

        # Pre-execute forced tool calls and inject results before asking for synthesis
        if self.forced_tool_calls:
            asst_msgs, result_msgs = self._execute_forced_calls()
            messages.extend(asst_msgs)
            messages.extend(result_msgs)
            messages.append({
                "role": "user",
                "content": "All required data has been gathered. Write your final report now.",
            })
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.2,
                max_tokens=2048,
            )
            content = response.choices[0].message.content or ""
            print(f"[{self.name}] Done.")
            return AgentResult(content=content, messages=messages)

        # LLM-directed tool calling (for capable models)
        call_kwargs: dict = {
            "model": self.model,
            "temperature": 0.2,
            "max_tokens": 2048,
        }
        if self._tool_defs:
            call_kwargs["tools"] = self._tool_defs
            call_kwargs["tool_choice"] = "auto"

        called_tool_names: set[str] = set()

        for _ in range(self.max_iterations):
            response = self.client.chat.completions.create(
                messages=messages, **call_kwargs
            )
            choice = response.choices[0]
            msg = choice.message

            assistant_msg: dict = {"role": "assistant", "content": msg.content or ""}
            if msg.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]
            messages.append(assistant_msg)

            if msg.tool_calls:
                for tc in msg.tool_calls:
                    fn_name = tc.function.name
                    try:
                        fn_args = json.loads(tc.function.arguments)
                    except Exception:
                        fn_args = {}

                    print(f"[{self.name}] Calling {fn_name}({fn_args})")
                    called_tool_names.add(fn_name)

                    tool = self.tool_map.get(fn_name)
                    if tool is None:
                        result_str = f"Error: tool '{fn_name}' not found."
                    else:
                        try:
                            raw = tool.fn(**fn_args)
                            result_str = raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False)
                        except Exception as e:
                            result_str = f"Error executing {fn_name}: {e}"

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": result_str,
                    })

                if self.terminal_tool and self.terminal_tool in called_tool_names:
                    call_kwargs["tool_choice"] = "none"

                continue

            print(f"[{self.name}] Done.")
            return AgentResult(content=msg.content or "", messages=messages)

        return AgentResult(content="[Error: max iterations reached]", messages=messages)
