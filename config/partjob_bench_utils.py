

import os
import math
import random
import numpy as np
import statistics
from typing import Dict, Any, Tuple

def set_seed(seed: int = 42):
    if seed is None:
        return

    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

    print(f"[Seed] Global seed set to: {seed}")

def partjob_is_finished(state: Dict[str, Any], max_days: int = 100) -> bool:
    money = state.get("money", 0)
    energy = state.get("energy", 0)
    stress = state.get("stress", 0)
    day = state.get("day", 0)

    if money <= 0: return True
    if energy <= 0: return True
    if stress >= 100: return True
    if day >= max_days: return True

    return False

def partjob_check_termination_reason(state: Dict[str, Any], max_days: int = 100) -> Tuple[str, float]:
    money = state.get("money", 0)
    energy = state.get("energy", 0)
    stress = state.get("stress", 0)
    day = state.get("day", 0)

    if money <= 0: return "Bankruptcy (Money <= 0)", 0.9
    if energy <= 0: return "Exhaustion (Energy <= 0)", 0.9
    if stress >= 100: return "Burnout (Stress >= 100)", 0.9
    if day >= max_days: return "Career Completed (Time limit reached)", 1.0

    return "Running", 1.0

def partjob_cal_metric(state: Dict[str, Any]) -> Dict[str, float]:
    reason, penalty = partjob_check_termination_reason(state)

    money = max(0, state.get("money", 0))
    energy = max(0, state.get("energy", 0))
    stress = min(100, max(0, state.get("stress", 0)))
    day = state.get("day", 0)

    skills = state.get("skill_rating", {})
    if isinstance(skills, dict):
        skill_values = list(skills.values())
        avg_skill = statistics.mean(skill_values) if skill_values else 60.0
    elif isinstance(skills, list):
        avg_skill = statistics.mean(skills) if skills else 60.0
    else:
        avg_skill = 60.0

    long_term_score = (avg_skill * 0.5) + (energy * 0.25) + ((100 - stress) * 0.25)

    raw_score = (money * 0.6 + long_term_score * 0.4)

    final_score = raw_score * penalty

    return {
        "final_day": day,
        "final_score": round(final_score, 2),
        "raw_score": round(raw_score, 2),
        "short_term_component": round(money * 0.6, 2),
        "long_term_component": round(long_term_score * 0.4, 2),
        "penalty_coefficient": penalty,
        "termination_reason": reason,
        "final_money": round(money, 2),
        "final_energy": round(energy, 2),
        "final_stress": round(stress, 2),
        "avg_skill": round(avg_skill, 2),
    }