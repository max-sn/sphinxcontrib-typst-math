"""
    sphinxcontrib.typst_math
    ~~~~~~~~~~~~~~~~~~~~~~~~

    An extension allowing math in typst syntax to be rendered as image.

    This module adds an extension to Sphinx that allows math (in typst syntax) to be
    rendered by typst and included in the documentation as a figure (pdf or svg).

    :copyright: Copyright 2024 by M.J.W. Snippe <maxsnippe@gmail.com>
    :license: BSD, see LICENSE for details.
"""

import shutil
import subprocess
from hashlib import sha1
from pathlib import Path
from typing import TYPE_CHECKING

from docutils import nodes
from sphinx.util.docutils import SphinxDirective

if TYPE_CHECKING:
    from sphinx.application import Sphinx
    from sphinx.util.typing import ExtensionMetadata


class TypstMathDirective(SphinxDirective):
    """
    Render math in Typst syntax as a figure.
    """

    has_content = True

    def run(self) -> list[nodes.Node]:
        """
        Run typst and to render math.

        Returns:
            A list with a single image node, containing the reference to the generated
            figure.
        """

        # Find the executable for typst
        typst = shutil.which(self.config.typst_math_typst)

        # Create a doc to parse. This is not a very nice way to do this, and to allow
        # more configuration it would be better to use a templating tool like jinja2.
        # For now this works.
        typst_doc = f"#set page(width: auto, height: auto, margin: 3.14pt)\n\n$ {'\n'.join(self.content)} $"

        # Ensure that the temporary directory exists.
        tmpdir = Path(self.env.app.builder.outdir) / "assets" / "typst_math"
        if not tmpdir.exists():
            tmpdir.mkdir(parents=True)

        # Generate a filename for the image file. This is taken from
        # :obj:`sphinx.ext.imgmath`.
        filename = f"{sha1(typst_doc.encode(), usedforsecurity=False).hexdigest()}"
        filepath = tmpdir / filename

        # Use '-' as input to process from pipe input.
        command = [typst, "compile", "-"]

        if self.env.app.builder.format == "html":
            command.append(str(filepath.with_suffix(".svg")))
        elif self.env.app.builder.format == "pdf":
            command.append(str(filepath.with_suffix(".pdf")))
        else:
            command.append(str(filepath.with_suffix(".png")))

        proc = subprocess.Popen(command, cwd=tmpdir, stdin=subprocess.PIPE)

        proc.communicate(typst_doc.encode())

        img_node = nodes.image()
        img_node["uri"] = str(filepath.with_suffix(".*"))
        img_node["classes"].append("typst-math")
        img_node["align"] = "center"
        return [img_node]


def setup(app: "Sphinx") -> "ExtensionMetadata":
    """
    Setup the extension.

    Args:
        app: The running Sphinx application.

    Returns:
        Sphinx extensions metadata.
    """
    app.add_directive("typst-math", TypstMathDirective)

    app.add_config_value("typst_math_typst", "typst", "env")

    return {
        "version": "0.1.0-dev",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }
