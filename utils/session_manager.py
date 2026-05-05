import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional


class SessionManager:

    def __init__(self, session_id: str, base_dir: str = "logs/sessions"):
        self.logger = logging.getLogger("agno_stimulation")
        self.session_id = session_id
        self.base_dir = Path(base_dir)
        self.session_dir = self.base_dir / session_id

        self.session_dir.mkdir(parents=True, exist_ok=True)

        self.metadata_file = self.session_dir / "metadata.json"
        self.steps_file = self.session_dir / "steps.jsonl"
        self.state_file = self.session_dir / "state.json"

        self.logger.info(f"会话管理器初始化 - Session ID: {session_id}")
        self.logger.info(f"会话目录: {self.session_dir}")

    def init_session(self, config: Dict[str, Any], initial_state: Dict[str, Any]) -> None:
        metadata = {
            "session_id": self.session_id,
            "start_time": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
            "last_step": 0,
            "total_steps": 0,
            "status": "running",
            "config": config,
            "initial_state": initial_state
        }

        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        self.save_state(initial_state, step=0)

        self.logger.info(f"会话初始化完成 - 元数据已保存到: {self.metadata_file}")

    def save_step(self, step_data: Dict[str, Any]) -> None:
        step_data['timestamp'] = datetime.now().isoformat()

        with open(self.steps_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(step_data, ensure_ascii=False) + '\n')

        self._update_metadata(step_data['step'], step_data.get('is_finished', False))

        self.logger.debug(f"Step {step_data['step']} 数据已保存")

    def save_state(self, state: Dict[str, Any], step: int) -> None:
        state_snapshot = {
            "step": step,
            "timestamp": datetime.now().isoformat(),
            "state": state
        }

        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(state_snapshot, f, ensure_ascii=False, indent=2)

        self.logger.debug(f"状态已保存 - Step {step}")

    def _update_metadata(self, step: int, is_finished: bool = False) -> None:
        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        metadata['last_step'] = step
        metadata['total_steps'] = step
        metadata['last_update'] = datetime.now().isoformat()
        if is_finished:
            metadata['status'] = 'completed'

        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    def mark_interrupted(self) -> None:
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            metadata['status'] = 'interrupted'
            metadata['interrupted_time'] = datetime.now().isoformat()

            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            self.logger.info("会话已标记为中断状态")

    def mark_completed(self) -> None:
        if self.metadata_file.exists():
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            metadata['status'] = 'completed'
            metadata['completed_time'] = datetime.now().isoformat()

            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            self.logger.info("会话已标记为完成状态")

    def update_cost_info(
        self,
        total_input_tokens: int,
        total_output_tokens: int,
        total_cost: float,
        model_name: str,
        pricing: Optional[Dict[str, float]] = None
    ) -> None:
        if not self.metadata_file.exists():
            return

        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        metadata['cost_info'] = {
            'total_input_tokens': total_input_tokens,
            'total_output_tokens': total_output_tokens,
            'total_tokens': total_input_tokens + total_output_tokens,
            'total_cost': total_cost,
            'model_name': model_name,
        }

        if pricing:
            metadata['cost_info']['pricing'] = pricing

        metadata['last_update'] = datetime.now().isoformat()

        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        self.logger.debug(f"成本信息已更新到元数据: Total Cost = ${total_cost:.6f}")

    def update_final_metrics(self, metrics: Dict[str, Any]) -> None:
        if not self.metadata_file.exists():
            return

        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        metadata['final_metrics'] = metrics

        metadata['last_update'] = datetime.now().isoformat()

        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

        self.logger.info(f"最终评估指标已保存到元数据")
        self.logger.debug(f"Final metrics: {metrics}")

    def load_metadata(self) -> Optional[Dict[str, Any]]:
        if not self.metadata_file.exists():
            return None

        with open(self.metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_state(self) -> Optional[Dict[str, Any]]:
        if not self.state_file.exists():
            return None

        with open(self.state_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_all_steps(self) -> List[Dict[str, Any]]:
        if not self.steps_file.exists():
            return []

        steps = []
        with open(self.steps_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    steps.append(json.loads(line))

        return steps

    def can_resume(self) -> bool:
        metadata = self.load_metadata()
        if not metadata:
            return False

        status = metadata.get('status', '')
        return status in ['interrupted', 'running']

    def get_resume_info(self) -> Optional[Dict[str, Any]]:
        if not self.can_resume():
            return None

        metadata = self.load_metadata()
        state_snapshot = self.load_state()

        if not metadata or not state_snapshot:
            return None

        actual_completed_step = state_snapshot.get('step', 0)
        metadata_last_step = metadata.get('last_step', 0)

        if actual_completed_step != metadata_last_step:
            self.logger.info(
                f"Resume: state.json step ({actual_completed_step}) differs from "
                f"metadata.json last_step ({metadata_last_step}). "
                f"Using state.json step as it represents the fully saved state."
            )

        return {
            'last_step': actual_completed_step,
            'state': state_snapshot['state'],
            'metadata': metadata,
            'session_id': self.session_id
        }

    @staticmethod
    def list_resumable_sessions(base_dir: str = "logs/sessions") -> List[Dict[str, Any]]:
        base_path = Path(base_dir)
        if not base_path.exists():
            return []

        resumable = []
        for session_dir in base_path.iterdir():
            if session_dir.is_dir():
                metadata_file = session_dir / "metadata.json"
                if metadata_file.exists():
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)

                    status = metadata.get('status', '')
                    if status in ['interrupted', 'running']:
                        resumable.append({
                            'session_id': session_dir.name,
                            'metadata': metadata
                        })

        resumable.sort(key=lambda x: x['metadata'].get('last_update', ''), reverse=True)
        return resumable

