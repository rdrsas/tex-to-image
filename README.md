# LaTeX Table to Image (.png)

I use this to generate high-dpi image files for my LaTeX tables (primarily regression tables from Stata). You will have to change root_folder under main to the folder where your .tex files are located and PDFLATEX_PATH to where your pdflatex is located.

The program looks for every .tex file in a given folder and generates an image of the same in the sub-folder the relevant file is in. It does so by processing it using pdflatex (thus, you will need a local TeX distribution), recognizing table borders and getting a snap of the same with an appropriate amount of margins.
