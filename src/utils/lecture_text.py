def create_lecture_text(attrs):
    lecture_text = ""

    for attr in attrs:
        title = attr.title.strip()
        text = attr.text.strip() if attr.text else None

        if title and title[-1] not in [".", "?", "!"]:
            title += '.'

        if text and text[-1] not in [".", "?", "!"]:
            text += '.'

        lecture_text += f"{title}\n{text}\n"
    return lecture_text

