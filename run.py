"""
StockSathi Application Launcher
Starts the FastAPI server serving both the REST APIs and the rich HTML/CSS/JS frontend.
"""

import sys
import os

if __name__ == "__main__":
    import uvicorn
    from backend.config import config
    
    print("=" * 65)
    print("  STOCKSATHI — Smart Retail Decision Engine")
    print("  PREDICT -> DECIDE -> RECOMMEND -> ACT")
    print(f"  Server starting at: http://127.0.0.1:{config.PORT}")
    print("=" * 65)
    
    uvicorn.run("backend.server:app", host=config.HOST, port=config.PORT, reload=True)
