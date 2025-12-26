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
```

## Step 2: Run a Task

Specify a task file using the `-i` option:

```bash
# Run with a specific task file
python runner.py -i task_sample.txt

# Run without arguments (uses default test task)
python runner.py
```

**Sample task files** (examples located in `tasks` folder):

**Create your own task**: simply create a `.txt` file with your task description and pass it via `-i`.

# to see how agent works:
[youtube](https://www.youtube.com/watch?v=6erdpQyXLaI)  
[vkvideo](https://vkvideo.ru/video-228427241_456239018)  


# more detailed habr article
[habr](https://habr.com/ru/articles/977062/)  


# files and folders overview
- `/agent` - main code (runs in Docker server)
- `/lib` - technical folder for agent, related to dynamic `pip install` functionality during execution  
- `/logs` - all steps with detailed thinking process, shows agent logic, logs based on .txt files  
- `/work` - agent working directory, for file operations  
- `/tasks` - one file for each task
- `/runner.py` - client to start agent (connects to Docker server)
- `requirements.txt` - will be installed in docker (will be used by agent)


# important notes
- **architecture**: Docker container = agent server (required), `runner.py` = client
- agent runs in docker container, non-root user
- agent can execute any python and bash commands (**take into account security issues**)
- agent can dynamically pip install packages during execution (inside docker container)
- agent cannot apt-get ...

# windows
preferably run linux to run agent (i used ubuntu 24)   
if run on windows:  
need to install docker desktop for windows

# log time zone
hard coded to TZ=Europe/Moscow  
see file: docker-compose.yml  
