from plyer import notification

def notify(title, message):
        # Truncate title and message to fit within the 64-character limit
    max_length = 64
    truncated_title = title[:max_length]
    truncated_message = message[:max_length]

    notification.notify(
        title=truncated_title,
        message=truncated_message,
        app_name="Job Watcher",
        timeout=10
    )