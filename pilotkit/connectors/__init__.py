from . import github, linear, notion, slack

NORMALIZERS = {
    "github": github.normalize,
    "slack": slack.normalize,
    "linear": linear.normalize,
    "notion": notion.normalize,
}
