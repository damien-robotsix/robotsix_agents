# Robotsix Agents: A Multi-Agent System for Automated Repository Management

This repository contains the source code for "Robotsix Agents," a sophisticated multi-agent system designed to automate and streamline repository management. The system leverages a team of specialized AI agents, each with a distinct role, to handle tasks ranging from code implementation and validation to version control and task organization. By working together, these agents provide a powerful and efficient solution for managing software development projects.

### Features

*   **Multi-Agent System:** Robotsix Agents is a collaborative team of specialized AI agents that work in unison to manage your repository.
*   **Specialized Agents:** Each agent is an expert in its domain:
    *   **Coding Specialist:** Handles file I/O, code implementation, and solution validation.
    *   **Git Assistant:** Manages all version control tasks, including commits, branches, and merges.
    *   **Repository Parser:** Indexes and performs semantic searches on the repository content for efficient information retrieval.
    *   **GitHub Agent:** Integrates with GitHub to streamline workflows.
    *   **Task Organizer:** Manages project tasks and maintains a TODO list to keep development on track.
*   **Automated Repository Operations:** The agent team automates complex workflows, from coding and testing to version control and task management.
*   **Collaborative Environment:** Agents coordinate their actions within a `SelectorGroupChat`, ensuring seamless and efficient task execution.
*   **Extensible by Design:** The modular architecture makes it easy to extend the system by adding new agents with unique capabilities.

### Installation

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/your-username/robotsix-agents.git
    cd robotsix-agents
    ```

2.  **Install the package:**

    It is recommended to install the package in a virtual environment.

    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install .
    ```

3.  **Initialize the configuration:**

    The agents require a configuration setup to define their behavior. Run the following command to initialize the default configuration:

    ```bash
    robotsix-agents init
    ```

    This will create the necessary configuration files in your user's home directory.

### Usage

To run the multi-agent system, use the `run` command and provide a task for the agents to complete.

```bash
robotsix-agents run "Your task description here"
```

The agents will then collaborate to handle the request. For example, if you ask the agents to "implement a new feature," the Task Organizer will create a TODO list, the Coding Specialist will write the code, and the Git Assistant will commit the changes.

### Contributing

We welcome contributions to Robotsix Agents! To ensure a smooth and collaborative process, please follow these guidelines:

**1. Fork and Clone the Repository**

Start by forking the repository to your own GitHub account and then clone it to your local machine:

```bash
git clone https://github.com/your-username/robotsix-agents.git
cd robotsix-agents
```

**2. Create a Virtual Environment and Install Dependencies**

It is recommended to work in a virtual environment to manage project dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -e '.[dev]'
```

The `-e` flag installs the package in "editable" mode, which allows you to make changes to the source code and have them immediately reflected in your environment. The `[dev]` extra installs the development dependencies.

**3. Create a New Branch**

Create a new branch for your feature or bug fix:

```bash
git checkout -b my-new-feature
```

**4. Make Your Changes**

Make your desired changes to the codebase. If you are adding a new agent or modifying an existing one, please ensure you also include or update the corresponding tests in the `tests/` directory.

**5. Run the Tests**

Before submitting your contribution, please run the test suite to ensure that your changes do not break any existing functionality:

```bash
pytest
```

**6. Submit a Pull Request**

Once you are satisfied with your changes and all tests pass, push your branch to your forked repository and open a pull request. Provide a clear and concise description of the changes you have made and the problem they solve.

### License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
