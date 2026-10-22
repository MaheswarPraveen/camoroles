"""
Ingest verified open engineering positions for Apple and Meta into Supabase.
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(".dev.vars")
load_dotenv("backend/.env")
load_dotenv(".env")

url = os.getenv("SUPABASE_URL", "https://xteoktfzftqybflpubvo.supabase.co")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
sb = create_client(url, key)

jobs = [
  {
    "title": "Software Engineer, Systems ML",
    "company": "Meta",
    "apply_url": "https://www.metacareers.com/profile/job_details/3414246448833665/",
    "location": "Sunnyvale, CA",
    "experience_min": 3,
    "experience_max": 8,
    "skills": ["Python", "C++", "PyTorch", "Distributed Training", "ML Systems"],
    "description": "Meta is seeking an AI Software Engineer to join our Research & Development teams applying deep systems and hardware acceleration expertise to build and optimize intelligent ML infrastructure.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "Software Engineer, Systems",
    "company": "Meta",
    "apply_url": "https://www.metacareers.com/profile/job_details/2082780019279407/",
    "location": "Tel Aviv, Israel",
    "experience_min": 8,
    "experience_max": 13,
    "skills": ["Distributed Systems", "C++", "Platform Infrastructure", "Performance Optimization", "Linux"],
    "description": "Staff Systems Software Engineer role designing and building foundational infrastructure that powers products used by billions worldwide.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "Software Engineer, AI Kernels & Performance Optimization - MTIA Software",
    "company": "Meta",
    "apply_url": "https://www.metacareers.com/profile/job_details/1442149171184618/",
    "location": "Menlo Park, CA",
    "experience_min": 6,
    "experience_max": 11,
    "skills": ["C++", "CUDA", "AI Kernels", "Hardware Accelerators", "PyTorch"],
    "description": "Meta designs and deploys its own AI systems using MTIA. This role focuses on developing low-level parallel AI kernels and fused attention operators.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "Software Engineer, GenAI Frameworks - MTIA",
    "company": "Meta",
    "apply_url": "https://www.metacareers.com/profile/job_details/2411086396300206/",
    "location": "Menlo Park, CA",
    "experience_min": 8,
    "experience_max": 13,
    "skills": ["Frontier Models", "PyTorch", "C++", "Distributed Inference", "MTIA"],
    "description": "Focuses on scaling frontier models onto Meta's in-house AI accelerators and building distributed inference substrates.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "Software Engineer, Systems ML - Compilers / Kernels",
    "company": "Meta",
    "apply_url": "https://www.metacareers.com/profile/job_details/1795363151729651/",
    "location": "Bellevue, WA",
    "experience_min": 6,
    "experience_max": 11,
    "skills": ["ML Compilers", "MLIR / LLVM", "CUDA", "C++", "PyTorch"],
    "description": "Designs, builds, and optimizes systems-level machine learning software enabling efficient training and inference across Meta's infrastructure.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "Software Engineer, SystemML - AI Networking",
    "company": "Meta",
    "apply_url": "https://www.metacareers.com/profile/job_details/1516424347176117/",
    "location": "Menlo Park, CA",
    "experience_min": 3,
    "experience_max": 8,
    "skills": ["AI Networking", "NCCL", "Distributed Systems", "PyTorch", "C++"],
    "description": "Part of the AI Networking Software team developing and owning the software stack around NCCL for multi-GPU LLM training clusters.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "Research Scientist, Artificial Intelligence",
    "company": "Meta",
    "apply_url": "https://www.metacareers.com/profile/job_details/1513805147458616/",
    "location": "Menlo Park, CA",
    "experience_min": 8,
    "experience_max": 13,
    "skills": ["Frontier Models", "PyTorch", "Distributed Training", "Large Language Models", "Python"],
    "description": "Staff Research Scientist role within Meta AI Research advancing foundational and frontier model training architectures.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "Software Engineer - Infrastructure (Technical Leadership)",
    "company": "Meta",
    "apply_url": "https://www.metacareers.com/profile/job_details/1405498381042864/",
    "location": "Menlo Park, CA",
    "experience_min": 12,
    "experience_max": 17,
    "skills": ["Infrastructure", "Distributed Systems", "High Availability", "C++", "Python"],
    "description": "Senior technical leadership position building the next generation of infrastructure for hyperscale production reliability.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "Software Engineer - Storage (Technical Leadership)",
    "company": "Meta",
    "apply_url": "https://www.metacareers.com/profile/job_details/2100171950572222/",
    "location": "Bellevue, WA",
    "experience_min": 8,
    "experience_max": 13,
    "skills": ["Distributed Storage", "Distributed Systems", "C++", "High Throughput", "Storage Infra"],
    "description": "Core storage infrastructure role powering Meta products at exabyte scale with sub-second latency constraints.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "Computer Vision Engineer, Reality Labs",
    "company": "Meta",
    "apply_url": "https://www.metacareers.com/profile/job_details/1725888355192236/",
    "location": "Redmond, WA",
    "experience_min": 2,
    "experience_max": 7,
    "skills": ["Computer Vision", "3D Reconstruction", "SLAM", "C++", "Perception"],
    "description": "Develops real-time computer vision, SLAM, and spatial perception algorithms within Reality Labs for next-generation VR/AR headsets.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "Software Engineer, Computer Vision (Technical Leadership)",
    "company": "Meta",
    "apply_url": "https://www.metacareers.com/profile/job_details/1349022433577870/",
    "location": "Burlingame, CA",
    "experience_min": 3,
    "experience_max": 8,
    "skills": ["Computer Vision", "Sensor Fusion", "Real-Time Systems", "C++", "Machine Learning"],
    "description": "Technical leadership role within Reality Labs and AI teams driving computer vision innovation for mixed reality hardware.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "Sr. Machine Learning Engineer, Foundation Models Inference - Cloud OS & Inference",
    "company": "Apple",
    "apply_url": "https://jobs.apple.com/en-us/details/200677962-3337/sr-machine-learning-engineer-foundation-models-inference-cloud-os-inference",
    "location": "Santa Clara, California",
    "experience_min": 3,
    "experience_max": 8,
    "skills": ["Frontier Models", "LLM Inference", "Low Latency C++", "GPU Optimization", "Distributed Systems"],
    "description": "Builds high-performance, secure, and private inference infrastructure powering Apple Intelligence and Siri across Private Cloud Compute.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "ML Framework (MetalLM) Engineer, Graphics, Game and ML",
    "company": "Apple",
    "apply_url": "https://jobs.apple.com/en-us/details/200572773/ml-framework-metallm-engineer-graphics-game-and-ml",
    "location": "Cupertino, California",
    "experience_min": 3,
    "experience_max": 8,
    "skills": ["Metal", "C++", "LLM Frameworks", "Apple Silicon", "PyTorch"],
    "description": "Focuses on enabling Apple Intelligence through high-performance, distributed inference of GenAI and LLM applications using Apple Silicon in data centers.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "AI/ML Software Engineer",
    "company": "Apple",
    "apply_url": "https://jobs.apple.com/en-us/details/200676774/ai-ml-software-engineer",
    "location": "Sunnyvale, California",
    "experience_min": 3,
    "experience_max": 8,
    "skills": ["On-Device AI", "CoreML", "Low Latency C++", "Python", "Swift"],
    "description": "Delivers computer vision and machine learning algorithms optimizing deep learning models for on-device inference using CoreML and Apple Neural Engine.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "CoreOS Kernel Performance Engineer",
    "company": "Apple",
    "apply_url": "https://jobs.apple.com/en-us/details/200678852-0836/coreos-kernel-performance-engineer",
    "location": "Cupertino, California",
    "experience_min": 3,
    "experience_max": 8,
    "skills": ["iOS / macOS Kernel", "XNU", "Low Latency C++", "Apple Silicon", "Operating Systems"],
    "description": "Works within Apple's CoreOS organization to push performance boundaries on Apple Silicon platforms across iOS, macOS, visionOS, and watchOS.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "Software Development Engineer in Test - Kernel Quality Engineering, Core OS",
    "company": "Apple",
    "apply_url": "https://jobs.apple.com/en-us/details/200688785/software-development-engineer-in-test-kernel-quality-engineering-core-os",
    "location": "Cupertino, California",
    "experience_min": 3,
    "experience_max": 8,
    "skills": ["iOS / macOS Kernel", "XNU", "C / C++", "Test Automation", "Darwin OS"],
    "description": "Part of the Darwin Kernel organization responsible for qualifying the XNU kernel running at the heart of iOS, macOS, watchOS, and visionOS.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "Software Development Engineer (Distributed Systems) - Cloud",
    "company": "Apple",
    "apply_url": "https://jobs.apple.com/en-us/details/2006771416-0836/software-development-engineer-distributed-systems-cloud",
    "location": "Cupertino, California",
    "experience_min": 3,
    "experience_max": 8,
    "skills": ["Distributed Systems", "Cloud Infrastructure", "Kubernetes", "Golang", "Scalability"],
    "description": "Builds and maintains key control-plane features and distributed primitives for Apple's large-scale, multi-site cloud compute platform.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "Core Distributed Systems Database Engineer",
    "company": "Apple",
    "apply_url": "https://jobs.apple.com/en-us/details/200686966/core-distributed-systems-database-engineer",
    "location": "London, England",
    "experience_min": 3,
    "experience_max": 8,
    "skills": ["Distributed Systems", "Cassandra", "NoSQL", "Database Systems", "Java"],
    "description": "Part of Apple Services Engineering architecting the next generation of massive-scale distributed data platforms based on Apache Cassandra.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "Software Engineer, Apple Services Engineering",
    "company": "Apple",
    "apply_url": "https://jobs.apple.com/en-us/details/200689298-3337/software-engineer-apple-services-engineering",
    "location": "Seattle, Washington",
    "experience_min": 3,
    "experience_max": 8,
    "skills": ["Distributed Systems", "CloudKit", "High-Throughput Services", "Java", "Backend Infra"],
    "description": "Develops CloudKit, Apple's foundational privacy-focused distributed database platform that synchronizes data across billions of active devices worldwide.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "Machine Learning Systems Engineer - Video Computer Vision",
    "company": "Apple",
    "apply_url": "https://jobs.apple.com/en-us/details/200681077-3956/machine-learning-systems-engineer-video-computer-vision",
    "location": "Sunnyvale, California",
    "experience_min": 3,
    "experience_max": 8,
    "skills": ["Computer Vision", "Video Generation", "Multimodal AI", "Apple Silicon", "C++"],
    "description": "Works within the Video Computer Vision team shipping multimodal foundation models and computer vision systems onto Apple hardware platforms.",
    "ats_type": "direct",
    "is_active": True
  },
  {
    "title": "Camera Machine Learning Engineer",
    "company": "Apple",
    "apply_url": "https://jobs.apple.com/en-us/details/200684944/camera-machine-learning-engineer",
    "location": "Cupertino, California",
    "experience_min": 3,
    "experience_max": 8,
    "skills": ["Computer Vision", "Computational Photography", "Deep Learning", "PyTorch", "C++"],
    "description": "Designs and implements machine learning algorithms for image/video processing and computational photography within Camera Hardware Engineering.",
    "ats_type": "direct",
    "is_active": True
  }
]

inserted = 0
for j in jobs:
    try:
        sb.table("jobs").upsert(j, on_conflict="apply_url").execute()
        inserted += 1
    except Exception as e:
        print(f"Error inserting {j['title']}: {e}")

print(f"Successfully inserted/upserted {inserted} verified Apple & Meta positions into Supabase!")
