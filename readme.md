# Galad Islands

Galad Islands is a game developed with PyGame.

## Description

Galad Islands is an adventure game where the player explores mysterious islands, and faces enemies to uncover the secrets of the archipelago.

## Installation

Clone the repository and install the dependencies:

```bash
git clone https://github.com/Fydyr/Galad-Islands.git
cd Galad-Islands
python setup_dev.py # ou python3 setup_dev.py -- Ce script crée un environnement virtuel, installe les dépendances principales et de développement
```

## Dependencies

### Game Dependencies

- [pygame](https://www.pygame.org/)
- [numpy](https://numpy.org/)
- [numba](https://numba.pydata.org/)
- [llvmlite](https://llvmlite.readthedocs.io/)
- [esper](https://esper.readthedocs.io/)
- [Pillow](https://python-pillow.org/)
- [tomli](https://tomli.readthedocs.io/)
- [scikit-learn](https://scikit-learn.org/)
- [joblib](https://joblib.readthedocs.io/)

### Development Dependencies

- [markdown](https://python-markdown.github.io/)
- [tkhtmlview](https://pypi.org/project/tkhtmlview/)
- [commitizen](https://commitizen-tools.github.io/commitizen/)
- [mkdocs](https://www.mkdocs.org/)
- [mkdocs-material](https://squidfunk.github.io/mkdocs-material/)
- [pytest](https://docs.pytest.org/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [pytest-mock](https://pypi.org/project/pytest-mock/)
- [psutil](https://psutil.readthedocs.io/)
- 

Make sure to list all libraries used in your `requirements.txt`.

## How to Run

To start the game, run the main file:

```bash
python main.py
```

## How to Build

To create a standalone executable, use PyInstaller:

```bash
pyinstaller --onefile main.py --name galad-islands --add-data "assets:assets"
```


## Features

- Procedurally generated islands
- Basic combat system
- IA for troops

## License

This project is licensed under the MIT License.

---

### Command to install the project's requirements

```bash
pip install -r requirements.txt
```
