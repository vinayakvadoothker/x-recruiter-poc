# Grok Recruiter - Demo Script

## Overview
This document outlines the step-by-step demo flow for the Grok Recruiter system.

## Demo Flow

### Step 1: Start the System
```bash
# Terminal 1: Start FastAPI server
cd /path/to/x-recruiter-poc
uvicorn backend.api.main:app --reload

# Terminal 2: Start Streamlit dashboard (optional)
streamlit run backend/demo/dashboard.py
```

### Step 2: Recruiter Requests Role
**Via X DM Simulator (CLI) or API:**

```
Recruiter: "I need an LLM inference optimization engineer for xAI"
```

**Expected System Response:**
```
@x_recruiting: "I'd be happy to help! Can you provide more details about:
- Required skills (e.g., CUDA, PyTorch, distributed systems)
- Experience level (junior, mid, senior)
- Timeline and location preferences"
```

### Step 3: Recruiter Provides Details
```
Recruiter: "We need someone with:
- 5+ years experience with CUDA kernel optimization
- Experience with multi-GPU tensor parallelism
- Knowledge of transformer architecture internals
- Experience with >100B parameter models
- Understanding of KV cache optimization"
```

**Expected System Response:**
```
@x_recruiting: "Got it! Sourcing candidates now..."
[System processes role request]
@x_recruiting: "I found 25 candidates. Top 5:

1. @candidate1 (Match: 87%)
2. @candidate2 (Match: 82%)
3. @candidate3 (Match: 79%)
4. @candidate4 (Match: 76%)
5. @candidate5 (Match: 74%)

Should I reach out to these candidates?"
```

### Step 4: System Shows Candidate List
**Via Dashboard or API:**
- Display candidate profiles
- Show graph similarity scores
- Show bandit algorithm scores
- Display skills and experience

### Step 5: Recruiter Provides Feedback
```
Recruiter: "Actually, candidate #3 isn't qualified - they don't have CUDA experience"
```

**Expected System Response:**
```
@x_recruiting: "Got it, updating my criteria. Here's a refined list with better matches..."
[System updates bandit with negative feedback]
[System shows improved candidate recommendations]
```

### Step 6: System Sends Outreach
```
Recruiter: "Yes, reach out to top 10 candidates"
```

**Expected System Response:**
```
@x_recruiting: "Sending personalized outreach messages to 10 candidates..."
[System generates and sends messages via simulator/X API]
@x_recruiting: "5 candidates responded. Sending technical assessment..."
```

### Step 7: Show Learning Metrics
**Via Dashboard:**
- Display learning curves (warm-start vs cold-start)
- Show response rates over time
- Display improvement metrics
- Show bandit state (alpha/beta values)

### Step 8: Demonstrate Improvement
**Key Points to Highlight:**
- "System learned from feedback - match quality improved from 60% to 85%"
- "Response rate improved from 15% to 35% after 20 interactions"
- "Graph warm-start enabled 3x faster learning compared to cold-start"

## Sample Role Description

```
Role: LLM Inference Optimization Engineer

We're looking for an engineer to optimize LLM inference for large-scale deployment.

Required Skills:
- CUDA kernel optimization
- Multi-GPU tensor parallelism
- PyTorch FSDP and DeepSpeed
- Transformer architecture internals
- LLM inference latency optimization
- Multi-node GPU cluster management

Experience:
- 5+ years in ML infrastructure
- Experience with >100B parameter models
- Understanding of KV cache optimization
- Knowledge of quantization techniques (FP8, INT4)
- Experience with custom attention implementations
- Background in HPC or ML infrastructure at scale
```

## Key Talking Points

1. **Graph-Warm-Started FG-TS**: "We use graph structure to warm-start Feel-Good Thompson Sampling, enabling faster learning."

2. **Novel Combination**: "This is the first application of graph structure as prior for bandits in recruiting."

3. **End-to-End System**: "Complete pipeline from sourcing → matching → outreach → learning."

4. **Self-Improving**: "System learns from each interaction and improves candidate matching over time."

5. **Research-Backed**: "Built on three papers: [cite papers from CITATIONS.md]"

## Demo Checklist

- [ ] FastAPI server running
- [ ] Dashboard accessible (if using)
- [ ] API keys configured (.env file)
- [ ] Sample role description ready
- [ ] Demo flow tested end-to-end
- [ ] Learning metrics visible
- [ ] Backup demo video recorded (optional)

## Troubleshooting

**If candidates not found:**
- Check GitHub API token
- Verify role description has sufficient detail
- Check API rate limits

**If Grok API errors:**
- Verify GROK_API_KEY is set
- Check API quota/limits
- Review error logs

**If dashboard not loading:**
- Ensure Streamlit is installed
- Check port conflicts
- Review console errors

