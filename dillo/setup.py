"""Setting up projects for Dillo.

This is intended to be used by the CLI and unittests only, not tested
for live/production situations.
"""

import copy
import logging

from bson import ObjectId
from eve.methods.put import put_internal
from flask import current_app

from pillar.api.utils import node_type_utils

from . import EXTENSION_NAME

log = logging.getLogger(__name__)


def _get_project(project_url):
    """Find a project in the database, or SystemExit()s.

    :param project_url: UUID of the project
    :type: str
    :return: the project
    :rtype: dict
    """

    projects_collection = current_app.data.driver.db['projects']

    # Find the project in the database.
    project = projects_collection.find_one({'url': project_url})

    if not project:
        raise RuntimeError('Project %s does not exist.' % project_url)

    return project


def _update_project(project):
    """Updates a project in the database, or SystemExit()s.

    :param project: the project data, should be the entire project document
    :type: dict
    :return: the project
    :rtype: dict
    """

    from pillar.api.utils import remove_private_keys

    project_id = ObjectId(project['_id'])
    project = remove_private_keys(project)
    result, _, _, status_code = put_internal('projects', project, _id=project_id)

    if status_code != 200:
        raise RuntimeError("Can't update project %s, issues: %s", project_id, result)


def setup_for_dillo(project_url, replace=False):
    """Adds Dillo node types to the project.

    Use --replace to replace pre-existing Dillo node types
    (by default already existing Dillo node types are skipped).

    Returns the updated project.
    """

    from .node_types import NODE_TYPES

    # Copy permissions from the project, then give everyone with PUT
    # access also DELETE access.
    project = _get_project(project_url)

    def permission_callback(node_type, ugw, ident, proj_methods):
        if 'PUT' not in set(proj_methods):
            return None

        # TODO: we allow PATCH on shot node types, but that's not explicit in
        # the permission system. Maybe we want to revisit that at some point.
        # if node_type is shot.node_type_shot:
        #     return ['DELETE', 'PATCH']

        return ['DELETE']

    # Add/replace our node types.
    node_types = node_type_utils.assign_permissions(project, NODE_TYPES, permission_callback)
    node_type_utils.add_to_project(project, node_types, replace_existing=replace)

    # Set default extension properties. Be careful not to overwrite any properties that
    # are already there.
    eprops = project.setdefault('extension_props', {})
    dillo_props = eprops.setdefault(EXTENSION_NAME, {
        'last_used_shortcodes': {},
    })


    # Set up task types
    # task_types = dillo_props.setdefault('task_types', {})
    # task_types.setdefault(shot.node_type_shot['name'], shot.task_types)
    # task_types.setdefault(asset.node_type_asset['name'], asset.task_types)

    _update_project(project)

    log.info('Project %s was updated for Dillo.', project_url)

    return project
