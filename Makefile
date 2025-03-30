build:
	python -m nuitka --standalone --include-package=OpenGL --include-package=OpenGL_accelerate --follow-imports main.py	