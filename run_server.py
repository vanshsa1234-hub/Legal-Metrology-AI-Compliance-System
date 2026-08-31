"""
Legal Lens - Server Launcher
Runs the FastAPI backend and serves the frontend on http://localhost:8000
"""
import uvicorn

if __name__ == "__main__":
    print("=" * 70)
    print("  LEGAL LENS - SMART INDIA HACKATHON PROTOTYPE")
    print("  AI-Assisted Consumer Compliance & Product Inspection System")
    print("=" * 70)
    print("\n  Open your web browser at:")
    print("  http://127.0.0.1:8000\n")
    print("  Demo Credentials:")
    print("  - Citizen User:  user@legallens.demo  /  user123")
    print("  - Officer/Admin: admin@legallens.demo /  admin123\n")
    print("=" * 70)

    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True)
