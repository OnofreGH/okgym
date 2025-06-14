# okgym-whatsapp-app

## Overview
The `okgym-whatsapp-app` is a Python application designed to automate the process of sending WhatsApp messages to clients based on their information stored in an Excel file. The application features a user-friendly interface that allows users to specify the Excel file and customize the message to be sent.

## Project Structure
```
okgym-whatsapp-app
├── src
│   ├── main.py          # Entry point for the application
│   ├── messagewhatsapp.py # Logic for reading client info and sending messages
│   └── ui.py           # User interface definition
├── requirements.txt     # List of dependencies
└── README.md            # Project documentation
```

## Installation
1. Clone the repository:
   ```
   git clone <repository-url>
   cd okgym-whatsapp-app
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage
1. Prepare an Excel file named `Clientes.xlsx` with the following columns:
   - `Celular`: Client's phone number
   - `Nombre`: Client's name
   - `Producto`: Product purchased

2. Run the application:
   ```
   python src/main.py
   ```

3. Use the user interface to select the Excel file and enter the message you wish to send.

4. Click the send button to start sending messages to all clients listed in the Excel file.

## Dependencies
- pandas
- pyautogui

## License
This project is licensed under the MIT License - see the LICENSE file for details.