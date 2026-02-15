"""State manager for tracking display state across processes."""

import json
import os
from datetime import datetime
from pathlib import Path
from utils.logger import get_logger

logger = get_logger()

# State file location - in the project root
STATE_FILE = Path(__file__).parent.parent.parent / 'state.json'


def save_state(last_updated=None, current_view=None):
    """
    Save display state to file.

    Args:
        last_updated: ISO format timestamp string or None to use current time
        current_view: Current view name (two_week, month, week, agenda, four_day)

    Returns:
        dict: The saved state
    """
    try:
        if last_updated is None:
            last_updated = datetime.now().isoformat()

        state = {
            'last_updated': last_updated,
            'current_view': current_view,
            'state_updated': datetime.now().isoformat()
        }

        # Ensure parent directory exists
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)

        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)

        logger.debug(f"State saved: {state}")
        return state
    except Exception as e:
        logger.error(f"Failed to save state: {e}")
        return None


def load_state():
    """
    Load display state from file.

    Returns:
        dict: State dictionary with keys 'last_updated' and 'current_view', or None if file doesn't exist
    """
    try:
        if not STATE_FILE.exists():
            logger.debug(f"State file not found at {STATE_FILE}")
            return None

        with open(STATE_FILE, 'r') as f:
            state = json.load(f)

        logger.debug(f"State loaded: {state}")
        return state
    except Exception as e:
        logger.error(f"Failed to load state: {e}")
        return None


def get_last_updated():
    """
    Get the last update timestamp.

    Returns:
        str: ISO format timestamp or None
    """
    state = load_state()
    return state.get('last_updated') if state else None


def get_current_view():
    """
    Get the current view from state.

    Returns:
        str: View name or None
    """
    state = load_state()
    return state.get('current_view') if state else None
