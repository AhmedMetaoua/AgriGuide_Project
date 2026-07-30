# 🌾 AI Agricultural Business Advisor

An intelligent, data-driven agricultural decision advisor built with **FastAPI**, **LangGraph**, and **Mistral AI**. 

This system bridges the gap between local agronomic soil recommendations and macro-economic market trends. It analyzes historical INSEE agricultural price index data (`FDS_IPPAP` datasets from 2020–2026) using custom Pandas tooling to determine the most profitable and stable crop strategy for a given region and season.

---

## 🛠️ Tech Stack

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/)
* **Agentic Framework:** [LangGraph](https://www.langchain.com/langgraph) & [LangChain](https://www.langchain.com/)
* **LLM Provider:** [Mistral AI](https://mistral.ai/) (`mistral-medium-latest`)
* **Data Processing:** [Pandas](https://pandas.pydata.org/)
* **ASGI Server:** [Uvicorn](https://www.uvicorn.org/)

---

## 🚀 Quickstart & Setup Guide

Follow these steps to clone, configure, and run the project locally on your machine.

### 1. Clone the Repository

```bash   // git clone <YOUR_GITHUB_REPOSITORY_URL>
cd agri_advisor



 2.Set Up a Virtual Environment :
python -m venv venv
.\venv\Scripts\Activate.ps1


3. Install Dependencies
pip install -r requirements.txt

4. Configure Your API Key
On Windows (vscode_PowerShell):  $env:MISTRAL_API_KEY="your_mistral_api_key_here"

⚡ Running the API Server :
uvicorn main:app --reload

Finally go to the link : 👉 http://127.0.0.1:8000/docs



