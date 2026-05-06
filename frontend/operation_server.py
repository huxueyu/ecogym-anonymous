


import sys
import os
import json
import math
from datetime import datetime


project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import yaml


app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)


bench_state = None
config = None


def load_config():
    config_path = os.path.join(project_root, 'config', 'operation_config.yaml')

    with open(config_path, 'r', encoding='utf-8') as f:
        content = f.read()
        lines = [line for line in content.split('\n') if '!include' not in line]
        modified_content = '\n'.join(lines)
        cfg = yaml.safe_load(modified_content)

    return cfg




def calculate_retention_rate(content_volume, content_quality, engagement_level, session_state):
    dynamics = session_state.get("_platform_dynamics", {})
    retention_params = dynamics.get("retention", {})

    base_retention = retention_params.get("base_retention", 0.80)
    content_factor_weight = retention_params.get("content_factor_weight", 0.20)
    quality_factor_weight = retention_params.get("quality_factor_weight", 0.20)
    engagement_factor_weight = retention_params.get("engagement_factor_weight", 0.25)
    max_retention = retention_params.get("max_retention", 0.95)
    min_retention = retention_params.get("min_retention", 0.3)


    content_factor = content_factor_weight * math.log(max(10, content_volume) / 10) / math.log(10)


    quality_factor = quality_factor_weight * content_quality


    engagement_factor = engagement_factor_weight * engagement_level


    quality_penalty = 0 if content_quality > 0.3 else (0.3 - content_quality) * 0.5

    retention = base_retention + content_factor + quality_factor + engagement_factor - quality_penalty

    return max(min_retention, min(max_retention, retention))


def calculate_natural_growth(content_quality, creator_activity, session_state):
    dynamics = session_state.get("_platform_dynamics", {})
    growth_params = dynamics.get("natural_growth", {})

    base_growth = growth_params.get("base_growth", 5)
    quality_multiplier = growth_params.get("quality_multiplier", 60)
    creator_multiplier = growth_params.get("creator_multiplier", 60)

    quality_bonus = int(quality_multiplier * content_quality)
    creator_bonus = int(creator_multiplier * creator_activity)

    return base_growth + quality_bonus + creator_bonus


def advance_platform_day(session_state):

    dau = session_state.get("dau", 1000)
    content_volume = session_state.get("content_volume", 100)
    content_quality = session_state.get("content_quality", 0.5)
    creator_activity = session_state.get("creator_activity", 0.5)
    engagement_level = session_state.get("engagement_level", 0)


    dynamics = session_state.get("_platform_dynamics", {})
    decay_params = dynamics.get("decay", {})
    ecosystem_params = dynamics.get("content_ecosystem", {})

    quality_decay_strength = decay_params.get("quality_decay", 0.05)
    quality_equilibrium = decay_params.get("quality_equilibrium", 0.00)
    creator_decay_strength = decay_params.get("creator_decay", 0.05)
    creator_equilibrium = decay_params.get("creator_equilibrium", 0.00)
    content_decay_rate = decay_params.get("content_decay_rate", 0.05)
    engagement_decay_rate = decay_params.get("engagement_decay", 0.08)

    content_creation_multiplier = ecosystem_params.get("content_creation_multiplier", 30)
    content_quality_bonus = ecosystem_params.get("content_quality_bonus", 0.5)


    retention_rate = calculate_retention_rate(content_volume, content_quality, engagement_level, session_state)
    retained_users = int(dau * retention_rate)
    churned_users = dau - retained_users


    natural_new_users = calculate_natural_growth(content_quality, creator_activity, session_state)


    new_dau = retained_users + natural_new_users
    session_state["dau"] = new_dau


    new_content_created = int(content_creation_multiplier * creator_activity * (1 + content_quality_bonus * content_quality))
    content_decay = int(content_volume * content_decay_rate)
    session_state["content_volume"] = max(10, content_volume + new_content_created - content_decay)


    engagement_penalty = engagement_level * 0.03
    quality_decay = (content_quality - quality_equilibrium) * quality_decay_strength
    session_state["content_quality"] = max(0.1, content_quality - quality_decay - engagement_penalty)

    session_state["engagement_level"] = max(0.0, engagement_level - engagement_decay_rate)

    creator_decay = (creator_activity - creator_equilibrium) * creator_decay_strength
    session_state["creator_activity"] = max(0.1, creator_activity - creator_decay)

    history = session_state.setdefault("dau_history", [])
    history.append({
        "day": session_state.get("day", 0),
        "dau": new_dau,
        "retained": retained_users,
        "new": natural_new_users,
        "churned": churned_users,
        "content_volume": session_state["content_volume"],
        "content_quality": round(session_state["content_quality"], 3),
        "retention_rate": round(retention_rate, 3),
        "timestamp": datetime.now().isoformat()
    })

    return {
        "dau": new_dau,
        "dau_change": new_dau - dau,
        "retained_users": retained_users,
        "new_users": natural_new_users,
        "churned_users": churned_users,
        "retention_rate": round(retention_rate, 3),
        "content_created": new_content_created,
        "content_decayed": content_decay
    }




def action_acquisition_boost(session_state):
    dynamics = session_state.get("_platform_dynamics", {})
    action_params = dynamics.get("actions", {}).get("acquisition_boost", {})
    base_new_users = action_params.get("base_new_users", 20)
    quality_bonus_rate = action_params.get("quality_bonus_rate", 1.1)

    quality = session_state.get("content_quality", 0.5)
    quality_bonus = int(base_new_users * quality * quality_bonus_rate)
    new_users = base_new_users + quality_bonus


    session_state["dau"] = session_state.get("dau", 0) + new_users

    history = session_state.setdefault("action_history", [])
    history.append({
        "day": session_state.get("day", 0),
        "action": "acquisition_boost",
        "new_users": new_users,
        "timestamp": datetime.now().isoformat()
    })

    return {
        "status": "success",
        "action": "acquisition_boost",
        "new_users_acquired": new_users
    }


def action_engagement_tune(session_state):
    dynamics = session_state.get("_platform_dynamics", {})
    action_params = dynamics.get("actions", {}).get("engagement_tune", {})
    engagement_boost = action_params.get("engagement_boost", 0.25)
    quality_penalty = action_params.get("quality_penalty", 0.05)

    current_engagement_level = session_state.get("engagement_level", 0)
    session_state["engagement_level"] = min(1.0, current_engagement_level + engagement_boost)

    quality = session_state.get("content_quality", 0.5)
    session_state["content_quality"] = max(0.0, quality - quality_penalty)

    history = session_state.setdefault("action_history", [])
    history.append({
        "day": session_state.get("day", 0),
        "action": "engagement_tune",
        "engagement_boost": engagement_boost,
        "quality_decay": quality_penalty,
        "timestamp": datetime.now().isoformat()
    })

    return {
        "status": "success",
        "action": "engagement_tune",
        "engagement_level": session_state["engagement_level"],
        "content_quality": round(session_state["content_quality"], 3)
    }


def action_creator_incentive(session_state):
    dynamics = session_state.get("_platform_dynamics", {})
    action_params = dynamics.get("actions", {}).get("creator_incentive", {})

    activity_boost_base = action_params.get("activity_boost_base", 0.25)
    diminishing_factor = action_params.get("diminishing_factor", 1.1)
    content_multiplier = action_params.get("content_multiplier", 50)

    creator_activity = session_state.get("creator_activity", 0.5)


    actual_boost = activity_boost_base * pow(1 - creator_activity, diminishing_factor)

    new_creator_activity = min(1.0, creator_activity + actual_boost)
    session_state["creator_activity"] = new_creator_activity

    content_volume = session_state.get("content_volume", 100)
    new_content = int(content_multiplier * new_creator_activity)
    session_state["content_volume"] = content_volume + new_content

    history = session_state.setdefault("action_history", [])
    history.append({
        "day": session_state.get("day", 0),
        "action": "creator_incentive",
        "creator_activity_gain": round(actual_boost, 4),
        "new_content": new_content,
        "timestamp": datetime.now().isoformat()
    })

    return {
        "status": "success",
        "action": "creator_incentive",
        "creator_activity": round(session_state["creator_activity"], 3),
        "activity_boost": round(actual_boost, 4),
        "content_added": new_content,
        "total_content": session_state["content_volume"]
    }


def action_moderation_tighten(session_state):
    dynamics = session_state.get("_platform_dynamics", {})
    action_params = dynamics.get("actions", {}).get("moderation_tighten", {})

    quality_boost_base = action_params.get("quality_boost_base", 0.30)
    diminishing_factor = action_params.get("diminishing_factor", 1.1)
    content_removal_rate = action_params.get("content_removal_rate", 0.10)
    creator_penalty_base = action_params.get("creator_penalty_base", 0.07)
    penalty_amplifier = action_params.get("penalty_amplifier", 1.1)

    quality = session_state.get("content_quality", 0.5)
    creator_activity = session_state.get("creator_activity", 0.5)

    actual_quality_boost = quality_boost_base * pow(1 - quality, diminishing_factor)
    session_state["content_quality"] = min(1.0, quality + actual_quality_boost)


    content_volume = session_state.get("content_volume", 100)
    removed = int(content_volume * content_removal_rate)
    session_state["content_volume"] = max(0, content_volume - removed)


    actual_creator_penalty = creator_penalty_base * (1 + penalty_amplifier * quality)
    session_state["creator_activity"] = max(0.0, creator_activity - actual_creator_penalty)

    history = session_state.setdefault("action_history", [])
    history.append({
        "day": session_state.get("day", 0),
        "action": "moderation_tighten",
        "quality_gain": round(actual_quality_boost, 4),
        "content_removed": removed,
        "creator_penalty": round(actual_creator_penalty, 4),
        "timestamp": datetime.now().isoformat()
    })

    return {
        "status": "success",
        "action": "moderation_tighten",
        "content_quality": round(session_state["content_quality"], 3),
        "quality_boost": round(actual_quality_boost, 4),
        "content_removed": removed,
        "remaining_content": session_state["content_volume"],
        "creator_activity": round(session_state["creator_activity"], 3),
        "creator_penalty": round(actual_creator_penalty, 4)
    }




def initialize_benchmark_state():
    global bench_state, config

    config = load_config()

    initial_state = config.get('initial_state', {})
    platform_dynamics = config.get('platform_dynamics_config', {})

    bench_state = {
        'day': initial_state.get('day', 0),
        'dau': initial_state.get('dau', 1000),
        'content_volume': initial_state.get('content_volume', 100),
        'content_quality': initial_state.get('content_quality', 0.5),
        'creator_activity': initial_state.get('creator_activity', 0.5),
        'engagement_level': initial_state.get('engagement_level', 0.0),
        'action_history': [],
        'dau_history': [],
        '_platform_dynamics': platform_dynamics
    }

    return bench_state


@app.route('/api/init', methods=['POST'])
def init_benchmark_session():
    state = initialize_benchmark_state()


    data = request.get_json() if request.is_json else {}
    user_id = data.get('user_id', 'anonymous')
    state['user_id'] = user_id

    return jsonify({
        'success': True,
        'state': {
            'day': state['day'],
            'dau': state['dau'],
            'content_volume': state['content_volume'],
            'content_quality': round(state['content_quality'], 3),
            'creator_activity': round(state['creator_activity'], 3),
            'engagement_level': round(state['engagement_level'], 3),
            'dau_history': state['dau_history'],
            'action_history': state['action_history']
        }
    })


@app.route('/api/action', methods=['POST'])
def execute_action():
    global bench_state

    if not bench_state:
        return jsonify({'success': False, 'message': 'Benchmark session not initialized'}), 400

    data = request.get_json()
    action_name = data.get('action')

    if not action_name:
        return jsonify({'success': False, 'message': 'No action specified'}), 400

    try:
        if action_name == 'acquisition_boost':
            result = action_acquisition_boost(bench_state)
        elif action_name == 'engagement_tune':
            result = action_engagement_tune(bench_state)
        elif action_name == 'creator_incentive':
            result = action_creator_incentive(bench_state)
        elif action_name == 'moderation_tighten':
            result = action_moderation_tighten(bench_state)
        else:
            return jsonify({'success': False, 'message': f'Unknown action: {action_name}'}), 400

        return jsonify({
            'success': True,
            'result': result,
            'state': {
                'day': bench_state['day'],
                'dau': bench_state['dau'],
                'content_volume': bench_state['content_volume'],
                'content_quality': round(bench_state['content_quality'], 3),
                'creator_activity': round(bench_state['creator_activity'], 3),
                'engagement_level': round(bench_state['engagement_level'], 3),
                'dau_history': bench_state['dau_history'],
                'action_history': bench_state['action_history']
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/end_day', methods=['POST'])
def end_day():
    global bench_state

    if not bench_state:
        return jsonify({'success': False, 'message': 'Benchmark session not initialized'}), 400

    try:
        day_result = advance_platform_day(bench_state)

        bench_state['day'] += 1

        max_days = config.get('run_settings', {}).get('max_days', 365)
        min_dau = config.get('run_settings', {}).get('min_dau_threshold', 100)

        run_terminated = False
        reason = None

        if bench_state['day'] >= max_days:
            run_terminated = True
            reason = 'max_days'
        elif bench_state['dau'] < min_dau:
            run_terminated = True
            reason = 'dau_collapse'

        return jsonify({
            'success': True,
            'day_result': day_result,
            'run_terminated': run_terminated,
            'reason': reason,
            'state': {
                'day': bench_state['day'],
                'dau': bench_state['dau'],
                'content_volume': bench_state['content_volume'],
                'content_quality': round(bench_state['content_quality'], 3),
                'creator_activity': round(bench_state['creator_activity'], 3),
                'engagement_level': round(bench_state['engagement_level'], 3),
                'dau_history': bench_state['dau_history'],
                'action_history': bench_state['action_history']
            }
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/state', methods=['GET'])
def get_state():
    if not bench_state:
        return jsonify({'success': False, 'message': 'Benchmark session not initialized'}), 400

    return jsonify({
        'success': True,
        'state': {
            'day': bench_state['day'],
            'dau': bench_state['dau'],
            'content_volume': bench_state['content_volume'],
            'content_quality': round(bench_state['content_quality'], 3),
            'creator_activity': round(bench_state['creator_activity'], 3),
            'engagement_level': round(bench_state['engagement_level'], 3),
            'dau_history': bench_state['dau_history'],
            'action_history': bench_state['action_history']
        }
    })


@app.route('/api/save_session', methods=['POST'])
def save_session():
    try:
        data = request.get_json()
        user_id = data.get('user_id', 'anonymous')
        state_snapshot = data.get('state_snapshot')
        if state_snapshot is None:
            state_snapshot = data.get('game_state', {})

        run_start_time = data.get('run_start_time', data.get('game_start_time'))
        run_end_time = data.get('run_end_time', data.get('game_end_time'))


        sessions_dir = os.path.join(project_root, 'logs', 'human_play_sessions')
        os.makedirs(sessions_dir, exist_ok=True)


        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        session_id = f"operation_bench_human_{user_id}_{timestamp}"
        session_dir = os.path.join(sessions_dir, session_id)
        os.makedirs(session_dir, exist_ok=True)


        metadata = {
            'session_id': session_id,
            'start_time': run_start_time,
            'completed_time': run_end_time,
            'last_update': run_end_time,
            'last_step': data.get('final_day', 0) * 2,
            'total_steps': data.get('final_day', 0) * 2,
            'status': 'completed',
            'config': {
                'benchmark_type': 'operation_bench',
                'participant_type': 'human',
                'user_id': user_id,
                'max_days': 365,
                'min_dau_threshold': 100
            },
            'initial_state': {
                'day': 0,
                'dau': 1000,
                'content_volume': 100,
                'content_quality': 0.5,
                'creator_activity': 0.5,
                'engagement_level': 0.0,
                'action_history': [],
                'dau_history': []
            },
            'final_stats': {
                'reason': data.get('reason'),
                'final_day': data.get('final_day'),
                'final_dau': data.get('final_dau'),
                'max_dau': data.get('max_dau'),
                'avg_dau': data.get('avg_dau')
            }
        }


        with open(os.path.join(session_dir, 'metadata.json'), 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)


        state_json = {
            'step': metadata['total_steps'],
            'timestamp': run_end_time,
            'state': {
                'day': state_snapshot.get('day', 0),
                'dau': state_snapshot.get('dau', 0),
                'content_volume': state_snapshot.get('content_volume', 0),
                'content_quality': state_snapshot.get('content_quality', 0),
                'creator_activity': state_snapshot.get('creator_activity', 0),
                'engagement_level': state_snapshot.get('engagement_level', 0),
                'action_history': state_snapshot.get('action_history', []),
                'dau_history': state_snapshot.get('dau_history', [])
            }
        }


        with open(os.path.join(session_dir, 'state.json'), 'w', encoding='utf-8') as f:
            json.dump(state_json, f, indent=2, ensure_ascii=False)


        steps = []
        action_history = state_snapshot.get('action_history', [])
        dau_history = state_snapshot.get('dau_history', [])

        step_num = 1
        for day in range(data.get('final_day', 0) + 1):

            day_action = next((a for a in action_history if a.get('day') == day), None)

            if day_action:

                action_name = day_action.get('action')
                action_timestamp = day_action.get('timestamp', run_start_time)

                if action_timestamp and not action_timestamp.endswith('Z'):
                    if '+' in action_timestamp:
                        action_timestamp = action_timestamp.split('+')[0] + 'Z'
                    else:
                        action_timestamp = action_timestamp + 'Z'

                step_entry = {
                    'step': step_num,
                    'session_id': session_id,
                    'state_before': {
                        'day': day
                    },
                    'tools_called': [{
                        'tool_name': action_name,
                        'tool_args': {},
                        'result': json.dumps(day_action),
                        'error': False
                    }],
                    'timestamp': action_timestamp
                }
                steps.append(step_entry)
                step_num += 1


            day_result = next((d for d in dau_history if d.get('day') == day), None)
            if day_result:

                day_timestamp = day_result.get('timestamp', run_start_time)

                if day_timestamp and not day_timestamp.endswith('Z'):
                    if '+' in day_timestamp:
                        day_timestamp = day_timestamp.split('+')[0] + 'Z'
                    else:
                        day_timestamp = day_timestamp + 'Z'

                task_done_entry = {
                    'step': step_num,
                    'session_id': session_id,
                    'state_before': {
                        'day': day
                    },
                    'tools_called': [{
                        'tool_name': 'task_done',
                        'tool_args': {},
                        'result': json.dumps(day_result),
                        'error': False
                    }],
                    'state_after': {
                        'day': day + 1
                    },
                    'timestamp': day_timestamp
                }
                steps.append(task_done_entry)
                step_num += 1


        with open(os.path.join(session_dir, 'steps.jsonl'), 'w', encoding='utf-8') as f:
            for step in steps:
                f.write(json.dumps(step, ensure_ascii=False) + '\n')

        return jsonify({
            'success': True,
            'message': 'Session saved successfully',
            'session_dir': session_dir,
            'session_id': session_id
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/api/user_sessions/<user_id>', methods=['GET'])
def get_user_sessions(user_id):
    try:
        sessions_dir = os.path.join(project_root, 'logs', 'human_play_sessions')

        if not os.path.exists(sessions_dir):
            return jsonify({
                'success': True,
                'sessions': []
            })

        sessions = []

        for dirname in sorted(os.listdir(sessions_dir), reverse=True):
            if dirname.startswith(f'operation_bench_human_{user_id}_'):
                session_dir = os.path.join(sessions_dir, dirname)
                metadata_path = os.path.join(session_dir, 'metadata.json')

                try:
                    with open(metadata_path, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        final_stats = metadata.get('final_stats', {})
                        sessions.append({
                            'session_id': metadata.get('session_id'),
                            'run_start_time': metadata.get('start_time'),
                            'run_end_time': metadata.get('completed_time'),
                            'reason': final_stats.get('reason'),
                            'final_day': final_stats.get('final_day'),
                            'final_dau': final_stats.get('final_dau'),
                            'max_dau': final_stats.get('max_dau'),
                            'avg_dau': final_stats.get('avg_dau')
                        })
                except Exception as e:
                    print(f"Error reading {dirname}: {e}")
                    continue

        return jsonify({
            'success': True,
            'sessions': sessions
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})


@app.route('/')
def index():
    return send_from_directory('.', 'operation_bench.html')


if __name__ == '__main__':
    print("=" * 60)
    print("Platform Operation Bench — Human study server")
    print("=" * 60)
    print("\nStarting server on http://localhost:5001")
    print("Study interface URL: http://localhost:5001/")
    print("You can also access it from other devices using: http://<your-ip>:5001/")
    print("\nPress Ctrl+C to stop the server\n")


    initialize_benchmark_state()


    app.run(host='0.0.0.0', port=5001, debug=True)
