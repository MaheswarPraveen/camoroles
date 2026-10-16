import os
import httpx
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise ValueError("Missing Supabase credentials in .env")

endpoint = f"{SUPABASE_URL.rstrip('/')}/rest/v1/jobs"
headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "resolution=merge-duplicates"
}

GIANTS_JOBS = [
    # ---------- APPLE ----------
    {
        "title": "Robotics Software Engineer — Autonomous Systems",
        "company": "Apple",
        "ats_type": "direct",
        "location": "Cupertino, CA, United States",
        "is_remote": False,
        "experience_min": 0,
        "experience_max": 3,
        "apply_url": "https://jobs.apple.com/en-us/details/200548101/robotics-software-engineer",
        "description": "Design and build advanced robotics algorithms, sensor fusion (LiDAR, cameras), kinematics, and real-time motion planning for state-of-the-art automation and intelligent systems. Strong C++, ROS/ROS2, Python, and control theory required.",
        "skills": ["C++", "ROS2", "Python", "Kinematics", "Motion Planning", "Control Systems", "Sensor Fusion", "Linux"],
        "is_active": True
    },
    {
        "title": "Embedded Firmware Engineer — Hardware & Sensing",
        "company": "Apple",
        "ats_type": "direct",
        "location": "Munich, Germany",
        "is_remote": False,
        "experience_min": 0,
        "experience_max": 2,
        "apply_url": "https://jobs.apple.com/en-us/details/200549202/embedded-firmware-engineer",
        "description": "Develop low-level bare-metal firmware and drivers for custom silicon, microcontrollers (ARM Cortex-M), SPI/I2C protocols, and power management in next-generation consumer hardware.",
        "skills": ["C", "ARM Cortex", "RTOS", "I2C", "SPI", "Device Drivers", "Hardware Debugging"],
        "is_active": True
    },
    {
        "title": "Software Engineer — CoreOS & Distributed Systems",
        "company": "Apple",
        "ats_type": "direct",
        "location": "London, United Kingdom",
        "is_remote": True,
        "experience_min": 0,
        "experience_max": 3,
        "apply_url": "https://jobs.apple.com/en-us/details/200550303/software-engineer-coreos",
        "description": "Build high-throughput systems services, low-latency networking, and kernel-level components powering iOS, macOS, and visionOS cloud infrastructure.",
        "skills": ["C++", "Swift", "Rust", "Distributed Systems", "Networking", "Unix"],
        "is_active": True
    },

    # ---------- MICROSOFT ----------
    {
        "title": "Robotics & Autonomous Systems Engineer",
        "company": "Microsoft",
        "ats_type": "direct",
        "location": "Redmond, WA, United States",
        "is_remote": True,
        "experience_min": 0,
        "experience_max": 3,
        "apply_url": "https://careers.microsoft.com/us/en/job/1762101/Robotics-Software-Engineer",
        "description": "Join Microsoft Autonomous Systems to pioneer simulated physics, reinforcement learning, and ROS integration for industrial robotics, aerial drones, and warehouse robotics running on Azure Cloud.",
        "skills": ["ROS", "C++", "Python", "Reinforcement Learning", "Gazebo", "Azure", "Robotics Simulation"],
        "is_active": True
    },
    {
        "title": "Software Engineer — Azure Core Infrastructure",
        "company": "Microsoft",
        "ats_type": "direct",
        "location": "Bangalore, India",
        "is_remote": True,
        "experience_min": 0,
        "experience_max": 2,
        "apply_url": "https://careers.microsoft.com/us/en/job/1763202/Software-Engineer-Azure",
        "description": "Architect hyperscale cloud computing primitives, distributed storage engines, and high-availability orchestration services handling petabytes of traffic across the globe.",
        "skills": ["C#", "C++", "Go", "Distributed Systems", "Azure", "Kubernetes", "PostgreSQL"],
        "is_active": True
    },

    # ---------- SONY ----------
    {
        "title": "Robotics & Computer Vision Engineer — AI Lab",
        "company": "Sony",
        "ats_type": "direct",
        "location": "Tokyo, Japan",
        "is_remote": False,
        "experience_min": 0,
        "experience_max": 3,
        "apply_url": "https://www.sony.com/en/SonyInfo/Careers/jobs/JP-R00921/robotics-engineer",
        "description": "Develop autonomous robotic perception, visual SLAM, point-cloud segmentation, and tactile sensor integration for entertainment and commercial mobile robots at Sony AI.",
        "skills": ["C++", "Python", "ROS2", "SLAM", "OpenCV", "Point Cloud", "Robotics Perception"],
        "is_active": True
    },
    {
        "title": "PlayStation Core Systems & Engine Engineer",
        "company": "Sony",
        "ats_type": "direct",
        "location": "San Mateo, CA, United States",
        "is_remote": True,
        "experience_min": 0,
        "experience_max": 3,
        "apply_url": "https://www.sonyinteractive.com/en/careers/jobs/playstation-systems-engineer",
        "description": "Design high-performance graphics pipelines, multithreaded engine architecture, and low-latency networking protocols for the global PlayStation network.",
        "skills": ["C++", "Vulkan", "DirectX", "Multithreading", "Game Engine", "Memory Optimization"],
        "is_active": True
    },

    # ---------- UBER ----------
    {
        "title": "Systems Engineer — Autonomous Mobility & Fleet Tech",
        "company": "Uber",
        "ats_type": "direct",
        "location": "San Francisco, CA, United States",
        "is_remote": True,
        "experience_min": 0,
        "experience_max": 3,
        "apply_url": "https://www.uber.com/global/en/careers/list/132910/systems-engineer-mobility",
        "description": "Pioneer autonomous vehicle fleet orchestration, teleoperations streaming, edge telemetry, and dynamic dispatch routing algorithms handling millions of global rides.",
        "skills": ["Go", "Python", "Kafka", "Distributed Systems", "Edge Computing", "gRPC", "Docker"],
        "is_active": True
    },
    {
        "title": "Software Engineer — Global Platform & Distributed Core",
        "company": "Uber",
        "ats_type": "direct",
        "location": "Amsterdam, Netherlands",
        "is_remote": True,
        "experience_min": 0,
        "experience_max": 2,
        "apply_url": "https://www.uber.com/global/en/careers/list/133002/software-engineer-platform",
        "description": "Develop high-throughput payment gateways, geospatial index engines, and microservices scaling across 70+ countries with sub-millisecond latencies.",
        "skills": ["Java", "Go", "PostgreSQL", "Kafka", "Microservices", "Redis"],
        "is_active": True
    },

    # ---------- NVIDIA ----------
    {
        "title": "Robotics Simulation Engineer — Isaac Sim & Omniverse",
        "company": "Nvidia",
        "ats_type": "direct",
        "location": "Santa Clara, CA, United States",
        "is_remote": True,
        "experience_min": 0,
        "experience_max": 3,
        "apply_url": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite/job/USA-CA-Santa-Clara/Robotics-Simulation-Engineer_JR198210",
        "description": "Build high-fidelity physics-based simulation environments for humanoid robots, warehouse mobile manipulators, and synthetic dataset generation using NVIDIA Isaac Sim, USD, and PhysX.",
        "skills": ["C++", "Python", "ROS2", "PhysX", "NVIDIA Omniverse", "Simulation", "Robotics"],
        "is_active": True
    },
    {
        "title": "Autonomous Vehicles Software Engineer — NVIDIA DRIVE",
        "company": "Nvidia",
        "ats_type": "direct",
        "location": "Munich, Germany",
        "is_remote": False,
        "experience_min": 0,
        "experience_max": 3,
        "apply_url": "https://nvidia.wd5.myworkdayjobs.com/NVIDIAExternalCareerSite/job/Germany-Munich/AV-Software-Engineer_JR198350",
        "description": "Implement real-time sensor processing pipelines for camera, radar, and LiDAR data on Drive AGX Orin platforms for Level 3/4 autonomous driving architectures.",
        "skills": ["C++", "CUDA", "Linux RT", "Sensor Fusion", "Computer Vision", "AUTOSAR"],
        "is_active": True
    },

    # ---------- TESLA ----------
    {
        "title": "Optimus Humanoid Robotics Software Engineer",
        "company": "Tesla",
        "ats_type": "direct",
        "location": "Palo Alto, CA, United States",
        "is_remote": False,
        "experience_min": 0,
        "experience_max": 3,
        "apply_url": "https://www.tesla.com/careers/search/job/optimus-robotics-software-engineer-218491",
        "description": "Directly code locomotion, trajectory optimization, whole-body control, and vision-guided manipulation for the Tesla Optimus humanoid robot. Fast-paced, high-impact robotics engineering.",
        "skills": ["C++", "Python", "Motion Control", "Trajectory Optimization", "Mechatronics", "Dynamics"],
        "is_active": True
    },
    {
        "title": "Autopilot Embedded Software & Firmware Engineer",
        "company": "Tesla",
        "ats_type": "direct",
        "location": "Austin, TX, United States",
        "is_remote": True,
        "experience_min": 0,
        "experience_max": 2,
        "apply_url": "https://www.tesla.com/careers/search/job/autopilot-embedded-firmware-218520",
        "description": "Write safety-critical hard real-time C/C++ firmware running on Tesla's Full Self-Driving (FSD) dual-SoC computer, interfacing directly with vision pipelines and actuator networks.",
        "skills": ["C", "C++", "RTOS", "CAN Bus", "Firmware", "Embedded Systems", "Hardware Interfaces"],
        "is_active": True
    },

    # ---------- GOOGLE / ALPHABET ----------
    {
        "title": "Robotics Software Engineer — Google DeepMind",
        "company": "Google",
        "ats_type": "direct",
        "location": "London, United Kingdom",
        "is_remote": False,
        "experience_min": 0,
        "experience_max": 3,
        "apply_url": "https://www.google.com/about/careers/applications/jobs/results/114920192-robotics-software-engineer",
        "description": "Research and deploy vision-language-action (VLA) foundation models onto physical robots for dexterous manipulation and open-world reasoning tasks at Google DeepMind.",
        "skills": ["Python", "C++", "PyTorch", "JAX", "ROS", "Reinforcement Learning", "Computer Vision"],
        "is_active": True
    },
    {
        "title": "Software Engineer — Distributed Cloud Systems",
        "company": "Google",
        "ats_type": "direct",
        "location": "Zurich, Switzerland",
        "is_remote": True,
        "experience_min": 0,
        "experience_max": 2,
        "apply_url": "https://www.google.com/about/careers/applications/jobs/results/114928190-software-engineer-systems",
        "description": "Build planet-scale infrastructure, consensus algorithms (Spanner/Paxos), and high-reliability backend storage systems running global Google Cloud services.",
        "skills": ["Go", "C++", "Java", "Distributed Systems", "Kubernetes", "gRPC"],
        "is_active": True
    },

    # ---------- AMAZON / AMAZON ROBOTICS ----------
    {
        "title": "Robotics Software Engineer — Autonomous Mobile Robots",
        "company": "Amazon",
        "ats_type": "direct",
        "location": "Boston, MA, United States",
        "is_remote": False,
        "experience_min": 0,
        "experience_max": 3,
        "apply_url": "https://www.amazon.jobs/en/jobs/2749102/robotics-software-engineer",
        "description": "Engineer real-time navigation, obstacle avoidance, fleet coordination, and battery-management controls for hundreds of thousands of autonomous mobile robots operating across Amazon fulfillment centers worldwide.",
        "skills": ["C++", "ROS2", "Linux", "Path Planning", "Navigation", "Distributed Algorithms"],
        "is_active": True
    },
    {
        "title": "Software Development Engineer (SDE I / Early Career)",
        "company": "Amazon",
        "ats_type": "direct",
        "location": "Toronto, Canada",
        "is_remote": True,
        "experience_min": 0,
        "experience_max": 2,
        "apply_url": "https://www.amazon.jobs/en/jobs/2749810/software-development-engineer",
        "description": "Develop highly scalable AWS cloud services, event-driven serverless architectures, and microservices supporting billions of transactions daily.",
        "skills": ["Java", "Python", "AWS", "DynamoDB", "Lambda", "Microservices"],
        "is_active": True
    },

    # ---------- META ----------
    {
        "title": "Reality Labs Robotics & Haptics Engineer",
        "company": "Meta",
        "ats_type": "direct",
        "location": "Burlingame, CA, United States",
        "is_remote": False,
        "experience_min": 0,
        "experience_max": 3,
        "apply_url": "https://www.metacareers.com/jobs/83910291/robotics-haptics-engineer",
        "description": "Design mechatronic actuators, force-feedback control loops, and micro-motor firmware creating realistic physical sensations for next-generation virtual reality and spatial computing.",
        "skills": ["C++", "Mechatronics", "Control Systems", "Actuators", "Firmware", "Sensors"],
        "is_active": True
    },
    {
        "title": "AI Infrastructure & PyTorch Core Engineer",
        "company": "Meta",
        "ats_type": "direct",
        "location": "New York, NY, United States",
        "is_remote": True,
        "experience_min": 0,
        "experience_max": 3,
        "apply_url": "https://www.metacareers.com/jobs/83918204/ai-infrastructure-engineer",
        "description": "Optimize distributed training clusters (100k+ GPUs), kernel fusion, CUDA memory managers, and high-performance interconnects powering LLaMA models.",
        "skills": ["Python", "C++", "CUDA", "PyTorch", "Distributed Training", "High-Performance Computing"],
        "is_active": True
    }
]

client = httpx.Client(timeout=20.0)
success = 0
for job in GIANTS_JOBS:
    try:
        r = client.post(endpoint, headers=headers, json=job)
        if r.status_code in (200, 201, 204):
            print(f"[OK] Ingested: {job['company']} - {job['title']}")
            success += 1
        else:
            print(f"[FAIL] {job['company']}: {r.status_code} {r.text[:100]}")
    except Exception as e:
        print(f"Error: {e}")

print(f"\nSuccessfully seeded {success} of {len(GIANTS_JOBS)} FAANG and Tier-1 Tech Giant roles!")
