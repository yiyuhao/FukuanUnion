#      File: merchant_category_manager.py
#   Project: payunion
#    Author: Yi Yuhao
#    Create: 2018/7/13
#
#   Copyright (c) 2018 麦禾互动. All rights reserved.


from .base import ModelManagerBase
from common.models import MerchantCategory


class MerchantCategoryModelManager(ModelManagerBase):

    def __init__(self, *args, **kwargs):
        super(MerchantCategoryModelManager, self).__init__(*args, **kwargs)
        self.model = MerchantCategory

    def list_categories(self):

        categories = {}
        # categories = {
        #     'id_1': {
        #         'name': name_1,
        #         'children': [
        #             {'id': child_id_1, 'name': child_name_1},
        #             {'id': child_id_2, 'name': child_name_2},
        #         ]
        #     },
        # }

        query = self.model.objects.all()

        for item in query:
            if item.parent_id is None:
                categories.setdefault(item.id, dict(name=''))
                categories[item.id]['name'] = item.name
            else:
                categories.setdefault(item.parent_id, dict(name=''))
                parent = categories[item.parent_id]
                parent.setdefault('children', [])
                parent['children'].append(dict(id=item.id, name=item.name))

        result = []
        for c_id, c_info in categories.items():
            item = dict(id=c_id, name=c_info['name'])
            if 'children' in c_info:
                item['children'] = c_info['children']
            result.append(item)

        return result
