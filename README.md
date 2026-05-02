# ServiceGuard - Windows Service Manager

A Python-based desktop application built with **PyQt6** designed to manage Windows services with a focus on high-end UI/UX and system safety. This tool allows users to monitor, start, and stop services through a modern, refined interface that prioritizes visual clarity and prevents accidental system instability.

---

### Key Features

*   **System Safety Protocol**: Includes a built-in guard that identifies "Critical Windows Services" (like RPC, PlugPlay, and Power). If a user attempts to stop a vital service, the app triggers a warning dialog to prevent accidental system crashes.
*   **Refined UI/UX**: Features a custom-styled interface with a focus on transparency and professional aesthetics.
    *   **Custom Scrollbars**: Fully stylized scrollbars designed to blend seamlessly with the application's theme.
    *   **Layer Transparency**: Strategic use of transparent backgrounds in navigation tabs and service lists to maintain a clean, modern look.
*   **Real-time Monitoring**: Displays the current status of services with intuitive color-coded indicators.
*   **Smart Search/Filter**: Easily navigate through the extensive list of system services.

---

### Why This Project?

Managing Windows services can be risky for inexperienced users. This project provides:
1.  **A Safety Net**: By categorizing and protecting essential services, it reduces the risk of BSOD (Blue Screen of Death).
2.  **Educational Value**: Helps users understand the hierarchy and importance of different system processes.
3.  **Modern Alternative**: Offers a more visually appealing and user-friendly experience compared to the default Windows `services.msc`.

---

### Getting Started

#### Prerequisites
*   Windows OS
*   Python 3.9+
*   PyQt6

#### Code Installation
1.  **Clone the repository**:
    ```bash
    git clone https://github.com/your-username/windows-service-manager.git
    ```
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Run the application**:
    > **Note**: Running as Administrator is required to manage (start/stop) certain services.
    ```bash
    python main.py
    ```

---

### How to Get Help
If you encounter any issues or have questions regarding service management:
*   Open an **Issue** on the GitHub repository.
*   Check the **Wiki** section for detailed documentation on critical services.
*   
---

### Contributors and Maintenance
*   **Project Lead**: BatAt3125 – Focused on UI refinement and logic implementation.
*   **Contributions**: We welcome contributions! Please refer to our `CONTRIBUTING.md` for guidelines on how to participate in the development of the math task generation or UI components.

---

### License
This project is licensed under the MIT License - see the `LICENSE` file for details.
