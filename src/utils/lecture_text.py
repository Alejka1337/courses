from bs4 import BeautifulSoup


def create_lecture_text(attrs: list[str]):
    lecture_text = ""

    for attr in attrs:
        title = attr.title.strip()
        text = attr.text.strip() if attr.text else None
        if text:
            soup = BeautifulSoup(text, 'html.parser')
            text = soup.get_text(strip=True)

        if title and title[-1] not in [".", "?", "!"]:
            title += '.'

        if text and text[-1] not in [".", "?", "!"]:
            text += '.'

        lecture_text += f"{title}\n{text}\n"
    return lecture_text

