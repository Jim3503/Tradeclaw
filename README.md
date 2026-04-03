# Tradeclaw Crew

Welcome to the Tradeclaw Crew project, powered by [crewAI](https://crewai.com). This is an advanced multi-agent AI trading analysis system with a sophisticated three-layer memory architecture for continuous learning and improved decision-making.

## Features

### 🤖 Multi-Agent Trading System
- **Data Fetcher Agent**: Retrieves real-time market data, hot sectors, and stock prices
- **Narrative Analyst**: Analyzes market narratives and identifies key themes
- **Technical Analyst**: Provides technical analysis with momentum indicators
- **Report Compiler**: Integrates all analysis into comprehensive daily reports

### 🧠 Advanced Memory System
- **Three-Layer Memory Architecture**: Policy, Episodic, and Reflection memories
- **Intelligent Retrieval**: BM25-based search with scope filtering
- **Continuous Learning**: Outcome tracking and effectiveness validation
- **Prompt Optimization**: Structured for efficient LLM consumption

For detailed information about the memory system, see [MEMORY_README.md](MEMORY_README.md)

## Quick Start

Ensure you have Python >=3.10 <3.14 installed on your system. This project uses [UV](https://docs.astral.sh/uv/) for dependency management and package handling, offering a seamless setup and execution experience.

First, if you haven't already, install uv:

```bash
pip install uv
```

Next, navigate to your project directory and install the dependencies:

(Optional) Lock the dependencies and install them by using the CLI command:
```bash
crewai install
```
### Customizing

**Add your `OPENAI_API_KEY` into the `.env` file**

- Modify `src/tradeclaw/config/agents.yaml` to define your agents
- Modify `src/tradeclaw/config/tasks.yaml` to define your tasks
- Modify `src/tradeclaw/crew.py` to add your own logic, tools and specific args
- Modify `src/tradeclaw/main.py` to add custom inputs for your agents and tasks

## Running the Project

To kickstart your crew of AI agents and begin task execution, run this from the root folder of your project:

```bash
$ crewai run
```

This command initializes the tradeclaw Crew, assembling the agents and assigning them tasks as defined in your configuration.

This example, unmodified, will run the create a `report.md` file with the output of a research on LLMs in the root folder.

## Understanding Your Crew

The tradeclaw Crew is composed of multiple AI agents, each with unique roles, goals, and tools. These agents collaborate on a series of tasks, defined in `config/tasks.yaml`, leveraging their collective skills to achieve complex objectives. The `config/agents.yaml` file outlines the capabilities and configurations of each agent in your crew.

Let's create wonders together with the power and simplicity of crewAI.
