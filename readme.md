**planning agent with repl**  

# how to run:

## Configuration (Required)

Create `.env` file with `OPENROUTER_API_KEY` and LLM model overrides based on .env.example:

- **OPENROUTER_API_KEY**: required
- **LLM_MODEL_PLAN**: optional (default: `openai/gpt-4.1`)
- **LLM_MODEL_DECISION**: optional (default: `openai/gpt-4.1`)
- **LLM_MODEL_REPLAN**: optional (default: `openai/gpt-4.1`)
- **LLM_MODEL_AGENT**: optional (default: `deepseek/deepseek-v3.2`)

## Step 1: Start Docker server (required)

```bash
git clone https://github.com/Grigory-T/plan_repl_agent
cd plan_repl_agent
docker compose build
docker compose up -d

chown -R 1000:1000 ./
```

## Step 2: Run a Task

```bash
python runner.py  # task could be inserted inside
```

# to see how agent works:
[youtube](https://www.youtube.com/watch?v=6erdpQyXLaI)  
[vkvideo](https://vkvideo.ru/video-228427241_456239018)  


# more detailed habr article
[habr](https://habr.com/ru/articles/977062/)  


# files and folders overview
- `/agent` - main code (runs in Docker)
- `/logs` - all steps with detailed thinking process, shows agent logic
- `/work` - agent working directory, for file operations  
- `/runner.py` - client to start agent (get/post to Docker)
- `requirements.txt` - will be installed in docker (will be used by agent)


# important notes
- **architecture**: Docker container = agent server (required), `runner.py` = simple client
- agent runs in docker container, non-root user (1000)
- agent can execute any python and bash commands (**take into account security issues**)
- agent can dynamically pip install packages during execution (inside docker container)
- agent cannot apt-get  

# windows
need to install docker desktop for windows

# log time zone
hard coded to TZ=Europe/Moscow  
see file: docker-compose.yml  
