import os
import logging

import pytest

from main import encode, decode

logging.basicConfig(level=logging.DEBUG)
LOGGER = logging.getLogger('test')


def get_path(filename):
    return os.path.join("./tests/data", filename)


@pytest.mark.parametrize("logger", [LOGGER])
@pytest.mark.parametrize(
    "input_file, output_file, message",
    [
        (
                get_path("Discord.wav"),
                get_path("Discord-demo.wav"),
                "Making a living selling used jalapenos",
        ),
    ]
)
def test_sanity_check(logger, input_file, output_file, message):
    if os.path.isfile(output_file):
        os.remove(output_file)

    encode(LOGGER, input_file, output_file, message)
    decoded_message = decode(LOGGER, output_file)

    assert decoded_message == message
    os.remove(output_file)
