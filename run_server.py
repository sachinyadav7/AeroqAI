"""Launch script for AeroqAI FastAPI REST server."""
import sys
import uvicorn


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=" * 80)
    print(" 🚀 Launching AeroqAI REST API Server on http://127.0.0.1:8000")
    print(" 📖 Interactive Swagger API Docs : http://127.0.0.1:8000/docs")
    print(" 📖 ReDoc Alternative API Docs  : http://127.0.0.1:8000/redoc")
    print("=" * 80)

    uvicorn.run(
        "AeroqAI.api.app:app",
        host="127.0.0.1",
        port=8000,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
