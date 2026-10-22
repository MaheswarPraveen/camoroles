import httpx
import json

URL = "https://camouroles.primemax.workers.dev/api/ai/recruiter_chat"

profile = {
    "headline": "Robotics and AI Research Engineer",
    "experienceYears": 1,
    "experienceText": "1+ yrs verified experience",
    "skills": ["Python", "C/C++", "JavaScript", "Kotlin", "ROS 2", "ArduPilot", "TensorFlow", "PyTorch", "OpenCV", "ESP32", "Arduino"],
    "discipline": "robotics"
}

def send_chat(msg, conversation):
    payload = {
        "message": msg,
        "conversation": conversation,
        "profile": profile,
        "cv_summary": "Robotics and AI Research Engineer (1+ yrs verified experience) - Core Skills: Python, C/C++, ROS 2, ArduPilot, PyTorch, OpenCV"
    }
    r = httpx.post(URL, json=payload, timeout=25.0)
    print(f"Status: {r.status_code}")
    data = r.json()
    print("REPLY:\n", data.get("reply"))
    print("FILTERS:", json.dumps(data.get("filters"), indent=2))
    print(f"TOTAL MATCHED: {data.get('total_matched')}")
    print("=" * 60)
    return data

def main():
    history = []

    print("--- TURN 1: Initial query ---")
    d1 = send_chat("Show me robotics positions", history)
    history.append({"role": "user", "content": "Show me robotics positions"})
    history.append({"role": "assistant", "content": d1.get("reply", "")})

    print("--- TURN 2: Follow-up for remote (Should retain robotics!) ---")
    d2 = send_chat("can we have some remote jobs?", history)
    history.append({"role": "user", "content": "can we have some remote jobs?"})
    history.append({"role": "assistant", "content": d2.get("reply", "")})

    print("--- TURN 3: Conversational Meta-Query (Memory check) ---")
    d3 = send_chat("what was my previous question?", history)
    history.append({"role": "user", "content": "what was my previous question?"})
    history.append({"role": "assistant", "content": d3.get("reply", "")})

if __name__ == "__main__":
    main()
