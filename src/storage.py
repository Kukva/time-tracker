import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

class Storage:
    """Handles data persistence for time tracking."""
    
    def __init__(self, data_dir: str = "~/.timetracker"):
        self.data_dir = Path(data_dir).expanduser()
        self.data_dir.mkdir(exist_ok=True)
        self.active_file = self.data_dir / "active.json"
        self.history_file = self.data_dir / "sessions.json"
    
    def save_active_session(self, task: str, start_time: str) -> None:
        """Save currently active session."""
        data = {"task": task, "start_time": start_time}
        with open(self.active_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def load_active_session(self) -> Optional[Dict]:
        """Load active session if exists."""
        if not self.active_file.exists():
            return None
        with open(self.active_file, 'r') as f:
            return json.load(f)
    
    def clear_active_session(self) -> None:
        """Remove active session file."""
        if self.active_file.exists():
            self.active_file.unlink()
    
    def save_completed_session(self, task: str, start_time: str, 
                               end_time: str, duration_seconds: int) -> None:
        """Append completed session to history."""
        session = {
            "task": task,
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": duration_seconds
        }
        
        history = self.load_history()
        history.append(session)
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def load_history(self) -> List[Dict]:
        """Load all completed sessions."""
        if not self.history_file.exists():
            return []
        with open(self.history_file, 'r') as f:
            return json.load(f)