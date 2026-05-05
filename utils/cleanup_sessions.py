
import json
import shutil
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional


def get_session_step(session_dir: Path) -> Optional[int]:
    state_file = session_dir / "state.json"

    if not state_file.exists():
        return None

    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            state_data = json.load(f)

        step = state_data.get('step')
        if step is not None:
            return int(step)

        return None
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        print(f"警告: 无法读取 {state_file}: {e}")
        return None


def list_sessions(base_dir: str = "logs/sessions") -> List[Dict[str, Any]]:
    base_path = Path(base_dir)
    if not base_path.exists():
        return []

    sessions = []
    for session_dir in base_path.iterdir():
        if session_dir.is_dir():
            step = get_session_step(session_dir)
            sessions.append({
                'session_id': session_dir.name,
                'step': step,
                'path': session_dir
            })

    return sessions


def cleanup_sessions(
    base_dir: str = "logs/sessions",
    min_step: int = 100,
    dry_run: bool = False
) -> Dict[str, Any]:
    sessions = list_sessions(base_dir)

    to_delete = []
    to_keep = []
    no_step_info = []

    for session in sessions:
        if session['step'] is None:
            no_step_info.append(session)
        elif session['step'] < min_step:
            to_delete.append(session)
        else:
            to_keep.append(session)

    print(f"\n会话统计:")
    print(f"  总会话数: {len(sessions)}")
    print(f"  将保留 (step >= {min_step}): {len(to_keep)}")
    print(f"  将删除 (step < {min_step}): {len(to_delete)}")
    print(f"  无 step 信息: {len(no_step_info)}")

    if to_delete:
        print(f"\n将要删除的会话 (step < {min_step}):")
        for session in sorted(to_delete, key=lambda x: x['step'] or 0):
            step_str = str(session['step']) if session['step'] is not None else "N/A"
            print(f"  - {session['session_id']} (step: {step_str})")

    if no_step_info:
        print(f"\n无 step 信息的会话 (不会删除):")
        for session in no_step_info:
            print(f"  - {session['session_id']}")

    deleted_count = 0
    if not dry_run and to_delete:
        print(f"\n开始删除 {len(to_delete)} 个会话目录...")
        for session in to_delete:
            try:
                shutil.rmtree(session['path'])
                deleted_count += 1
                print(f"  ✓ 已删除: {session['session_id']}")
            except Exception as e:
                print(f"  ✗ 删除失败 {session['session_id']}: {e}")
    elif dry_run:
        print(f"\n[DRY RUN] 未实际删除任何文件")

    return {
        'total': len(sessions),
        'kept': len(to_keep),
        'deleted': deleted_count,
        'no_step_info': len(no_step_info)
    }


def main():
    parser = argparse.ArgumentParser(
        description="清除 step 数量小于指定阈值的会话目录"
    )
    parser.add_argument(
        '--base-dir',
        type=str,
        default='logs/sessions',
        help='会话存储的基础目录 (默认: logs/sessions)'
    )
    parser.add_argument(
        '--min-step',
        type=int,
        default=300,
        help='最小 step 阈值，小于此值的会话将被清除 (默认: 100)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='只显示将要删除的会话，不实际删除'
    )

    args = parser.parse_args()

    print(f"清理配置:")
    print(f"  基础目录: {args.base_dir}")
    print(f"  最小 step 阈值: {args.min_step}")
    print(f"  模式: {'DRY RUN (仅预览)' if args.dry_run else '实际删除'}")

    stats = cleanup_sessions(
        base_dir=args.base_dir,
        min_step=args.min_step,
        dry_run=args.dry_run
    )

    print(f"\n清理完成!")
    print(f"  保留: {stats['kept']} 个会话")
    print(f"  删除: {stats['deleted']} 个会话")
    print(f"  无 step 信息: {stats['no_step_info']} 个会话")


if __name__ == '__main__':
    main()

