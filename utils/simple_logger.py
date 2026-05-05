
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, Any, Dict, List
from colorama import init, Fore, Style

init(autoreset=True)


class SimpleLogger:

    def __init__(self, log_dir: str = "logs", log_filename: Optional[str] = None, enable_color: bool = True):
        self.enable_color = enable_color

        if log_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_filename = f"simple_{timestamp}.log"
        else:
            if not log_filename.startswith("simple_"):
                log_filename = f"simple_{log_filename}"

        self.log_path = Path(log_dir) / log_filename
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

        self.log_file = open(self.log_path, 'a', encoding='utf-8')

        init_msg = f"简化日志系统初始化 - 日志文件: {self.log_path}\n"
        init_msg_with_timestamp = self._add_timestamp(init_msg)
        self._write_to_file(init_msg_with_timestamp)
        separator = "=" * 80 + "\n"
        separator_with_timestamp = self._add_timestamp(separator)
        self._write_to_file(separator_with_timestamp)

    def _get_timestamp(self) -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _write_to_file(self, content: str):
        self.log_file.write(content)
        self.log_file.flush()

    def _print_console(self, content: str, color: str = ""):
        if self.enable_color:
            print(f"{color}{content}{Style.RESET_ALL}", end="")
        else:
            print(content, end="")

    def _add_timestamp(self, content: str) -> str:
        timestamp = self._get_timestamp()
        lines = content.split('\n')
        if lines and lines[0].strip():
            lines[0] = f"[{timestamp}] {lines[0]}"
        elif lines and not lines[0].strip() and len(lines) > 1 and lines[1].strip():
            lines[1] = f"[{timestamp}] {lines[1]}"
        return '\n'.join(lines)

    def _format_content(self, content: Any, max_length: int = 500) -> str:
        if content is None:
            return "None"

        if isinstance(content, str):
            formatted = content
        elif isinstance(content, (dict, list)):
            try:
                formatted = json.dumps(content, indent=2, ensure_ascii=False)
            except (TypeError, ValueError):
                formatted = str(content)
        elif hasattr(content, 'model_dump_json'):
            try:
                formatted = content.model_dump_json(indent=2, exclude_none=True)
            except:
                if hasattr(content, 'content'):
                    formatted = str(content.content) if content.content else str(content)
                else:
                    formatted = str(content)
        elif hasattr(content, 'content') and not isinstance(content, type):
            formatted = self._format_content(content.content, max_length=max_length)
        else:
            formatted = str(content)

        if len(formatted) > max_length:
            return formatted[:max_length] + f"\n... (内容过长，已截断，总长度: {len(formatted)} 字符)"

        return formatted

    def log_step_start(self, step: int, max_steps: int):
        header = f"\n{'=' * 80}\n"
        header += f"Step {step}/{max_steps}\n"
        header += f"{'=' * 80}\n"

        self._print_console(header, Fore.CYAN + Style.BRIGHT)
        header_with_timestamp = self._add_timestamp(header)
        self._write_to_file(header_with_timestamp)

    def log_agent_input(self, input_text: str):
        section = "\n[Agent Input]\n"
        section += "-" * 80 + "\n"
        section += f"{self._format_content(input_text)}\n"
        section += "-" * 80 + "\n"

        self._print_console(section, Fore.GREEN + Style.BRIGHT)
        section_with_timestamp = self._add_timestamp(section)
        self._write_to_file(section_with_timestamp)

    def log_agent_output(self, output: Any):
        section = "\n[Agent Output]\n"
        section += "-" * 80 + "\n"
        section += f"{self._format_content(output)}\n"
        section += "-" * 80 + "\n"

        self._print_console(section, Fore.BLUE + Style.BRIGHT)
        section_with_timestamp = self._add_timestamp(section)
        self._write_to_file(section_with_timestamp)

    def log_tool_call(self, tool_name: str, tool_args: Optional[Dict[str, Any]]):
        section = "\n[Tool Call]\n"
        section += "-" * 80 + "\n"
        section += f"Tool: {tool_name}\n"
        if tool_args:
            section += f"Arguments:\n{self._format_content(tool_args, max_length=1000)}\n"
        else:
            section += "Arguments: None\n"
        section += "-" * 80 + "\n"

        self._print_console(section, Fore.YELLOW + Style.BRIGHT)
        section_with_timestamp = self._add_timestamp(section)
        self._write_to_file(section_with_timestamp)

    def log_tool_output(self, tool_name: str, result: Any, error: Optional[bool] = None):
        section = "\n[Tool Output]\n"
        section += "-" * 80 + "\n"
        section += f"Tool: {tool_name}\n"
        if error:
            section += f"Status: ERROR\n"
        else:
            section += f"Status: SUCCESS\n"
        section += f"Result:\n{self._format_content(result, max_length=1000)}\n"
        section += "-" * 80 + "\n"

        color = Fore.RED + Style.BRIGHT if error else Fore.MAGENTA + Style.BRIGHT
        self._print_console(section, color)
        section_with_timestamp = self._add_timestamp(section)
        self._write_to_file(section_with_timestamp)

    def log_tools_summary(self, tools: List[Any]):
        if not tools or len(tools) == 0:
            return

        if len(tools) > 1:
            section = f"\n[Tools Summary] 共 {len(tools)} 个工具调用\n"
            self._print_console(section, Fore.CYAN)
            section_with_timestamp = self._add_timestamp(section)
            self._write_to_file(section_with_timestamp)

    def log_state(self, state: Dict[str, Any], key_fields: Optional[List[str]] = None):
        if key_fields is None:
            key_fields = ["money", "day", "inventory", "price_by_sku", "qty_by_sku"]

        state_summary = {}
        for key in key_fields:
            if key in state:
                value = state[key]
                if isinstance(value, dict):
                    if len(value) == 0:
                        state_summary[key] = "{}"
                    elif len(value) <= 5:
                        state_summary[key] = value
                    else:
                        items = list(value.items())[:3]
                        state_summary[key] = f"{{... {len(value)} items, showing first 3: {dict(items)}}}"
                elif isinstance(value, list):
                    if len(value) == 0:
                        state_summary[key] = "[]"
                    elif len(value) <= 5:
                        state_summary[key] = value
                    else:
                        state_summary[key] = f"[... {len(value)} items, showing first 3: {value[:3]}]"
                else:
                    state_summary[key] = value

        section = "\n[State]\n"
        section += "-" * 80 + "\n"

        simple_fields = ["money", "day"]
        for key in simple_fields:
            if key in state_summary:
                section += f"{key}: {state_summary[key]}\n"

        complex_fields = [k for k in key_fields if k not in simple_fields]
        for key in complex_fields:
            if key in state_summary:
                value_str = self._format_content(state_summary[key], max_length=400)
                section += f"{key}: {value_str}\n"

        section += "-" * 80 + "\n"

        self._print_console(section, Fore.WHITE + Style.BRIGHT)
        section_with_timestamp = self._add_timestamp(section)
        self._write_to_file(section_with_timestamp)

    def close(self):
        footer = "\n" + "=" * 80 + "\n"
        footer += "简化日志结束\n"
        footer += "=" * 80 + "\n"

        self._print_console(footer, Fore.CYAN + Style.BRIGHT)
        footer_with_timestamp = self._add_timestamp(footer)
        self._write_to_file(footer_with_timestamp)

        if self.log_file:
            self.log_file.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

