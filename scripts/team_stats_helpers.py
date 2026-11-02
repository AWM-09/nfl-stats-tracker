"""Shared filters for team-level play-by-play calculations."""

def is_fourth_down_attempt(play_type):
    """Only count snaps that attempt to gain a first down.

    Fake punts and field goals remain eligible when classified as a run or pass.
    """
    return str(play_type or "").strip().lower() in {"run", "pass"}
