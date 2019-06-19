#      File: area_manager.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/7/18
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.

from .base import ModelManagerBase
from common.models import Area
from common.model_manager.utils import AreaNode


class AreaModelManager(ModelManagerBase):

    def __init__(self, *args, **kwargs):
        super(AreaModelManager, self).__init__(*args, **kwargs)
        self.model = Area

    def list_areas(self):

        query = self.model.objects.all()

        areas = {}  # hash table for searching node's parent
        for item in query:
            areas[item.id] = dict(
                name=item.name,
                adcode=item.adcode,
                parent_id=item.parent_id
            )

        root = AreaNode(id_=-1, name='root', adcode='root')

        # 已生成的node
        made_nodes = {}

        def make_node(id_, name, adcode, parent_id=None):
            if parent_id:
                # if already made
                if parent_id in made_nodes:
                    parent_node = made_nodes[parent_id]
                else:
                    parent = areas[parent_id]
                    parent_node = make_node(parent_id, parent['name'], parent['adcode'], parent['parent_id'])
                    made_nodes[parent_id] = parent_node
            else:
                parent_node = root
            node = AreaNode(id_, name, adcode, parent_node)
            made_nodes[id_] = node
            return node

        # build tree (all the nodes will be related to each other)
        for item in query:
            if item.id not in made_nodes:
                make_node(item.id, item.name, item.adcode, item.parent_id)

        root_dict = root.to_dict()
        return root_dict['children']
