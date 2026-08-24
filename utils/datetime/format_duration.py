def format_duration(duration):
    if duration is None:
        return ""
    total_seconds = int(duration.total_seconds())

    hours, remainder = divmod(total_seconds, 3600)
    minutes = remainder // 60

    if hours and minutes:
        return f"{hours} hr {minutes} min"

    if hours:
        return f"{hours} hr"

    return f"{minutes} min"
