import pyglet

pyglet.font.add_file("./assets/alagard.ttf")


def _cross_platform_name(name: str) -> str:
    if pyglet.compat_platform == "linux":
        return name.lower()

    return name


class WindowData:
    width = 1600
    height = 900
    scale = (width / 1600, height / 900)
    window_icon = pyglet.image.load("./assets/icon.png")
    font = _cross_platform_name("Alagard")
