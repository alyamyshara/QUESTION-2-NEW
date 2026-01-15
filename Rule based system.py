# app.py
import operator
import streamlit as st
from typing import Dict, Any, List, Tuple

# ----------------------------
# Rule engine operators
# ----------------------------
OPS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
}

# ----------------------------
# Rule definitions (Table 1)
# ----------------------------
DEFAULT_RULES: List[Dict[str, Any]] = [
    {
        "name": "Windows open → turn AC off",
        "priority": 100,
        "conditions": [["windows_open", "==", True]],
        "action": {
            "ac_mode": "OFF",
            "fan_speed": "LOW",
            "setpoint": "-",
            "reason": "Windows are open",
        },
    },
    {
        "name": "No one home → eco mode",
        "priority": 90,
        "conditions": [
            ["occupancy", "==", "EMPTY"],
            ["temperature", ">=", 24],
        ],
        "action": {
            "ac_mode": "ECO",
            "fan_speed": "LOW",
            "setpoint": 27,
            "reason": "Home empty; save energy",
        },
    },
    {
        "name": "Hot & humid (occupied) → cool strong",
        "priority": 80,
        "conditions": [
            ["occupancy", "==", "OCCUPIED"],
            ["temperature", ">=", 30],
            ["humidity", ">=", 70],
        ],
        "action": {
            "ac_mode": "COOL",
            "fan_speed": "HIGH",
            "setpoint": 23,
            "reason": "Hot and humid",
        },
    },
    {
        "name": "Night (occupied) → sleep mode",
        "priority": 75,
        "conditions": [
            ["occupancy", "==", "OCCUPIED"],
            ["time_of_day", "==", "NIGHT"],
            ["temperature", ">=", 26],
        ],
        "action": {
            "ac_mode": "SLEEP",
            "fan_speed": "LOW",
            "setpoint": 26,
            "reason": "Night comfort",
        },
    },
    {
        "name": "Hot (occupied) → cool",
        "priority": 70,
        "conditions": [
            ["occupancy", "==", "OCCUPIED"],
            ["temperature", ">=", 28],
        ],
        "action": {
            "ac_mode": "COOL",
            "fan_speed": "MEDIUM",
            "setpoint": 24,
            "reason": "Temperature high",
        },
    },
    {
        "name": "Slightly warm (occupied) → gentle cool",
        "priority": 60,
        "conditions": [
            ["occupancy", "==", "OCCUPIED"],
            ["temperature", ">=", 26],
            ["temperature", "<", 28],
        ],
        "action": {
            "ac_mode": "COOL",
            "fan_speed": "LOW",
            "setpoint": 25,
            "reason": "Slightly warm",
        },
    },
    {
        "name": "Too cold → turn off",
        "priority": 85,
        "conditions": [["temperature", "<=", 22]],
        "action": {
            "ac_mode": "OFF",
            "fan_speed": "LOW",
            "setpoint": "-",
            "reason": "Already cold",
        },
    },
]

# ----------------------------
# Rule evaluation functions
# ----------------------------
def evaluate_condition(facts: Dict[str, Any], cond: List[Any]) -> bool:
    field, op, value = cond
    return OPS[op](facts[field], value)


def rule_matches(facts: Dict[str, Any], rule: Dict[str, Any]) -> bool:
    return all(evaluate_condition(facts, c) for c in rule["conditions"])


def run_rules(
    facts: Dict[str, Any], rules: List[Dict[str, Any]]
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    fired = [r for r in rules if rule_matches(facts, r)]
    if not fired:
        return {
            "ac_mode": "OFF",
            "fan_speed": "LOW",
            "setpoint": "-",
            "reason": "No rule matched",
        }, []
    fired.sort(key=lambda r: r["priority"], reverse=True)
    return fired[0]["action"], fired


# ----------------------------
# Streamlit UI
# ----------------------------
st.set_page_config(page_title="Smart Home AC Controller", page_icon="❄️")
st.title("❄️ Rule-Based Smart Home Air Conditioner Controller")

st.sidebar.header("Home Conditions")
temperature = st.sidebar.number_input("Temperature (°C)", value=22)
humidity = st.sidebar.number_input("Humidity (%)", value=46)
occupancy = st.sidebar.selectbox("Occupancy", ["OCCUPIED", "EMPTY"])
time_of_day = st.sidebar.selectbox(
    "Time of Day", ["MORNING", "AFTERNOON", "EVENING", "NIGHT"]
)
windows_open = st.sidebar.checkbox("Windows Open", value=False)

facts = {
    "temperature": temperature,
    "humidity": humidity,
    "occupancy": occupancy,
    "time_of_day": time_of_day,
    "windows_open": windows_open,
}

st.subheader("Current Home Facts")
st.json(facts)

if st.button("Evaluate AC Setting", type="primary"):
    action, fired = run_rules(facts, DEFAULT_RULES)

    st.subheader("AC Decision")
    st.success(
        f"""
**Mode:** {action['ac_mode']}  
**Fan Speed:** {action['fan_speed']}  
**Setpoint:** {action['setpoint']}  
**Reason:** {action['reason']}
"""
    )

    st.subheader("Matched Rules (Priority Order)")
    for r in fired:
        st.write(f"• {r['name']} (priority {r['priority']})")
