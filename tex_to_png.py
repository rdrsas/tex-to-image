import os
import subprocess
import tempfile
from pathlib import Path
import re
import time
def worker(tex_path):
    return tex_path, process_tex_file(tex_path)

PDFLATEX_PATH = "/Library/TeX/texbin/pdflatex"  # Update if necessary

def find_tex_files(root_dir):
    tex_files = []
    for root, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith('.tex'):
                tex_files.append(os.path.join(root, file))
    return tex_files

def extract_table_content(tex_file_path):
    with open(tex_file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    match = re.search(r'\\begin{table}.*?\\end{table}', content, re.DOTALL)
    if match:
        return match.group(0), True

    for env in ['tabular', 'tabularx', 'longtable']:
        match = re.search(rf'\\begin{{{env}}}.*?\\end{{{env}}}', content, re.DOTALL)
        if match:
            return match.group(0), False

    return None, False

def create_latex_document(table_content, is_full_table):
    # Replace numbered caption with unnumbered caption with label
    table_content = re.sub(
        r'\\caption\{(.*?)\}',
        lambda m: f'\\caption*{{Table: {m.group(1).strip()}}}',
        table_content,
        flags=re.DOTALL
    )

    preamble = r'''\documentclass[12pt]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{geometry}
\usepackage{booktabs,array,longtable,multirow,multicol,amsmath,amssymb,siunitx,tabularx,ltxtable,caption,threeparttable,dcolumn,xcolor}
\geometry{landscape, paperwidth=22in, paperheight=17in, margin=1in}
\pagestyle{empty}
\pagecolor{white}
\color{black}
\begin{document}
%s
\end{document}
'''

    if not is_full_table:
        table_content = r"\begin{table}[ht]\centering\n" + table_content + "\n\\end{table>"

    return preamble % table_content

def compile_latex_to_pdf(tex_str, temp_dir):
    tex_path = os.path.join(temp_dir, "table.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write(tex_str)

    subprocess.run([
        PDFLATEX_PATH,
        "-interaction=nonstopmode",
        "-output-directory", temp_dir,
        tex_path
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    pdf_path = os.path.join(temp_dir, "table.pdf")
    return pdf_path if os.path.exists(pdf_path) else None

def crop_pdf_to_image(pdf_path, output_path):
    raw_png = str(output_path).replace(".png", "_raw.png")
    final_png = str(output_path)

    # Step 1: Convert PDF to PNG (high resolution)
    subprocess.run([
        "magick",
        "-density", "450",
        pdf_path,
        "-background", "white",
        "-alpha", "remove",
        "-alpha", "off",
        "PNG:" + raw_png
    ])

    # Step 2: Trim and add white border
    subprocess.run([
        "magick",
        raw_png,
        "-trim",
        "-bordercolor", "white",
        "-border", "150x150",
        final_png
    ])

    if os.path.exists(final_png):
        os.remove(raw_png)
        return True
    return False

def process_tex_file(tex_file_path):
    print(f"▶ Processing: {tex_file_path}")
    table_content, is_full = extract_table_content(tex_file_path)
    if not table_content:
        print("No table found.")
        return False

    with tempfile.TemporaryDirectory() as tmpdir:
        latex_code = create_latex_document(table_content, is_full)
        pdf_path = compile_latex_to_pdf(latex_code, tmpdir)
        if not pdf_path:
            print("PDF not generated.")
            return False

        output_png = Path(tex_file_path).with_suffix('.png')
        if crop_pdf_to_image(pdf_path, output_png):
            print(f"PNG saved: {output_png}")
            return True
        else:
            print("PNG conversion failed.")
            return False

def main():
    root_dir = "../../Results"
    if not os.path.exists(root_dir):
        print(f" Directory not found: {root_dir}")
        return

    tex_files = find_tex_files(root_dir)
    if not tex_files:
        print(f" No .tex files found in {root_dir}")
        return

    print(f"🔍 Found {len(tex_files)} LaTeX files.")
    start = time.time()
    success = 0
    failure = 0

    # SERIAL processing (safe in notebooks)
    for tex_file in tex_files:
        result = process_tex_file(tex_file)
        if result:
            success += 1
        else:
            failure += 1

    elapsed = time.time() - start
    print(f"\n Done. Successful: {success}, Failed: {failure}, Total: {len(tex_files)}")
    print(f"⏱ Total time: {elapsed:.2f} seconds")


if __name__ == "__main__":
    main()
