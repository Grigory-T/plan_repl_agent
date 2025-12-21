**planning agent with repl**  

# how to run:

```bash
git clone https://github.com/Grigory-T/plan_repl_agent
cd plan_repl_agent
docker compose build
docker compose up -d
```

then create .env file with OPENROUTER_API_KEY

```bash
# write some task in runner.py
# use e.g. task_sample variable
python3 runner.py  # or python runner.py
```

# to see how agent works:
[youtube](https://www.youtube.com/watch?v=6erdpQyXLaI)  
[vkvideo](https://vkvideo.ru/video-228427241_456239018)  


# more detailed habr article
[habr](https://habr.com/ru/articles/977062/)  


# files and folders overivew
/agent - main code  
/lib - technical folder for agent, realted to `pip install` functionality  
/logs - all steps with detaild thinking process. shows agent logic. logs based on .txt files  
/work - agent working directory, for file operations  
/runner.py - use to start agent


# important notes
- agent runs in docker, non-root user
- agent can execute any python and bash commands (**take into account security issues**)
- agent can pip install ...
- agent cannot apt-get ...

# windows
preferably run linux to run agent (i used ubuntu 24)   
if run on windows:  
need to install docker desktop for windows

correct .sh file line endings:  
```bash
(Get-Content docker-entrypoint.sh -Raw) -replace "`r`n","`n" | Set-Content docker-entrypoint.sh -NoNewline
```
