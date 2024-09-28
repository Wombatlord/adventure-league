from __future__ import annotations

from typing import Any, Callable, NamedTuple

import arcade
from arcade import gl
from arcade.gl.types import PyGLenum


class Uniform(NamedTuple):
    type_name: str
    name: str


class Sources(NamedTuple):
    vertex_shader: str | None = None
    fragment_shader: str | None = None

    def uniforms(self) -> dict[str, Uniform]:
        uniform_dict = {}
        for source in self:
            if source is None:
                continue

            for line in source.split("\n"):
                if line.startswith("uniform"):
                    _, type_name, name = line[:-1].split(" ")
                    uniform_dict[name] = Uniform(type_name, name)

        return uniform_dict


class Binding(NamedTuple):
    bind_offset: int
    texture: gl.Texture2D
    framebuffer: arcade.gl.Framebuffer

    def capture(self, draw_func: Callable):
        self.framebuffer.clear()
        self.framebuffer.use()
        draw_func()

    def use(self):
        self.texture.use(self.bind_offset)


class NoBinding(NamedTuple):
    bind_offset: int

    def use(self):
        pass


class Shader:
    _program: gl.Program | None = None
    _sources: Sources | None = None
    _bindings: dict[str, Binding | NoBinding]
    _ctx: gl.Context
    _on_use: list[Callable[[gl.Program], None]]

    @staticmethod
    def gen_tx_buf(
        ctx: gl.Context,
        size: tuple[int, int],
        components=4,
        dtype="f4",
        wrapping: tuple[PyGLenum, PyGLenum] = (gl.REPEAT, gl.REPEAT),
    ) -> tuple[arcade.gl.Texture2D, arcade.gl.Framebuffer]:
        tx = ctx.texture(
            size,
            components=components,
            filter=(ctx.NEAREST, ctx.NEAREST),
            dtype=dtype,
            wrap_x=wrapping[0],
            wrap_y=wrapping[1],
        )
        buf = ctx.framebuffer(color_attachments=[tx])
        buf.resize()
        buf.viewport = (0, 0, *size)
        return tx, buf

    def __init__(self, ctx: gl.Context):
        self._ctx = ctx
        self._bindings = {}
        self._on_use = []

    def load_sources(self, fragment_path: str, vertex_path: str):
        with open(fragment_path, "r") as frag:
            frag_src = frag.read()

        with open(vertex_path, "r") as vert:
            vert_src = vert.read()

        self._sources = Sources(vert_src, frag_src)
        self._preprocess()

    def _preprocess(self):
        bindings = {}
        for uniform in self._sources.uniforms().values():
            if uniform.type_name.endswith("sampler2D"):
                bindings[uniform.name] = NoBinding(len(bindings))

        self._bindings = bindings

    def compile(self, force: bool = False):
        if force or self._program is None:
            self._program = self._ctx.program(**self._sources._asdict())

        for name, (offset, *_) in self._bindings.items():
            self._program[name] = offset

    def bind(
        self,
        name: str,
        size: tuple[int, int],
        components: int = 4,
        dtype: str = "f1",
        wrapping: tuple[PyGLenum, PyGLenum] = (gl.REPEAT, gl.REPEAT),
    ) -> Binding:
        names = [*self._bindings.keys()]
        if self._bindings.get(name) is None:
            raise ValueError(
                f"There is no uniform sampler2D named {name}. Names found were: {', '.join(names)}."
            )

        (bind_offset, *_) = self._bindings[name]

        self._bindings[name] = (  # 😲 Spicy!
            bound := Binding(
                bind_offset,
                *self.gen_tx_buf(
                    self._ctx,
                    size,
                    components=components,
                    dtype=dtype,
                    wrapping=wrapping,
                ),
            )
        )

        return bound

    def attach_uniform(self, name: str, get_value: Callable[[], Any]):
        def _update(prog: gl.Program):
            nonlocal name
            nonlocal get_value
            prog[name] = get_value()

        self._on_use.append(_update)

    def __enter__(self) -> gl.Program:
        if not self._program:
            self.compile()

        for binding in self._bindings.values():
            binding.use()

        for update in self._on_use:
            update(self._program)

        return self._program

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
