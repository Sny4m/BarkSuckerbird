def escape_html(text):
    # telegram markdown ke liye
    html_escape_map = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;",
        "/": "&#47;"
    }
    return ''.join(html_escape_map.get(c, c) for c in text)