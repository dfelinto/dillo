import logging
import requests
from urllib.parse import urlparse, urljoin
from re import compile

from bs4 import BeautifulSoup
from micawber.exceptions import ProviderException, ProviderNotFoundException
from flask import abort, Blueprint, current_app, redirect, render_template, request, url_for, \
    jsonify
from werkzeug import exceptions as wz_exceptions
from werkzeug.contrib.atom import AtomFeed
from flask_login import current_user, login_required
from pillarsdk import Project, Node, Activity, User
from pillarsdk.exceptions import ResourceNotFound, ForbiddenAccess

from pillar.web import subquery
from pillar.web import system_util
from pillar.web.utils import attach_project_pictures
from pillar.web.utils import get_file
from pillar.web.utils import get_main_project
from pillar.web.nodes.routes import url_for_node
from pillar.web.nodes import attachments


from pillar import current_app

blueprint = Blueprint('feeds', __name__)
log = logging.getLogger(__name__)


def common_feed(community_url: str, feed_url: str):
    """Util function to process the required feeds.
    """
    api = system_util.pillar_api()

    project = Project.find_first({'where': {'url': community_url}}, api=api)
    posts = Node.all({
        'where': {'project': project['_id'], 'node_type': 'dillo_post', 'properties.status': 'published'},
        'sort': '-_created',
    }, api=api)

    if project is None:
        return abort(404)

    return render_template(
        feed_url,
        project=project,
        posts=posts,
    )


@blueprint.route('/feeds/rss/<community_url>')
def rss(community_url):
    """Feed aggregator for a project
    """
    return common_feed(community_url, "dillo/feeds/rss.xml")


@blueprint.route('/feeds/atom/<community_url>')
def atom(community_url):
    """Feed aggregator for a project
    """
    return common_feed(community_url, "dillo/feeds/atom.xml")


"""
@blueprint.route('/c/<community_url>/')
def index(community_url):
    api = system_util.pillar_api()

    project = Project.find_first({'where': {'url': community_url}}, api=api)

    if project is None:
        return abort(404)

    attach_project_pictures(project, api)

    # Fetch all activities for the main project
    activities = Activity.all({
        'where': {
            'project': project['_id'],
        },
        'sort': [('_created', -1)],
        'max_results': 15,
    }, api=api)

    # Fetch more info for each activity.
    for act in activities['_items']:
        act.actor_user = subquery.get_user_info(act.actor_user)
        act.link = url_for_node(node_id=act.object)

    return render_template(
        'dillo/index.html',
        col_right={'activities': activities},
        project=project,
        submit_menu=project_submit_menu(project))
"""