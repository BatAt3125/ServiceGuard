---

# Contributing to Windows Service Manager

First off, thank you for considering contributing to this project! It is through contributors like you that tools become more reliable and user-friendly.

Please take a moment to review these guidelines to ensure a smooth collaboration process.

---

## Project Standards

### UI & Aesthetics
Since this project prioritizes a refined and modern visual experience, all contributions must adhere to our design language:
*   **Transparency**: Maintain layer transparency in navigation tabs and lists.
*   **Custom Styling**: Any new tabs must use the project's custom-styled interface.
*   **UI Consistency**: Backgrounds should be transparent rather than solid white where specified to prevent obscuring background graphics.

### System Safety
Safety is a core pillar of this application:
*   **Critical Services**: If you suggest adding new features to the service management logic, you must ensure that vital system services (like RPC or PlugPlay) remain protected.
*   **User Warnings**: Any action that could lead to system instability must trigger a `QMessageBox` warning before execution.

---

## How Can I Contribute?

### Reporting Bugs
If you find a bug, please open an issue and include:
*   Your version of Windows.
*   Steps to reproduce the error (e.g., "The `NoneType` error occurs when clicking service 'X'").
*   A screenshot if it relates to UI/UX issues, such as scrollbar glitches.

### Suggesting Enhancements
We welcome ideas for:
*   New mathematical task types for the educational module.
*   Visual refinements to the `ServiceItemWidget`.
*   Performance optimizations for service status polling.

### Pull Requests
1.  **Fork the repository** and create your branch from `main`.
2.  **Follow the code style**: Use `snake_case` for Python functions and `CamelCase` for PyQt5 classes.
3.  **Document your changes**: Update the `README.md` if you add new features.
4.  **Test your code**: Ensure that your changes do not introduce `NoneType` errors or break the UI transparency.

---

## Development Setup

1.  **Clone the repo**: `git clone [https://github.com/your-username/repository-name.git](https://github.com/your-username/repository-name.git)`
2.  **Create a virtual environment**: `python -m venv venv`
3.  **Install dependencies**: `pip install -r requirements.txt`
4.  **Run with Admin rights**: Managing Windows services requires administrative privileges.

---

## Code of Conduct
By participating in this project, you agree to maintain a respectful and professional environment for all contributors.

---

**Happy Coding!**
