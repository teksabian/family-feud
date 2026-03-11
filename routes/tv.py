"""
TV display routes for the Live TV Game Board.

Includes public TV display page and host-authenticated control pages.
"""

from flask import Blueprint, flash, redirect, render_template, url_for

from auth import host_required
from database import get_setting

tv_bp = Blueprint('tv', __name__)


@tv_bp.route('/tv/board')
def tv_board():
    """Full-screen TV display page for answer reveals."""
    return render_template('tv_board.html')


@tv_bp.route('/host/reveal-control')
@host_required
def reveal_control():
    """Mobile-friendly reveal control page for the host."""
    if get_setting('tv_board_enabled', 'false') != 'true':
        flash('TV Board is not enabled', 'error')
        return redirect(url_for('host.host_dashboard'))
    return render_template('reveal_control.html')
