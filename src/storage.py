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
        """Load active session if exists. Returns None if corrupted."""
        if not self.active_file.exists():
            return None
        
        try:
            with open(self.active_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            # JSON corrupted - log and return None
            print(f"⚠️  Warning: Active session file corrupted. Starting fresh.")
            # Backup corrupted file
            backup_path = self.active_file.with_suffix('.json.backup')
            try:
                self.active_file.rename(backup_path)
                print(f"   Corrupted file backed up to: {backup_path}")
            except Exception:
                pass
            return None
    
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
        
        # Backup existing file before writing
        if self.history_file.exists():
            backup_path = self.history_file.with_suffix('.json.bak')
            try:
                import shutil
                shutil.copy2(self.history_file, backup_path)
            except Exception:
                pass  # Continue even if backup fails
        
        with open(self.history_file, 'w') as f:
            json.dump(history, f, indent=2)
    
    def load_history(self) -> List[Dict]:
        """Load all completed sessions. Returns empty list if corrupted."""
        if not self.history_file.exists():
            return []
        
        try:
            with open(self.history_file, 'r') as f:
                data = json.load(f)
                # Validate that it's a list
                if not isinstance(data, list):
                    print("⚠️  Warning: History file has invalid format. Starting fresh.")
                    return []
                return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"⚠️  Warning: History file corrupted. Starting fresh.")
            # Backup corrupted file
            backup_path = self.history_file.with_suffix('.json.corrupted')
            try:
                self.history_file.rename(backup_path)
                print(f"   Corrupted file backed up to: {backup_path}")
            except Exception:
                pass
            return []
