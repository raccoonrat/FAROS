"""Paper-domain storage facade."""

from app.storage.paper_storage import (
    add_log,
    copy_figure_to_paper,
    create_paper,
    create_paper_zip,
    generate_latex_figure_reference,
    get_paper,
    get_paper_figures,
    get_paper_latex_dir,
    list_paper_files,
    list_papers,
    read_paper_file,
    update_paper,
    write_paper_file,
)
from app.storage.experiment_storage import get_experiment, get_metrics

__all__ = [
    "add_log",
    "copy_figure_to_paper",
    "create_paper",
    "create_paper_zip",
    "generate_latex_figure_reference",
    "get_experiment",
    "get_metrics",
    "get_paper",
    "get_paper_figures",
    "get_paper_latex_dir",
    "list_paper_files",
    "list_papers",
    "read_paper_file",
    "update_paper",
    "write_paper_file",
]
