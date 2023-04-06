import pyglet

pyglet.font.add_file("./assets/alagard.ttf")
pyglet.font.add_file("./assets/PirataOne-Regular.ttf")


def _cross_platform_name(name: str) -> str:
    if pyglet.compat_platform == "linux":
        return name.lower()

    return name


class WindowData:
    width = 800
    height = 600
    scale = (width / 800, height / 600)
    window_icon = pyglet.image.load("./assets/icon.png")
    font = _cross_platform_name("Alagard")
