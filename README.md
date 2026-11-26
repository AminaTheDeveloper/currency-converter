# currency-converter
Desktop currency converter built with Python and CustomTkinter, featuring live exchange rates for 160+ currencies via ExchangeRate-API.

## Features

- **160+ Currencies:** Fetches live USD-based rates from ExchangeRate-API and computes cross-currency conversions dynamically (`USD` to `PKR` by default).
- **Live & On-Demand Conversion:** Recalculates automatically as you type in the amount field, or converts on demand by clicking **Convert currency** or pressing **Enter**.
- **One-Click Currency Swap (`⇅`):** Swaps `FROM` and `TO` currencies and immediately updates the converted amount and unit rate.
- **Background Rate Refresh (`↻`):** Fetches and refreshes exchange rates on a background thread so the interface remains responsive.
- **Input Validation:** Supports comma-formatted numbers (such as `1,250.50`) and displays clear status or dialog feedback for invalid or non-positive amounts.
- **Windows Desktop Placement:** Sizes and centers the window within the active Windows work area while accounting for display scaling.

## Project Structure

```text
├── Currency Exchange GUI.py   # Main CustomTkinter application and API client
├── requirements.txt           # Python dependencies
├── .gitignore                 # Excludes local environment files (including .env)
├── .env                       # Local API key configuration (not committed)
└── README.md                  # Project documentation
```

## Prerequisites

- **Windows** (uses `ctypes.windll.user32` for work-area centering and `Segoe UI` typography)
- **Python 3.10+** (tested on Python 3.15)
- A free or paid API key from [ExchangeRate-API](https://www.exchangerate-api.com/)

## Setup & Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/<AminaTheDeveloper>/<currency-converter>.git
   cd <currency-converter>
   ```

2. **Create and activate a virtual environment (recommended)**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure your API key**
   Create a `.env` file in the root directory of the project and add your ExchangeRate-API key:
   ```env
   EXCHANGE_RATE_API_KEY=your_api_key_here
   ```

## Usage

Run the application from the project root:

```powershell
python "Currency Exchange GUI.py"
```

## Dependencies

- [`customtkinter`](https://customtkinter.tomschimansky.com/) (`6.0.0`)
- [`python-dotenv`](https://github.com/theskumar/python-dotenv) (`1.2.4`)

## Notes

- **Keep `.env` private:** Ensure `.env` is listed in `.gitignore` before committing or pushing changes to GitHub so your API key is never exposed publicly.
- **Startup Check:** The application raises a `ValueError` on launch if `EXCHANGE_RATE_API_KEY` is missing from your `.env` file or system environment variables.
