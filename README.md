# CodeChat IDE: AI-Powered Development Environment

CodeChat IDE is a web-based integrated development environment (IDE) that integrates a powerful AI coding assistant to streamline your development workflow. It features a real-time file explorer, a code editor with syntax highlighting, and an interactive chat panel to generate, refactor, and understand code with the help of AI.

## Features

*   **AI-Powered Chat**: Interact with an intelligent AI assistant to generate code, refactor existing code, answer programming questions, and more.
*   **Real-time File Explorer**: Browse and manage your project files and folders within a sandboxed `agentic_coder` directory. Updates automatically reflect file system changes.
*   **Code Editor**: Edit code directly in the browser with basic syntax highlighting.
*   **Code Execution**: Run Python and JavaScript code snippets directly from the IDE and view the output.
*   **Session Management**: Backend handles sessions for AI interactions.

## Technologies Used

### Frontend

*   **React**: A JavaScript library for building user interfaces.
*   **Vite**: A fast build tool for modern web projects.
*   **TypeScript**: A typed superset of JavaScript that compiles to plain JavaScript.
*   **Shadcn UI**: A collection of re-usable components built using Radix UI and Tailwind CSS.
*   **Tailwind CSS**: A utility-first CSS framework for rapidly building custom designs.
*   **React Router**: For declarative routing in React applications.
*   **Socket.IO Client**: For real-time communication with the backend.

### Backend

*   **Flask**: A lightweight Python web framework.
*   **Flask-CORS**: Enables Cross-Origin Resource Sharing (CORS) for Flask applications.
*   **Flask-SocketIO**: Integrates Socket.IO with Flask for WebSocket communication.
*   **Watchdog**: Python library to monitor file system events.
*   **Google ADK (Agent Development Kit)**: Used for building the AI agent system.
*   **Pydantic**: Data validation and settings management using Python type hints.
*   **Requests**: HTTP library for Python.

## Setup Instructions

Follow these steps to get the CodeChat IDE up and running on your local machine.

### Prerequisites

*   Node.js (LTS version recommended)
*   npm (comes with Node.js)
*   Python 3.8+
*   pip (comes with Python)

### 1. Clone the Repository

```bash
git clone <repository_url>
cd digital-ide-buddy
```

### 2. Backend Setup

It's highly recommended to use a Python virtual environment to manage dependencies.

```bash
# Create a virtual environment
python3 -m venv backend/venv

# Activate the virtual environment
source backend/venv/bin/activate  # On Windows, use `backend\venv\Scripts\activate`

# Install backend dependencies
pip install -r backend/requirements.txt
```

### 3. Frontend Setup

```bash
# Navigate to the project root
cd /Users/shashank/Desktop/Security/projects/agentic_ide/digital-ide-buddy

# Install frontend dependencies
npm install
```

## Running the Application

### 1. Start the Backend Server

First, ensure your Python virtual environment is activated (if you deactivated it).

```bash
cd /Users/shashank/Desktop/Security/projects/agentic_ide/digital-ide-buddy/backend
source venv/bin/activate # On Windows, use `venv\Scripts\activate`
python3 app.py
```

The backend server will start on `http://127.0.0.1:5000`.

### 2. Start the Frontend Development Server

In a new terminal, navigate to the project root and start the frontend.

```bash
cd /Users/shashank/Desktop/Security/projects/agentic_ide/digital-ide-buddy
npm run dev
```

The frontend development server will start, usually on `http://localhost:5173`. Your browser should automatically open to this address.

## Usage

*   **Chat with AI**: Use the chat panel on the left to interact with the AI assistant. Type your requests for code generation, refactoring, or general programming questions.
*   **File Explorer**: The left panel of the code editor displays the contents of the `agentic_coder` directory. Click on files to view their content in the editor.
*   **Code Editor**: The right panel is where you can view and edit code.
*   **Run Code**: Use the "Run" button in the editor's toolbar to execute the code currently displayed. The output will appear in the console panel below.
*   **Real-time Updates**: Any changes you make to files within the `agentic_coder` directory (e.g., via the AI, or manually through your OS file system) will automatically reflect in the IDE's file explorer.

## Project Structure

```
digital-ide-buddy/
├── backend/
│   ├── .env                  # Environment variables for backend (e.g., API keys)
│   ├── app.py                # Flask backend application
│   ├── requirements.txt      # Python dependencies
│   ├── llm_coding_agent/     # AI agent logic
│   │   ├── agent.py          # Core AI agent definitions and tools
│   │   └── ...
│   └── venv/                 # Python virtual environment
├── public/                   # Static assets
├── src/
│   ├── components/           # React UI components (ChatPanel, CodeEditor, ResizablePanel, etc.)
│   ├── pages/                # React pages (Index, NotFound)
│   ├── App.tsx               # Main React application component
│   ├── main.tsx              # React entry point
│   └── ...
├── .gitignore
├── package.json              # Frontend dependencies and scripts
├── README.md                 # This file
├── tailwind.config.ts
├── tsconfig.json
├── vite.config.ts
└── ...
```