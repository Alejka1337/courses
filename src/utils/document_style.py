from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
from docx.shared import RGBColor
from docx.shared import Pt


class DocumentStyleManager:

    @staticmethod
    def set_paragraph_font_size(p, size: int):
        for run in p.runs:
            run.font.size = Pt(size)

    @staticmethod
    def set_paragraph_font_name(p, name):
        for run in p.runs:
            run.font.name = name

    @staticmethod
    def set_paragraph_indent(p, left, right):
        p.paragraph_format.left_indent = Pt(left)
        p.paragraph_format.right_indent = Pt(right)

    @staticmethod
    def set_paragraph_bold(p):
        for run in p.runs:
            run.bold = True

    @staticmethod
    def set_paragraph_italic(p):
        for run in p.runs:
            run.italic = True

    @staticmethod
    def set_paragraph_text_color(p, r, g, b):
        for run in p.runs:
            run.font.color.rgb = RGBColor(r, g, b)

    @staticmethod
    def set_paragraph_alignment(p, value: str):
        if value == "center":
            p.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER
        elif value == "right":
            p.alignment = WD_PARAGRAPH_ALIGNMENT.RIGHT
        elif value == "left":
            p.alignment = WD_PARAGRAPH_ALIGNMENT.LEFT
        else:
            p.alignment = WD_PARAGRAPH_ALIGNMENT.JUSTIFY

    @staticmethod
    def set_bold_run(run):
        run.bold = True

    @staticmethod
    def set_italic_run(run):
        run.italic = True

    @staticmethod
    def set_underline_run(run):
        run.underline = True

    @staticmethod
    def set_font_size_run(run, size):
        run.font.size = Pt(size)

    @staticmethod
    def set_font_name_run(run, name):
        run.font.name = name

    @staticmethod
    def set_font_color_run(run, r, g, b):
        run.font.color.rgb = RGBColor(r, g, b)

    @staticmethod
    def hex_to_rgb(hex_color):
        hex_color = hex_color.lstrip("#")
        return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
