# yapf: disable

from log21 import ColorizingArgumentParser

# yapf: enable


def create_admin():
    """Create a new admin user."""
    parser = ColorizingArgumentParser(description="Create a new admin user.")
    parser.add_argument("username", help="The username of the admin user.")
    parser.add_argument("password", help="The password of the admin user.")
    args = parser.parse_args()  # noqa
    raise NotImplementedError("This function is not implemented yet.")
